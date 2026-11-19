# メモの一覧・済み・見送り・振り返り

SKILL.md の「書き留める」以外の操作。どの出力もコンテキストに残るので、必要な範囲だけを取り出す。

## 一覧・済み・見送り

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py list                    # 今のプロジェクトの未着手
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py list --all              # 今のプロジェクトの済み・見送りも
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py list --project api      # 別のプロジェクト
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py list --all-projects     # 全プロジェクト
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py list --ids 2 3          # 番号で指定
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py done 3 7                # 済んだ
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py drop 5                  # やらないと決めた
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py export --all > memo.md  # 全プロジェクトを Markdown に書き出す
```

`list` は何も指定しなければ今のプロジェクトだけを出す。メモが溜まっても出力が膨らまないようにするため。全プロジェクトを出すのは、ユーザーが「全部」「他のプロジェクトも」と言ったときだけにする。
メモは SQLite に入っているので、読み書きは必ずこのスクリプトを通す。DB を直接開いて編集しない。
一覧は出力をそのまま見せる（日付・プロジェクト付きの箇条書きで十分）。並べ替えや分類は頼まれたときだけ。
ファイルとして手元に欲しい、エディタで眺めたいと言われたら `export` で Markdown に書き出す。
「#3 やった」「それはもういい」のように番号や内容で指されたら、該当を `done` / `drop` にする。どれか曖昧なら一覧を出して確認する。

## 締めくくりでの振り返り

ユーザーが会話を締めくくったときに、このセッションで書き留めたメモのうち未着手のものを振り返る。
どのメモをこのセッションで書いたかは、会話の中で自分が返した `📝 #番号 メモした` を見ればわかる。その番号だけを `--ids` で取り出す。

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/jot.py list --ids 2 3
```

`--ids` は未着手のものだけを返す。途中で済んだメモは出てこない。
残っていれば、締めくくりの返事の最後に次の形で短く添える。

```
📝 このセッションのメモ（未着手）
- #2 ○○
- #3 △△
どれか今やる？ 残しておくなら何もしなくてOK。
```

振り返りは締めくくりごとに一度だけ。同じメモを何度も出すと邪魔になる。ユーザーが選んだメモに取り組んで終えたら `done` にする。
