#!/usr/bin/env python3
"""Extract the user's own prompts from Claude Code history into an analysis-ready Markdown digest.

Usage:
  extract_prompts.py [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--project SUBSTR]
                     [--max-chars N] [--history PATH] [--out PATH]

Output: a stats header (counts, months, projects, slash commands, heuristic tags)
followed by every prompt grouped by session in chronological order, so short
follow-ups ("修正して", "よろ") can be read in context.

Tags are cheap heuristics to help the analyst find things; they are not the analysis.
  [Q]   question-shaped (〜って何 / なぜ / どうやって / ？ ...)
  [FIX] correction or redo (違う / そうじゃなく / 戻して / やり直し ...)
"""

import argparse
import collections
import datetime as dt
import json
import os
import re
import sys

Q_RE = re.compile(
    r"(って何|ってなに|とは[？?]?$|とは何|なぜ|なんで|どうして|どうやって|どうすれば|どう違う|違いは|教えて|わからない|分からない|わかってない|理解できて|意味は|[?？]\s*$|\bwhat\b|\bwhy\b|\bhow\b)",
    re.I | re.M,
)
FIX_RE = re.compile(
    r"(違う|ちがう|そうじゃな|戻して|元に戻|やり直|やめて|消して|間違|おかしい|うまくいかな|動かな|直って(い)?ない|まだ.*(エラー|ダメ|だめ)|意図と|そういう意味じゃ|revert)",
    re.I,
)


# secrets: long hex / base64-ish runs and common token prefixes
SECRET_RE = re.compile(
    r"(sk-[\w-]{10,}|gh[pousr]_\w{20,}|xox[abp]-[\w-]+|AKIA[0-9A-Z]{16}|\b[0-9a-fA-F]{24,}\b|\b[A-Za-z0-9_\-]{40,}\b)"
)
# vim/shell leftovers typed into the prompt box, and bare housekeeping commands
NOISE_RE = re.compile(
    r"^(:\w*!?|q|exit|/(resume|clear|exit|usage|export|copy|login|model|vim|cost|status|help))$",
    re.I,
)


def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def parse_date(s, end=False):
    d = dt.datetime.strptime(s, "%Y-%m-%d")
    return d + dt.timedelta(days=1) if end else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default=os.path.expanduser("~/.claude/history.jsonl"))
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--project", help="substring match on the project path")
    ap.add_argument(
        "--max-chars", type=int, default=500, help="truncate each prompt to this length"
    )
    ap.add_argument("--out")
    a = ap.parse_args()

    if not os.path.exists(a.history):
        sys.exit(f"history not found: {a.history}")

    rows = load(a.history)
    since = parse_date(a.since) if a.since else None
    until = parse_date(a.until, end=True) if a.until else None

    items = []
    noise = 0
    for r in rows:
        text = (r.get("display") or "").strip()
        if not text or "timestamp" not in r:
            continue
        t = dt.datetime.fromtimestamp(r["timestamp"] / 1000)
        if (since and t < since) or (until and t >= until):
            continue
        proj = r.get("project") or "?"
        if a.project and a.project not in proj:
            continue
        if NOISE_RE.match(text):
            noise += 1
            continue
        text = SECRET_RE.sub("[REDACTED]", text)
        items.append(
            {
                "t": t,
                "text": text,
                "project": proj,
                "session": r.get("sessionId") or proj + t.strftime("%Y%m%d"),
                "pasted": bool(r.get("pastedContents")),
            }
        )
    items.sort(key=lambda x: x["t"])
    if not items:
        sys.exit("no prompts in range")

    home = os.path.expanduser("~")

    def short(p):
        return p.replace(home, "~")

    def is_slash(text):
        # "/clear", "/grill-me plan..." are commands; "/lua/plugins/x.lua" is a path
        return re.match(r"^/[\w:.-]+(\s|$)", text) is not None

    slash = [i for i in items if is_slash(i["text"])]
    # commands with arguments still carry the user's own words, so analyse them too
    free = [
        i for i in items if not is_slash(i["text"]) or len(i["text"].split(None, 1)) > 1
    ]
    for i in items:
        i.setdefault("tags", [])
    for i in free:
        i["tags"] = [
            tag for tag, rx in (("Q", Q_RE), ("FIX", FIX_RE)) if rx.search(i["text"])
        ]

    out = []
    w = out.append
    w("# Prompt digest\n")
    w(f"- 期間: {items[0]['t']:%Y-%m-%d} 〜 {items[-1]['t']:%Y-%m-%d}")
    w(
        f"- プロンプト数: {len(items)}（自由記述 {len(free)} / スラッシュコマンド {len(slash)}、引数付きコマンドは両方に計上）"
    )
    w(f"- セッション数: {len({i['session'] for i in items})}")
    lens = sorted(len(i["text"]) for i in free) or [0]
    w(f"- 自由記述の文字数: 中央値 {lens[len(lens) // 2]} / 最大 {lens[-1]}")
    w(f"- 除外したノイズ（:q, 引数なしの /resume /clear /usage 等）: {noise}")
    w(f"- 貼り付けを含む: {sum(i['pasted'] for i in items)}")
    w(
        f"- [Q] 質問形: {sum('Q' in i['tags'] for i in free)} / [FIX] 修正・やり直し: {sum('FIX' in i['tags'] for i in free)}\n"
    )

    w("## 月別件数")
    for m, c in sorted(
        collections.Counter(i["t"].strftime("%Y-%m") for i in items).items()
    ):
        w(f"- {m}: {c}")
    w("\n## プロジェクト別件数")
    for p, c in collections.Counter(short(i["project"]) for i in items).most_common(15):
        w(f"- {p}: {c}")
    if slash:
        w("\n## スラッシュコマンド")
        for s, c in collections.Counter(
            i["text"].split()[0] for i in slash
        ).most_common(20):
            w(f"- {s}: {c}")

    w("\n## プロンプト（セッションごと・時系列）")
    w("凡例: `[Q]` 質問形, `[FIX]` 修正・やり直し, `[P]` 貼り付けあり, `…` 切り詰め\n")
    by_session = collections.OrderedDict()
    for i in items:
        by_session.setdefault(i["session"], []).append(i)
    for sid, ps in by_session.items():
        w(
            f"### {ps[0]['t']:%Y-%m-%d %H:%M} | {short(ps[0]['project'])} | {str(sid)[:8]}"
        )
        for i in ps:
            text = re.sub(r"\s*\n\s*", " ⏎ ", i["text"])
            if len(text) > a.max_chars:
                text = text[: a.max_chars] + "…"
            tags = "".join(f"[{t}]" for t in i.get("tags", [])) + (
                "[P]" if i["pasted"] else ""
            )
            w(f"- {i['t']:%m-%d %H:%M} {tags + ' ' if tags else ''}{text}")
        w("")

    result = "\n".join(out)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"wrote {a.out} ({len(result)} chars, {len(items)} prompts)")
    else:
        print(result)


if __name__ == "__main__":
    main()
