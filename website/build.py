# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Build the static Codebase Map website into website/dist/.

Usage: python3 website/build.py [--site-url https://cbm.example.com]

Needs PyYAML (imported by codebase_map.config). The live demo, the graph
numbers and the terminal sample are produced from this checkout's own
codebase_map/ sources on every build, so the page never drifts from the code.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC = HERE / "src"
DIST = HERE / "dist"
REPO_URL = "https://github.com/hypercommerce-vn/codebase-map"
IMPACT_EXAMPLE = "GraphBuilder"
STATIC_FILES = ("styles.css", "site.js", "favicon.svg")

# Build from this checkout's sources, not whichever codebase-map is installed.
sys.path.insert(0, str(REPO))

from content import STRINGS  # noqa: E402

from codebase_map import __version__  # noqa: E402
from codebase_map.config import Config, SourceConfig  # noqa: E402
from codebase_map.exporters.html_exporter import export_html  # noqa: E402
from codebase_map.exporters.json_exporter import export_json  # noqa: E402
from codebase_map.graph.builder import GraphBuilder  # noqa: E402
from codebase_map.graph.models import Graph  # noqa: E402

PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")

# lang -> (output path, relative base, link to the other language, its label)
PAGES = {
    "vi": ("index.html", "", "en/", "en", "English"),
    "en": ("en/index.html", "../", "../", "vi", "Tiếng Việt"),
}


def fill(text: str, values: dict[str, str]) -> str:
    def sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"no value for {{{{{key}}}}}")
        return values[key]

    return PLACEHOLDER.sub(sub, text)


def build_graph() -> Graph:
    config = Config(
        project="codebase-map",
        sources=[
            SourceConfig(
                path="codebase_map",
                language="python",
                base_module="codebase_map",
                exclude=["__pycache__"],
            )
        ],
        project_root=REPO,
    )
    return GraphBuilder(config, use_cache=False).build()


def impact_sample(graph: Graph) -> str:
    """Run the real `impact` command against the freshly built graph."""
    with tempfile.TemporaryDirectory() as tmp:
        graph_file = Path(tmp) / "graph.json"
        export_json(graph, graph_file)
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (str(REPO), env.get("PYTHONPATH", "")) if p
        )
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "codebase_map", "impact", IMPACT_EXAMPLE]
                + ["-f", str(graph_file)],
                cwd=REPO,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise SystemExit(
                f"`codebase-map impact {IMPACT_EXAMPLE}` failed "
                f"(exit {exc.returncode}):\n{exc.stderr or exc.stdout}"
            ) from exc
    return proc.stdout.rstrip()


def terminal_html(graph: Graph, impact: str) -> str:
    def prompt(cmd: str) -> str:
        return f'<span class="t-prompt">$</span> {html.escape(cmd)}'

    done = f"{graph.project} — {len(graph.nodes)} nodes, {len(graph.edges)} edges"
    lines = [
        prompt("codebase-map generate -c codebase-map.yaml"),
        f'<span class="t-ok">[DONE]</span> {html.escape(done)}',
        "",
        prompt(f'codebase-map impact "{IMPACT_EXAMPLE}" -f graph.json'),
    ]
    for line in impact.splitlines():
        text = html.escape(line)
        if line.startswith("==="):
            lines.append(f'<span class="t-head">{text}</span>')
        elif line.lstrip().startswith("!!"):
            lines.append(f'<span class="t-hit">{text}</span>')
        else:
            lines.append(text)
    return "\n".join(lines)


def number(n: int, lang: str) -> str:
    return f"{n:,}".replace(",", "." if lang == "vi" else ",")


def seo_links(site_url: str, path: str) -> str:
    if not site_url:
        return ""
    url = html.escape(site_url, quote=True)
    return "\n".join(
        [
            f'<link rel="canonical" href="{url}/{path}">',
            f'<link rel="alternate" hreflang="vi" href="{url}/">',
            f'<link rel="alternate" hreflang="en" href="{url}/en/">',
            f'<link rel="alternate" hreflang="x-default" href="{url}/">',
            f'<meta property="og:url" content="{url}/{path}">',
        ]
    )


def asset_hash() -> str:
    digest = hashlib.sha256()
    for name in STATIC_FILES:
        digest.update((SRC / name).read_bytes())
    return digest.hexdigest()[:10]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(site_url: str) -> None:
    keys = {lang: set(strings) for lang, strings in STRINGS.items()}
    if keys["vi"] != keys["en"]:
        raise SystemExit(f"content.py keys differ: {keys['vi'] ^ keys['en']}")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    graph = build_graph()
    export_html(graph, DIST / "demo" / "index.html")
    # The HTML map only draws edges whose both ends are nodes in the graph;
    # the rest point at builtins, libraries or modules.
    drawn = sum(
        1 for e in graph.edges if e.source in graph.nodes and e.target in graph.nodes
    )
    version_hash = asset_hash()
    shared = {
        "version": __version__,
        "repo": REPO_URL,
        "asset_hash": version_hash,
        "terminal": terminal_html(graph, impact_sample(graph)),
    }

    template = (SRC / "index.html").read_text(encoding="utf-8")
    for lang, (out, base, alt_href, alt_lang, alt_label) in PAGES.items():
        counts = {
            "n_nodes": len(graph.nodes),
            "n_links": drawn,
            "n_edges": len(graph.edges),
        }
        computed = {
            **shared,
            **{k: number(v, lang) for k, v in counts.items()},
            "base": base,
            "home": "./",
            "alt_href": alt_href,
            "alt_lang": alt_lang,
            "alt_label": alt_label,
            "seo_links": seo_links(site_url, out.removesuffix("index.html")),
        }
        clash = computed.keys() & STRINGS[lang].keys()
        if clash:
            raise SystemExit(f"content.py keys shadow computed values: {clash}")
        strings = {k: fill(v, computed) for k, v in STRINGS[lang].items()}
        write(DIST / out, fill(template, {**computed, **strings}))

    for name in STATIC_FILES:
        shutil.copy2(SRC / name, DIST / name)
    not_found = (SRC / "404.html").read_text(encoding="utf-8")
    write(DIST / "404.html", fill(not_found, {"asset_hash": version_hash}))

    robots = "User-agent: *\nAllow: /\n"
    if site_url:
        robots += f"Sitemap: {site_url}/sitemap.xml\n"
        urls = "".join(f"<url><loc>{site_url}/{p}</loc></url>" for p in ("", "en/"))
        write(
            DIST / "sitemap.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{urls}</urlset>\n",
        )
    write(DIST / "robots.txt", robots)

    print(
        f"[OK] Site built: {DIST} (v{__version__}, demo graph "
        f"{len(graph.nodes)} nodes / {len(graph.edges)} edges)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--site-url",
        default=os.environ.get("SITE_URL", ""),
        help="Public URL, e.g. https://cbm.example.com (adds canonical + sitemap)",
    )
    site_url = parser.parse_args().site_url.rstrip("/")
    if site_url and not re.fullmatch(r"https?://[A-Za-z0-9.-]+(:\d+)?", site_url):
        parser.error("--site-url must look like https://host[:port] with no path")
    build(site_url)


if __name__ == "__main__":
    main()
