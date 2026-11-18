"""Ready-made coding standards for code-reviewer bots.

A company can start from a well-known standard in one click and add its own rules on top. Each
'##' section becomes a rule the reviewer cites by name, e.g. [OWASP A05: Injection].

Written in SkyMind's own words as short, checkable review rules. They summarise the public standards;
they are not the official text. Sources:
  OWASP Top 10:2025            https://owasp.org/Top10/
  PEP 8 (Python style guide)   https://peps.python.org/pep-0008/
"""

OWASP_TOP10 = """
## About the OWASP Top 10 rules
These rules follow the OWASP Top 10:2025, the most widely used list of the most critical web application security risks (owasp.org/Top10). Each rule below names its OWASP category.

## OWASP A01: Broken Access Control
Check on the server that the signed-in user may access or change this specific record (for example, that the order belongs to them), not just that they are signed in. Deny by default. Never trust IDs, roles or prices sent by the browser. Don't rely on hiding buttons or links for security.

## OWASP A02: Security Misconfiguration
No debug mode, default passwords, sample accounts or detailed error pages in production. Turn on security headers. Give services and cloud storage the least access they need, and keep storage buckets private unless they must be public.

## OWASP A03: Software Supply Chain Failures
Pin dependency versions and install them from trusted sources. Remove unused packages. Don't copy code or download scripts from unknown places at build or run time. Keep dependencies updated when security fixes are released.

## OWASP A04: Cryptographic Failures
Never write keys, passwords or tokens in code; read them from environment variables or a secrets manager, and rotate any secret that was committed. Hash passwords with a slow password hash (bcrypt, scrypt or Argon2), never MD5 or SHA-1 alone, and never store them in plain text. Use HTTPS for all traffic. Use the secrets module, not random, for tokens.

## OWASP A05: Injection
Never build SQL, shell commands, LDAP queries or HTML by joining strings with user input. Use parameterised queries, pass command arguments as a list without shell=True, and escape output in templates. Never call eval() or exec() on input. Validate input against what is allowed (type, length, format).

## OWASP A06: Insecure Design
Design limits into features: rate-limit logins, password resets, coupon codes and anything that costs money. Think about how a feature could be abused before building it, and keep security checks in one shared place instead of repeating them.

## OWASP A07: Authentication Failures
Use a proven login library or provider rather than custom code. Limit failed login attempts, support multi-factor sign-in, and never reveal whether the username or the password was wrong. Session tokens must be random, expire, and be cleared on sign-out.

## OWASP A08: Software or Data Integrity Failures
Don't load objects from untrusted data with pickle or similar unsafe deserialisers; use JSON and validate it. Verify signatures on updates, webhooks and tokens before trusting them.

## OWASP A09: Security Logging and Alerting Failures
Log security events (sign-ins, failed sign-ins, permission denied, admin actions) with enough detail to investigate, but never log passwords, tokens, keys or full card numbers. Errors must be logged, not silently ignored.

## OWASP A10: Mishandling of Exceptional Conditions
Handle errors deliberately: catch specific exceptions, never use a bare except or swallow errors. When something fails, fail safely (deny access, roll back the change) instead of continuing in a half-done state. Set timeouts on network calls. Don't show stack traces or internal details to users.
"""

PEP8 = """
## About the PEP 8 rules
These rules follow PEP 8, the official style guide for Python code (peps.python.org/pep-0008). Consistency within a project matters most.

## PEP 8: Layout
Indent with 4 spaces, never tabs. Keep lines to at most 79 characters (72 for comments and docstrings); a team may agree on up to 99. Put two blank lines around top-level functions and classes, and one blank line between methods.

## PEP 8: Imports
Put imports at the top of the file, one module per line. Group them: standard library, then third-party packages, then your own modules, with a blank line between groups. Avoid wildcard imports (from module import *).

## PEP 8: Naming
Functions, variables and modules use lowercase_with_underscores (snake_case). Classes use CapWords. Constants use UPPER_CASE. Don't use l, O or I as single-letter names. Names should say what something is, not how it is stored.

## PEP 8: Whitespace and expressions
No spaces just inside brackets or before a comma. One space around assignment and comparison operators. Don't line up assignments with extra spaces.

## PEP 8: Comparisons and exceptions
Compare with None using "is None" or "is not None", never == or !=. Use isinstance() instead of comparing types. Use "if items:" to check for an empty list, not len(items) == 0. Catch specific exceptions; a bare "except:" also catches Ctrl+C and system exits.

## PEP 8: Comments and docstrings
Comments explain why, not what, and are kept up to date. Write docstrings for all public modules, functions, classes and methods.
"""

CLEAN_CODE = """
## About the clean code rules
General good practice for readable, maintainable code in any language.

## Clean code: Functions
A function does one thing, and its name says what. Keep functions short (roughly under 40 lines) with few parameters (3 or fewer is best); group related parameters into an object.

## Clean code: Names
Use clear, searchable names (order_total, not ot or x). Avoid abbreviations and magic numbers; give important numbers a named constant.

## Clean code: Duplication
Don't repeat the same logic in several places (DRY); move it into one function. Delete dead code and commented-out code instead of keeping it.

## Clean code: Errors
Validate inputs at the edges of the system. Raise or return clear errors; never hide failures. Clean up resources with context managers (with open(...)).

## Clean code: Tests
New behaviour and bug fixes come with automated tests, including edge cases (empty, zero, invalid input). Tests are readable and independent of each other.

## Clean code: Changes
Keep pull requests small and focused on one change. Leave no TODOs, debug prints or leftover logging of private data in merged code.
"""

STANDARDS = [
    {"key": "owasp", "label": "OWASP Top 10 (security)",
     "description": "The 10 most critical web security risks (2025): injection, access control, secrets...",
     "text": OWASP_TOP10.strip()},
    {"key": "pep8", "label": "PEP 8 (Python style)",
     "description": "Python's official style guide: layout, imports, naming, comparisons.",
     "text": PEP8.strip()},
    {"key": "clean", "label": "Clean code basics",
     "description": "Readable, maintainable code in any language: functions, names, duplication, tests.",
     "text": CLEAN_CODE.strip()},
]
