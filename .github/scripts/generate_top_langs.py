#!/usr/bin/env python3
"""Generate a compact Most Used Languages card from GitHub repo language stats."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

USER = "Ferxeegs"
TOP_N = 6
OUTPUT = Path("assets/github-top-langs.svg")
API = "https://api.github.com"

# GitHub Linguist colors
LANG_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178C6",
    "Vue": "#41B883",
    "Go": "#00ADD8",
    "C": "#555555",
    "CSS": "#663399",
    "JavaScript": "#F1E05A",
    "SCSS": "#C6538C",
    "Kotlin": "#A97BFF",
    "Astro": "#FF5A03",
    "Blade": "#F7523F",
    "PHP": "#4F5D95",
    "HTML": "#E34C26",
    "C++": "#F34B7D",
    "Shell": "#89E051",
    "Dockerfile": "#384D54",
}


def gh_json(url: str):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "User-Agent": "ferxcode-readme",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def collect_languages() -> dict[str, int]:
    totals: dict[str, int] = {}
    repos = gh_json(f"{API}/users/{USER}/repos?per_page=100&type=owner")
    for repo in repos:
        if repo.get("fork"):
            continue
        languages = gh_json(repo["languages_url"])
        for name, size in languages.items():
            totals[name] = totals.get(name, 0) + int(size)
    return totals


def generate_svg(languages: list[tuple[str, int]]) -> str:
    total = sum(size for _, size in languages) or 1
    items = []
    for name, size in languages:
        percent = size / total * 100
        items.append(
            {
                "name": name,
                "percent": percent,
                "color": LANG_COLORS.get(name, "#94A3B8"),
            }
        )

    bar_x = 25
    bar_y = 80
    bar_w = 445
    bar_h = 8
    segments = []
    offset = 0.0
    for item in items:
        width = bar_w * (item["percent"] / 100)
        segments.append(
            f'  <rect height="{bar_h}" x="{bar_x + offset:.2f}" y="{bar_y}" '
            f'width="{width:.2f}" fill="{item["color"]}" mask="url(#lang-bar-mask)"/>'
        )
        offset += width

    rows = []
    col_w = 222
    row_h = 28
    start_y = 108
    for index, item in enumerate(items):
        col = index % 2
        row = index // 2
        x = 25 + col * col_w
        y = start_y + row * row_h
        label = f"{item['name']} {item['percent']:.2f}%"
        rows.append(
            "\n".join(
                [
                    f'  <g transform="translate({x}, {y})">',
                    f'    <circle cx="5" cy="6" r="5" fill="{item["color"]}"/>',
                    f'    <text x="16" y="10" class="lang-name">{label}</text>',
                    "  </g>",
                ]
            )
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-labelledby="title desc">
  <title id="title">Most Used Languages</title>
  <desc id="desc">Compact GitHub top languages card for {USER}</desc>
  <style>
    .kicker {{ font: 600 10px 'Segoe UI', Ubuntu, sans-serif; fill: #67E8F9; letter-spacing: 1.6px; }}
    .header {{ font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: #E6F7FF; }}
    .lang-name {{ font: 400 12px 'Segoe UI', Ubuntu, sans-serif; fill: #94A3B8; }}
  </style>
  <rect x="0.5" y="0.5" width="494" height="194" rx="16" fill="#07111F" fill-opacity="0.55" stroke="#67E8F9" stroke-opacity="0.16"/>
  <text x="25" y="28" class="kicker">GITHUB</text>
  <text x="25" y="52" class="header">Most Used Languages</text>
  <rect x="25" y="62" width="36" height="3" rx="1.5" fill="#22D3EE"/>
  <defs>
    <mask id="lang-bar-mask">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5" fill="white"/>
    </mask>
  </defs>
{chr(10).join(segments)}
{chr(10).join(rows)}
</svg>
"""


def main() -> None:
    totals = collect_languages()
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:TOP_N]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generate_svg(ranked), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(ranked)} languages")


if __name__ == "__main__":
    main()
