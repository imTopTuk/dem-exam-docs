"""Check local links and anchors in the generated MkDocs site."""

from __future__ import annotations

import argparse
import posixpath
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse


IGNORED_SCHEMES = {"data", "javascript", "mailto", "tel"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[int, str]] = []
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.anchors.add(values["id"] or "")
        if tag == "a" and values.get("name"):
            self.anchors.add(values["name"] or "")
        if values.get("href"):
            self.links.append((self.getpos()[0], values["href"] or ""))


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def public_path(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    if relative == "index.html":
        return ""
    if relative.endswith("/index.html"):
        return relative.removesuffix("index.html")
    return relative


def target_file(root: Path, url_path: str) -> Path | None:
    relative = unquote(url_path).lstrip("/")
    candidate = root / relative
    if candidate.is_dir():
        candidate = candidate / "index.html"
    elif not candidate.exists() and not candidate.suffix:
        candidate = candidate / "index.html"
    return candidate if candidate.is_file() else None


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("site", nargs="?", default="site", type=Path)
    cli.add_argument(
        "--site-url",
        default="https://imtoptuk.github.io/dem-exam-docs/",
        help="Published site URL, including the repository path.",
    )
    args = cli.parse_args()

    root = args.site.resolve()
    if not root.is_dir():
        print(f"Site directory does not exist: {root}", file=sys.stderr)
        return 2

    site_url = args.site_url.rstrip("/") + "/"
    site = urlparse(site_url)
    base_path = site.path.rstrip("/") + "/"
    pages = sorted(root.rglob("*.html"))
    parsed = {page.resolve(): parse_page(page) for page in pages}
    errors: list[str] = []
    checked = 0

    for source in pages:
        source_url = urljoin(site_url, public_path(source, root))
        for line, href in parsed[source.resolve()].links:
            value = href.strip()
            if not value or value.startswith("//"):
                continue

            raw = urlparse(value)
            if raw.scheme in IGNORED_SCHEMES:
                continue
            if raw.scheme and raw.scheme not in {"http", "https"}:
                errors.append(f"{source.relative_to(root)}:{line}: unsupported URL: {href}")
                continue

            resolved = urlparse(urljoin(source_url, value))
            if resolved.scheme not in {"http", "https"} or resolved.netloc != site.netloc:
                continue
            if not (resolved.path == base_path.rstrip("/") or resolved.path.startswith(base_path)):
                errors.append(f"{source.relative_to(root)}:{line}: link leaves site base path: {href}")
                continue

            local_path = resolved.path[len(base_path) :] if resolved.path.startswith(base_path) else ""
            destination = target_file(root, local_path)
            checked += 1
            if destination is None:
                errors.append(f"{source.relative_to(root)}:{line}: missing target: {href}")
                continue

            fragment = unquote(resolved.fragment)
            if fragment and fragment not in parsed.get(destination.resolve(), parse_page(destination)).anchors:
                errors.append(
                    f"{source.relative_to(root)}:{line}: missing anchor #{fragment}: {href}"
                )

    if errors:
        print(f"Link check failed with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Checked {checked} internal links across {len(pages)} HTML pages: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
