# hrkmtsmt skills

自分用の Claude Code プラグインマーケットプレイス。

## インストール

```
/plugin marketplace add hrkmtsmt/skills
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
