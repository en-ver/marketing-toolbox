"""Run with pinned Python -I, against a stopped build's fresh, read-only output copy."""

import json
import pathlib
import stat
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlsplit

root = pathlib.Path(sys.argv[1])
base_bytes = pathlib.Path(sys.argv[2]).read_bytes()
assert len(base_bytes) < 65536
baseline = json.loads(base_bytes)
assert len(baseline) == 8 and sum(len(x["headings"]) for x in baseline) == 33
expected = {x["route"].lstrip("/") + "index.html": x for x in baseline}
assert not root.is_symlink() and root.is_dir()
files = {}
total = 0
entries = 0
for p in root.rglob("*"):
    entries += 1
    assert entries <= 8192
    s = p.lstat()
    rel = p.relative_to(root).as_posix()
    assert len(rel) <= 512 and not any(
        x.startswith(".") for x in p.relative_to(root).parts if x != ".nojekyll"
    )
    assert stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)
    if stat.S_ISDIR(s.st_mode):
        continue
    assert s.st_nlink == 1
    assert s.st_size <= 8 * 1024 * 1024
    total += s.st_size
    assert total <= 256 * 1024 * 1024
    assert len(files) < 4096
    assert (
        p.suffix
        in {
            ".html",
            ".js",
            ".css",
            ".json",
            ".woff",
            ".woff2",
            ".ttf",
            ".svg",
            ".png",
            ".ico",
            ".txt",
        }
        or rel == ".nojekyll"
    )
    files[rel] = p
assert {n for n in files if n.endswith(".html")} == set(expected) | {"404.html"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.headings = set()
        self.links = []
        self.open_html = self.close_html = self.open_body = self.close_body = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        assert len(a) == len(attrs)
        if a.get("id"):
            assert a["id"] not in self.ids
            self.ids.add(a["id"])
            if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                self.headings.add(a["id"])
        if tag == "html":
            self.open_html += 1
        if tag == "body":
            self.open_body += 1
        if "href" in a:
            self.links.append(a["href"])
        if "src" in a:
            self.links.append(a["src"])
        assert tag not in {
            "base",
            "iframe",
            "object",
            "embed",
            "audio",
            "video",
            "source",
            "track",
        }

    def handle_endtag(self, tag):
        if tag == "html":
            self.close_html += 1
        if tag == "body":
            self.close_body += 1


pages = {}
for name, p in files.items():
    if not name.endswith(".html"):
        continue
    b = p.read_bytes()
    text = b.decode("utf-8", errors="strict")
    assert "\x00" not in text
    parser = Page()  # Never reuse across files or stream chunks.
    parser.feed(text)  # Exactly one feed per fresh parser.
    assert not parser.rawdata and parser.cdata_elem is None
    parser.close()
    assert not parser.rawdata
    assert (
        parser.open_html
        == parser.close_html
        == parser.open_body
        == parser.close_body
        == 1
    )
    pages[name] = parser
for name, old in expected.items():
    assert {h["id"] for h in old["headings"]} <= pages[name].headings
for name, page in pages.items():
    route = "/" + name[:-10] if name.endswith("index.html") else "/" + name
    for href in page.links:
        assert not any(ord(c) < 32 for c in href)
        u = urlsplit(urljoin("https://marketing-toolbox.org" + route, href))
        if u.scheme in {"mailto", "tel"}:
            continue
        assert u.scheme in {"http", "https"}
        if u.hostname != "marketing-toolbox.org":
            continue
        assert u.username is None and u.password is None and u.port in (None, 443)
        path = unquote(u.path)
        assert "\x00" not in path and "\\" not in path
        dest = path.lstrip("/")
        if dest.endswith("/") or not dest:
            dest += "index.html"
        assert dest in files, (name, href)
        if u.fragment and dest in pages:
            assert unquote(u.fragment) in pages[dest].ids, (name, href)
for route, frag in [
    ("/auth/", "credential-precedence"),
    ("/tools/", "output-and-requests"),
    ("/tools/ga4-admin/", "destructive-admin-mutations"),
]:
    assert frag in pages[route.lstrip("/") + "index.html"].headings
print(
    json.dumps(
        {
            "routes": [x["route"] for x in baseline],
            "heading_count": 33,
            "files": len(files),
            "bytes": total,
        }
    )
)
