import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Document import: PDF, Word, text, web pages, and the SSRF protection."""
import asyncio, io
import fakeredis, httpx
from fastapi.testclient import TestClient
import ingest, main

main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(decode_responses=True)

# ---------- sample files built in memory ----------
from reportlab.pdfgen import canvas
buf = io.BytesIO(); pdf = canvas.Canvas(buf)
pdf.drawString(72, 750, "Parking permits cost 150 dollars per semester."); pdf.showPage()
pdf.drawString(72, 750, "Lot 20 is closest to the library."); pdf.save()
PDF = buf.getvalue()
import docx
d = docx.Document(); d.add_heading("Housing", level=1); d.add_paragraph("Fall move-in starts August 20.")
t = d.add_table(rows=1, cols=2); t.rows[0].cells[0].text = "Hall"; t.rows[0].cells[1].text = "Maple"
b2 = io.BytesIO(); d.save(b2); DOCX = b2.getvalue()

pdf_text = ingest.extract_file("guide.pdf", PDF)
assert "## guide.pdf, page 1" in pdf_text and "150 dollars" in pdf_text and "## guide.pdf, page 2" in pdf_text
docx_text = ingest.extract_file("housing.docx", DOCX)
assert "## Housing" in docx_text and "August 20" in docx_text and "Hall | Maple" in docx_text
assert ingest.extract_file("notes.txt", b"Open 9 to 5").startswith("## notes.txt")
for name, data, why in (("x.exe", b"MZ", "type"), ("big.txt", b"a" * (ingest.MAX_FILE_BYTES + 1), "size"), ("bad.pdf", b"%PDF-1.4 broken", "corrupt")):
    try:
        ingest.extract_file(name, data); raise SystemExit(f"FAIL accepted {why}")
    except ingest.IngestError:
        pass
print("files OK: PDF pages, Word headings and tables, text; wrong type, too big and corrupt refused")

# ---------- SSRF protection ----------
async def private_dns(host):  return ["10.0.0.7"]
async def public_dns(host):   return ["93.184.216.34"]
blocked = ["http://localhost/", "http://127.0.0.1/admin", "http://10.0.0.5/", "http://192.168.1.1/", "http://172.18.0.2:80/",
           "http://169.254.169.254/latest/meta-data/", "http://[::1]/", "http://[::ffff:127.0.0.1]/", "http://0.0.0.0/",
           "file:///etc/passwd", "ftp://example.com/x", "http://example.com:6379/", "http://user:pw@example.com/", "gopher://x"]
async def check_all():
    for u in blocked:
        try:
            await ingest.check_public_url(u, public_dns if "example.com" in u else private_dns)
            raise SystemExit(f"FAIL: allowed {u}")
        except ingest.IngestError:
            pass
    try:  # a public-looking name that resolves to a private address (e.g. http://redis/)
        await ingest.check_public_url("http://redis/", private_dns); raise SystemExit("FAIL: allowed redis")
    except ingest.IngestError:
        pass
    assert await ingest.check_public_url("https://www.unt.edu/admissions", public_dns)
asyncio.run(check_all())
print(f"SSRF OK: {len(blocked) + 1} private or unsafe addresses refused, public address allowed")

PAGE = b"""<html><head><title>UNT Parking</title><style>.x{}</style></head><body><nav>Menu Home About</nav>
<h1>Parking at UNT</h1><p>Students need a permit to park on campus.</p><script>alert(1)</script>
<h2>Visitors</h2><ul><li>Visitor parking is in the Union garage.</li></ul><footer>Copyright</footer></body></html>"""
def site(request):
    path = request.url.path
    if path == "/page":    return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=PAGE)
    if path == "/moved":   return httpx.Response(302, headers={"location": "/page"})
    if path == "/evil":    return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})
    if path == "/image":   return httpx.Response(200, headers={"content-type": "image/png"}, content=b"png")
    if path == "/huge":    return httpx.Response(200, headers={"content-type": "text/html"}, content=b"a" * (ingest.MAX_PAGE_BYTES + 10))
    if path == "/doc.pdf": return httpx.Response(200, headers={"content-type": "application/pdf"}, content=PDF)
    return httpx.Response(404)
async def fetch_all():
    client = httpx.AsyncClient(transport=httpx.MockTransport(site), follow_redirects=False)
    title, text = await ingest.fetch_url("https://www.example.edu/page", client, public_dns)
    assert title == "UNT Parking" and "## Parking at UNT" in text and "## Visitors" in text and "Union garage" in text
    assert "alert" not in text and "Menu Home" not in text and "Copyright" not in text, text
    _, moved = await ingest.fetch_url("https://www.example.edu/moved", client, public_dns)
    assert "Union garage" in moved
    _, pdftext = await ingest.fetch_url("https://www.example.edu/doc.pdf", client, public_dns)
    assert "Lot 20" in pdftext
    for path, why in (("/evil", "redirect to a private address"), ("/image", "image"), ("/huge", "too large"), ("/missing", "404")):
        try:
            await ingest.fetch_url("https://www.example.edu" + path, client, public_dns); raise SystemExit(f"FAIL: {why}")
        except ingest.IngestError:
            pass
    await client.aclose()
asyncio.run(fetch_all())
print("web pages OK: headings kept, menus/scripts/footers dropped, redirects re-checked, PDF links, image/huge/404 refused")

# ---------- endpoints ----------
with TestClient(main.app) as c:
    H = {"X-Admin-Token": main.app.state.admin_token}
    r = c.post("/import/file", files={"file": ("guide.pdf", PDF, "application/pdf")}).json()
    assert "150 dollars" in r["text"] and r["truncated"] is False
    r = c.post("/import/file", files={"file": ("housing.docx", DOCX, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}).json()
    assert "## Housing" in r["text"]
    assert c.post("/import/file", files={"file": ("virus.exe", b"MZ", "application/octet-stream")}).status_code == 422
    big = c.post("/import/file", files={"file": ("big.pdf", b"%PDF" + b"a" * 7_000_000, "application/pdf")})
    assert big.status_code == 413, big.status_code
    assert c.post("/import/url", json={"url": "http://127.0.0.1:8000/admin/overview"}).status_code == 422
    assert c.post("/import/url", json={"url": "http://169.254.169.254/latest/meta-data/"}).status_code == 422
    main.settings.IMPORT_LIMIT_PER_HOUR = 2
    codes = [c.post("/import/file", files={"file": ("n.txt", b"hello there", "text/plain")}).status_code for _ in range(3)]
    assert codes == [200, 429, 429] or codes[-1] == 429, codes
    assert c.post("/import/file", files={"file": ("n.txt", b"hello there", "text/plain")}, headers=H).status_code == 200, "admins not limited"
print("endpoints OK: file import, 413 over 6 MB, private URLs refused, rate limit")
print("ALL INGEST TESTS PASSED")
