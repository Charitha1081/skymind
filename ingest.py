"""Turn files and web pages into text a bot can learn from.

  extract_file(name, data)  .pdf, .docx, .txt, .md, .csv  -> text with "## " section titles
  fetch_url(url)            a public web page (or PDF)     -> text with "## " section titles

Safety:
  - size limits (MAX_FILE_BYTES, MAX_PAGES, MAX_PAGE_BYTES) so one upload can't exhaust memory
  - fetch_url only visits public internet addresses. It refuses localhost, private networks
    (10.x, 192.168.x, the Docker network, ...), cloud metadata (169.254.169.254) and every other
    non-public address, checks again after every redirect, and only accepts web pages, text and PDFs.
    This blocks SSRF: tricking the server into reading its own private services.
"""
import asyncio
import io
import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx

MAX_FILE_BYTES = 5_000_000
MAX_PAGES = 300
MAX_PAGE_BYTES = 3_000_000
MAX_REDIRECTS = 3
FETCH_TIMEOUT_S = 10
USER_AGENT = "SkyMindBot/1.0 (document import)"


class IngestError(ValueError):
    """A problem the user can fix (wrong type, too big, blocked address)."""


def _clean(text: str) -> str:
    text = text.replace("\r", "\n").replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------- files

def _pdf(name: str, data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise IngestError("This PDF is password-protected. Remove the password and try again.")
        pages = []
        for i, page in enumerate(reader.pages[:MAX_PAGES]):
            text = _clean(page.extract_text() or "")
            if text:
                pages.append(f"## {name}, page {i + 1}\n{text}")
    except IngestError:
        raise
    except Exception:
        raise IngestError("Could not read this PDF.") from None
    if not pages:
        raise IngestError("No text found in this PDF (it may be scanned images).")
    return "\n\n".join(pages)


def _docx(name: str, data: bytes) -> str:
    import docx  # python-docx

    try:
        doc = docx.Document(io.BytesIO(data))
    except Exception:
        raise IngestError("Could not read this Word file (only .docx is supported).") from None
    lines = [f"## {name}"]
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name or "").lower() if para.style is not None else ""
        lines.append(f"\n## {text}" if style.startswith(("heading", "title")) else text)
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(" | ".join(cells))
    if len(lines) > 1 and lines[1].startswith("\n## "):
        lines = lines[1:]  # the document starts with its own heading: no need for the file name
    text = _clean("\n".join(lines))
    if text in ("", f"## {name}"):
        raise IngestError("No text found in this Word file.")
    return text


def extract_file(name: str, data: bytes) -> str:
    name = re.sub(r"[^\w .()-]", "", name or "document")[:80] or "document"
    if len(data) > MAX_FILE_BYTES:
        raise IngestError(f"File is too large (limit {MAX_FILE_BYTES // 1_000_000} MB).")
    lower = name.lower()
    if lower.endswith(".pdf") or data[:5] == b"%PDF-":
        return _pdf(name, data)
    if lower.endswith(".docx"):
        return _docx(name, data)
    if lower.endswith((".txt", ".md", ".markdown", ".csv")):
        text = _clean(data.decode("utf-8", errors="replace"))
        return text if text.lstrip().startswith("#") else f"## {name}\n{text}"
    raise IngestError("Use a PDF, Word (.docx), text, Markdown or CSV file.")


# ---------------------------------------------------------------- web pages

class _PageText(HTMLParser):
    """Keeps headings (as ## titles), paragraphs, list items and table cells; drops menus and scripts."""

    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe", "button", "select"}
    BLOCK = {"p", "li", "td", "th", "div", "section", "article", "br", "tr", "dd", "dt", "blockquote"}
    HEAD = {"h1", "h2", "h3", "h4"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.title, self.in_title, self.in_head = [], 0, "", False, False
        self.links: list[tuple[str, str]] = []   # (href, link text), including menu links
        self._href, self._atext = None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._atext = []
        if tag in self.SKIP:
            self.skip += 1
        elif tag == "title":
            self.in_title = True
        elif tag in self.HEAD:
            self.out.append("\n\n## ")
            self.in_head = True
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            if len(self.links) < 500:
                self.links.append((self._href, " ".join("".join(self._atext).split())[:120]))
            self._href = None
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag == "title":
            self.in_title = False
        elif tag in self.HEAD:
            self.out.append("\n")
            self.in_head = False

    def handle_data(self, data):
        if self._href is not None:
            self._atext.append(data)
        if self.in_title:
            self.title += data
        elif not self.skip:
            self.out.append(data.replace("\n", " ") if self.in_head else data)


def html_to_text(html: str, url: str = "") -> tuple[str, str]:
    title, text, _ = html_page(html, url)
    return title, text


def html_page(html: str, url: str = "") -> tuple[str, str, list[tuple[str, str]]]:
    """(title, text, links). Links are absolute http(s) addresses with their link text."""
    parser = _PageText()
    parser.feed(html)
    links = []
    for href, label in parser.links:
        absolute = urljoin(url, href.strip()).split("#")[0]
        if urlsplit(absolute).scheme in ("http", "https"):
            links.append((absolute, label))
    title = " ".join(parser.title.split())[:120] or urlsplit(url).netloc or "Web page"
    body = "".join(parser.out)
    lines = [ln.strip() for ln in body.split("\n")]
    text = _clean("\n".join(ln for ln in lines if ln and ln != "##"))
    if len(text) < 40:
        raise IngestError("Found almost no readable text on this page (it may need JavaScript).")
    if not text.startswith("## "):
        text = f"## {title}\n{text}"
    return title, text, links


def _is_public(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return addr.is_global and not addr.is_multicast


async def check_public_url(url: str, resolve=None) -> str:
    """Raise IngestError unless url is http(s) on port 80/443 and every address it resolves to is public."""
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise IngestError("Use a full web address starting with https://")
    if parts.username or parts.password:
        raise IngestError("Web addresses with a username or password are not allowed.")
    if parts.port not in (None, 80, 443):
        raise IngestError("Only standard web ports (80 and 443) are allowed.")
    host = parts.hostname
    try:
        ips = [host] if _looks_like_ip(host) else await (resolve or _resolve)(host)
    except OSError:
        raise IngestError(f"Could not find the website {host}.") from None
    if not ips or not all(_is_public(ip) for ip in ips):
        raise IngestError("That address is not a public website, so SkyMind won't fetch it.")
    return parts.geturl()


def _looks_like_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


async def _resolve(host: str) -> list[str]:
    infos = await asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


async def fetch_url(url: str, client: httpx.AsyncClient | None = None, resolve=None) -> tuple[str, str]:
    """Fetch a public page (following up to 3 redirects, each re-checked) and return (title, text)."""
    page = await fetch_page(url, client, resolve)
    return page["title"], page["text"]


async def fetch_page(url: str, client: httpx.AsyncClient | None = None, resolve=None) -> dict:
    """Like fetch_url, but returns {"url" (after redirects), "title", "text", "links"}."""
    own = client is None
    client = client or httpx.AsyncClient(timeout=FETCH_TIMEOUT_S, follow_redirects=False)
    try:
        for _ in range(MAX_REDIRECTS + 1):
            url = await check_public_url(url, resolve)
            try:
                async with client.stream("GET", url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,application/pdf"},
                                         timeout=FETCH_TIMEOUT_S) as resp:
                    if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("location"):
                        url = urljoin(url, resp.headers["location"])
                        continue
                    if resp.status_code != 200:
                        raise IngestError(f"The website answered with error {resp.status_code}.")
                    ctype = resp.headers.get("content-type", "").split(";")[0].strip().lower()
                    if ctype not in ("text/html", "application/xhtml+xml", "text/plain", "application/pdf"):
                        raise IngestError("That page isn't a web page, text or PDF.")
                    body = bytearray()
                    async for chunk in resp.aiter_bytes():
                        body += chunk
                        if len(body) > MAX_PAGE_BYTES:
                            raise IngestError("That page is too large to import.")
            except httpx.HTTPError:
                raise IngestError("Could not download that page (it may be down or too slow).") from None
            if ctype == "application/pdf":
                name = urlsplit(url).path.rsplit("/", 1)[-1] or "document.pdf"
                return {"url": url, "title": name, "text": _pdf(name, bytes(body)), "links": []}
            text = body.decode(resp.encoding or "utf-8", errors="replace")
            if ctype == "text/plain":
                return {"url": url, "title": url, "text": f"## {urlsplit(url).netloc}\n{_clean(text)}", "links": []}
            title, page_text, links = html_page(text, url)
            return {"url": url, "title": title, "text": page_text, "links": links}
        raise IngestError("Too many redirects.")
    finally:
        if own:
            await client.aclose()
