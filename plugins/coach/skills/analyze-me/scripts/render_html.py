#!/usr/bin/env python3
"""Render an analyze-me Markdown report into a standalone, readable HTML page.

Usage: render_html.py <report.md> [--out report.html]

Only the Markdown the report template uses is supported: headings (#, ##, ###),
bullet and numbered lists, pipe tables, paragraphs, **bold** and `code`.
Each ## becomes a section, each ### a card, and 確度 values become badges.
No dependencies, no network: the page has inline CSS only.
"""

import argparse
import html
import os
import re

BADGE = {"高": "high", "中〜高": "midhigh", "中": "mid", "低": "low"}


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


def badge(text):
    t = text.strip()
    for k, cls in BADGE.items():
        if t == k or t.startswith(k + "（") or t.startswith(k + " "):
            return f'<span class="badge {cls}">{inline(t)}</span>'
    return None


def render(md):
    lines = md.splitlines()
    out, title, meta = [], "自己分析レポート", ""
    in_section = in_card = False
    list_tag = None
    para = []
    i = 0

    def flush_para():
        nonlocal para
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para = []

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    def close_card():
        nonlocal in_card
        flush_para()
        close_list()
        if in_card:
            out.append("</div>")
            in_card = False

    def close_section():
        nonlocal in_section
        close_card()
        if in_section:
            out.append("</section>")
            in_section = False

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("対象:") and not in_section:
            meta = line
        elif line.startswith("## "):
            close_section()
            name = line[3:].strip()
            cls = {"ひとことで": "hero", "次の一歩": "next"}.get(name, "")
            out.append(f'<section class="{cls}"><h2>{inline(name)}</h2>')
            in_section = True
        elif line.startswith("### "):
            close_card()
            out.append(f'<div class="card"><h3>{inline(line[4:].strip())}</h3>')
            in_card = True
        elif line.startswith("|"):
            flush_para()
            close_list()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            i -= 1
            if rows:
                head, body = rows[0], rows[1:]
                out.append(
                    '<div class="table-wrap"><table><thead><tr>'
                    + "".join(f"<th>{inline(c)}</th>" for c in head)
                    + "</tr></thead><tbody>"
                )
                for r in body:
                    out.append(
                        "<tr>"
                        + "".join(f"<td>{badge(c) or inline(c)}</td>" for c in r)
                        + "</tr>"
                    )
                out.append("</tbody></table></div>")
        elif re.match(r"^\s*(-|\d+\.)\s+", line):
            flush_para()
            tag = "ol" if re.match(r"^\s*\d+\.", line) else "ul"
            if list_tag != tag:
                close_list()
                out.append(f"<{tag}>")
                list_tag = tag
            item = re.sub(r"^\s*(-|\d+\.)\s+", "", line)
            m = re.match(
                r"^(確度|シグナル|傾向|根拠|何が欠けていそうか|効いている面 / 裏目に出る面|解決すること|やること|形式|既存との関係)[:：]\s*(.*)$",
                item,
            )
            if m:
                val = badge(m.group(2)) if m.group(1) == "確度" else None
                item_html = f'<span class="label">{m.group(1)}</span><span class="value">{val or inline(m.group(2))}</span>'
                out.append(f'<li class="kv">{item_html}</li>')
            else:
                out.append(f"<li>{inline(item)}</li>")
        elif not line.strip():
            flush_para()
            close_list()
        else:
            close_list()
            para.append(line.strip())
        i += 1
    close_section()

    body = "\n".join(out)
    return TEMPLATE.format(title=html.escape(title), meta=inline(meta), body=body)


TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{
  --background: #ffffff; --foreground: #09090b;
  --card: #ffffff; --muted: #f4f4f5; --muted-foreground: #71717a;
  --border: #e4e4e7; --primary: #18181b; --primary-foreground: #fafafa;
  --secondary: #f4f4f5; --secondary-foreground: #18181b;
  --radius: 0.75rem;
  --shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --background: #09090b; --foreground: #fafafa;
    --card: #09090b; --muted: #27272a; --muted-foreground: #a1a1aa;
    --border: #27272a; --primary: #fafafa; --primary-foreground: #18181b;
    --secondary: #27272a; --secondary-foreground: #fafafa;
    --shadow: none;
  }}
}}
* {{ box-sizing: border-box; border-color: var(--border); }}
body {{
  margin: 0; background: var(--background); color: var(--foreground);
  font-family: "Geist", "Inter", ui-sans-serif, system-ui, -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif;
  font-size: 14px; line-height: 1.7; -webkit-font-smoothing: antialiased;
}}
main {{ max-width: 768px; margin: 0 auto; padding: 48px 16px 96px; }}
header {{ margin-bottom: 32px; }}
header h1 {{ font-size: 30px; line-height: 1.2; font-weight: 700; letter-spacing: -0.025em; margin: 0 0 8px; }}
header .meta {{ color: var(--muted-foreground); font-size: 14px; margin: 0; }}
section {{ margin: 48px 0; }}
h2 {{
  font-size: 20px; font-weight: 600; letter-spacing: -0.02em; margin: 0 0 16px;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}}
h3 {{ font-size: 16px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.4; margin: 0 0 16px; }}
p {{ margin: 0 0 12px; }}
ul, ol {{ margin: 0 0 12px; padding-left: 1.25em; }}
li {{ margin: 6px 0; }}
li::marker {{ color: var(--muted-foreground); }}
strong {{ font-weight: 600; }}
code {{
  font-family: "Geist Mono", ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em;
  background: var(--muted); padding: 2px 6px; border-radius: 6px;
}}
.card {{
  background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 24px; margin: 0 0 16px;
}}
.card ul {{ padding: 0; margin: 0; }}
li.kv {{
  list-style: none; display: grid; grid-template-columns: 9rem 1fr; gap: 16px;
  padding: 12px 0; margin: 0; border-top: 1px solid var(--border);
}}
li.kv:first-child {{ border-top: none; padding-top: 0; }}
li.kv:last-child {{ padding-bottom: 0; }}
.label {{ color: var(--muted-foreground); font-size: 13px; font-weight: 500; line-height: 1.7; }}
.value {{ min-width: 0; overflow-wrap: anywhere; }}
.hero {{
  border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow);
  padding: 24px; font-size: 15px; background: var(--card);
}}
.hero h2 {{
  border: none; padding: 0; margin: 0 0 8px; font-size: 13px; font-weight: 500;
  letter-spacing: 0; color: var(--muted-foreground);
}}
.hero p:last-child {{ margin: 0; }}
.next ol {{ counter-reset: step; list-style: none; padding: 0; margin: 0; }}
.next ol li {{
  counter-increment: step; position: relative; background: var(--card);
  border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow);
  padding: 20px 20px 20px 60px; margin: 0 0 12px;
}}
.next ol li::before {{
  content: counter(step); position: absolute; left: 20px; top: 20px; width: 24px; height: 24px;
  border-radius: 6px; background: var(--primary); color: var(--primary-foreground);
  display: grid; place-items: center; font-size: 12px; font-weight: 600; line-height: 1;
}}
.table-wrap {{
  overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow); background: var(--card);
}}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ text-align: left; vertical-align: top; padding: 12px 16px; border-bottom: 1px solid var(--border); }}
th {{ height: 40px; color: var(--muted-foreground); font-weight: 500; font-size: 13px; }}
tbody tr {{ transition: background-color .15s; }}
tbody tr:hover {{ background: var(--muted); }}
tr:last-child td {{ border-bottom: none; }}
td:first-child {{ font-weight: 500; min-width: 9em; }}
.badge {{
  display: inline-flex; align-items: center; padding: 2px 10px; border-radius: 6px;
  font-size: 12px; font-weight: 600; line-height: 1.5; white-space: nowrap; border: 1px solid transparent;
}}
.badge.high {{ background: var(--primary); color: var(--primary-foreground); }}
.badge.midhigh, .badge.mid {{ background: var(--secondary); color: var(--secondary-foreground); }}
.badge.low {{ background: transparent; color: var(--foreground); border-color: var(--border); }}
@media (max-width: 600px) {{
  main {{ padding-top: 32px; }}
  header h1 {{ font-size: 24px; }}
  .card, .hero {{ padding: 20px; }}
  li.kv {{ grid-template-columns: 1fr; gap: 2px; }}
}}
</style>
</head>
<body>
<main>
<header><h1>{title}</h1><p class="meta">{meta}</p></header>
{body}
</main>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--out")
    a = ap.parse_args()
    with open(a.report, encoding="utf-8") as f:
        md = f.read()
    out = a.out or os.path.splitext(a.report)[0] + ".html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(md))
    print(out)


if __name__ == "__main__":
    main()
