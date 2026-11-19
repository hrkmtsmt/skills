# hrkmtsmt skills

自分用の Claude Code プラグインマーケットプレイス。

## プラグイン

### coach

| スキル | 呼び出し | やること |
|---|---|---|
| analyze-me | `/coach:analyze-me` | `~/.claude/history.jsonl` の全プロンプトから、思考のクセ・理解できていること・できていないこと・作ると効くスキルを分析し、`~/.claude/analyze-me/reports/` に Markdown と HTML で保存する |

### memo

| スキル | 呼び出し | やること |
|---|---|---|
| jot | `/memo:jot` | 会話の途中で「忘れないうちに」と出てきたこと（アイデア、TODO、確認事項など）を `~/.claude/memo/memo.db`（SQLite）に1行で書き留め、すぐ本題に戻る。一覧・済み・見送りの管理と、会話の締めくくりでの振り返りもする |

## インストール

```
/plugin marketplace add hrkmtsmt/skills
/plugin install coach@hrkmtsmt
/plugin install memo@hrkmtsmt
```

## 開発

Node.js 系のツールは pnpm workspace、Python 系のツールは uv workspace で管理する。

```bash
pnpm install
uv sync
```

| チェック | コマンド |
|---|---|
| プラグインの検証 | `claude plugin validate . --strict` |
| 文章の校正（textlint + preset-ja-technical-writing） | `pnpm lint:text` |
| Python の lint | `uv run ruff check` |
| Python のフォーマット | `uv run ruff format --check` |

同じチェックを GitHub Actions（`.github/workflows/ci.yml`）で push と pull request ごとに実行する。

`analyze-me` と `jot` のスクリプトは Python 3 の標準ライブラリだけで動く。
