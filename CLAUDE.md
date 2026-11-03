# レースデータ帳 運用ルール

公営競技の公式成績を集計して公開する統計サイト。現在はボートレースのみ(競輪・JRAは今後追加予定)。
データ取得・集計・公開は GitHub Actions が自動で行う。Claude の仕事は **毎朝1本の記事を書いて main に push すること**。

## 仕組み

- `scripts/boat_fetch.py` … 公式の競走成績ファイルを取得・解析し `data/boat/races/YYYY-MM.csv.gz`(1レース1行)と `data/boat/entries/YYYY-MM.csv.gz`(1艇1行)に保存。boat-data ワークフローが毎朝 JST 6:17 に直近3日分を取得
- `scripts/boat_stats.py` … 集計して `data/boat/summary.json` を作る。**記事の数値は必ずこの出力か、下の「独自集計」の出力から取る**
- `scripts/build_site.py` … トップ・場別ページ(24場)・記事を `_site/` に生成。site ワークフローが main への push で公開
- 記事: `content/posts/YYYY-MM-DD-英小文字スラッグ.md`

### データの列

- races: date, jcd(場コード01〜24), venue, day(開催日目), rno, race_type(予選・優勝戦など), distance, weather, wind_dir, wind_m, wave_cm, kimarite, win/ex/qn/tri/trio の combo・pay(円)・pop(人気)
- entries: date, jcd, rno, finish(1〜6、または F・L・K0・S0 など), boat(艇番), racer_id, racer_name, course(進入コース), st(スタートタイミング), flying

## 毎朝の手順

1. `git pull` → `python scripts/boat_stats.py` を実行して最新の集計を確認する(`--venue 01` で場別の詳細)
2. `content/posts/` の既存記事タイトルを見て、テーマが重複しないようにする
3. 下の「記事の種類」から今日の記事を決めて書く
4. **検証**: 記事中のすべての数値(%・円・件数・期間)を集計出力と照合する。割り算や差は Python で計算して確かめる。データ以外の事実(ルール・制度など)は WebSearch で公式情報を確認し、確認できないことは書かない
5. `pip install -q jinja2 markdown pyyaml && python scripts/build_site.py` でビルドが通ることを確認
6. `git pull --rebase` → `git add content/posts scripts/adhoc && git commit -m "記事: タイトル" && git push origin main`
7. 数分後に `https://api.github.com/repos/kotsuo07/race-stats/actions/runs?per_page=3` で site ワークフローが success か確認。失敗なら直して再 push
8. 最後に記事タイトル・要点2〜3行・URL を報告する(データ取得の失敗などがあればそれも)

## 独自集計

summary.json にない切り口(季節別、優勝戦だけ、特定の選手など)を使うときは、`scripts/adhoc/YYYY-MM-DD-内容.py` に集計スクリプトを書いて実行し、その出力の数値だけを記事に使う。スクリプトも一緒にコミットする。件数(分母)を必ず記事に書く。分母が300未満の数値は「参考値」と明記する。

## 記事の種類(曜日でローテーション)

- 月: 場別データ紹介(場コード順に1場ずつ。summary.json の場別データ+独自集計で特徴を解説。場別ページへリンク)
- 火: 解説記事(進入と枠番の違い、決まり手、万舟、スタートタイミング、展示タイムなど、まだ書いていないテーマ)
- 水: 全国ランキング(1コース1着率、万舟率、3連単中央値などの場別順位と、前回からの変化)
- 木: 条件別の傾向(風速・波高・天候・季節・レース種別などで成績がどう変わるか)
- 金: 2場の比較(似た特徴・対照的な特徴の場を並べる)
- 土: 先週の振り返り(先週の高配当、1コース1着率の平年との差など)
- 日: Q&A(「1号艇はどれくらい勝つ?」「万舟はどのくらい出る?」など)

## 書き方

- 1記事 1,500〜3,000字。冒頭3行で結論(数字入り)
- 見出し(##)3〜6個、表を1つ以上
- 数値には集計期間とレース数を添える(例:「2025年11月〜2026年11月の1万6,000レース」)
- 想定読者はボートレースを始めたばかり〜中級者。用語は初出で説明
- 場別ページ・トップ・関連記事への内部リンク(`/race-stats/` で始まる絶対パス。場別は `/race-stats/boat/venue/01/` の形)

### 前付け

```
---
title: タイトル(32字前後、場名・「1コース」「1着率」など検索語を前半に)
date: YYYY-MM-DD
description: 120字前後の要約
tags: [ボートレース, 1コース, 大村]
---
```

## 禁止事項

- データにない数値の創作。推測は「推測」と明記
- 「必ず当たる」「儲かる」「勝てる買い方」など的中・利益を約束する表現、買い目の推奨。統計の紹介にとどめ、「過去の傾向で将来を保証しない」趣旨を必要に応じて添える
- 20歳未満を対象にした表現。のめり込みを助長する表現
- 公式サイトや他サイトの文章・表のコピー
- 運営者が個人的に使っている買い方のルールは載せない
- `data/`・`scripts/`(adhoc を除く)・`.github/` の変更は、取得の不具合を直す場合だけ(直したら報告に書く)
