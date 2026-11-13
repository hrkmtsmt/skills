# hrkmtsmt skills

自分用の Claude Code プラグインマーケットプレイス。

## プラグイン

### coach

| スキル | 呼び出し | やること |
|---|---|---|
| analyze-me | `/coach:analyze-me` | `~/.claude/history.jsonl` の全プロンプトから、思考のクセ・理解できていること・できていないこと・作ると効くスキルを分析し、`~/.claude/analyze-me/reports/` に Markdown と HTML で保存する |

## インストール

```
/plugin marketplace add hrkmtsmt/skills
/plugin install coach@hrkmtsmt
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

`analyze-me` のスクリプトは Python 3 の標準ライブラリだけで動く。
