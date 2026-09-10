from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript"}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src"):
            value = attrs.get(key)
            if value:
                self.links.append(value.strip())


def resolve_local(source: Path, raw: str):
    if not raw or raw.startswith("#") or raw.startswith("//"):
        return None
    parsed = urlparse(raw)
    if parsed.scheme in SKIP_SCHEMES:
        return None
    path = parsed.path
    if not path:
        return None
    if path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = source.parent / path
    target = target.resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return target
    if target.is_dir():
        target = target / "index.html"
    return target


def main():
    html_files = sorted(ROOT.rglob("*.html"))
    failures = []
    checked = 0

    for html_file in html_files:
        parser = LinkParser()
        try:
            parser.feed(html_file.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            failures.append(f"PARSE {html_file.relative_to(ROOT)}: {exc}")
            continue

        for raw in parser.links:
            target = resolve_local(html_file, raw)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                failures.append(
                    f"MISSING {html_file.relative_to(ROOT)} -> {raw} "
                    f"(resolved: {target})"
                )

    print(f"HTML files: {len(html_files)}")
    print(f"Local references checked: {checked}")

    if failures:
        print("\nValidation failures:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Site validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
