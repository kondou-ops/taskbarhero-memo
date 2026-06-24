# TBH: Task Bar Hero 素材・装備メモ

- `index.html`: 画像付きメモ本体
- `tools/build_site.py`: 抽出済みデータから `index.html` を再生成するスクリプト
- `tools/update_market.py`: Steam Marketから日本円の最低価格・中央値・取引量を取得するスクリプト
- `.github/workflows/update-market.yml`: 毎日05:15(JST)ごろに価格を更新して公開ページを再生成
- `icons/`: ゲーム本体から抽出したアイコン
- `images/`: Steam公式マーケットから取得した掲載アイコン
- `ItemTable.csv` / `StringTable.csv`: 抽出元の日本語/英語ローカライズ表
- `market-items.json`: Steam公式マーケット検索結果と円建て価格

## 入っているもの

- 511件の素材/装備カード
- アイテムクリック時の用途・売却判断・関連レベル帯・マーケット表示
- 素材とレベル帯の整理表
- キャラクター別の装備/残すステータスメモ
- クラフト/売却ティア表
- 物理/攻撃速度、魔法/属性、防御/耐久のビルド別メモ
- Steam Marketの日本円価格、中央値、取引量
- 情報元ごとの正確性メモ

Steamの公開APIで安定取得できる価格は最低価格・中央値・取引量です。現在の最高売注文は未取得として表示しています。
価格は変動するため、売却前にSteamマーケットで再確認してください。
Xserverは使用しません。
