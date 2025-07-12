# Construction Term Extractor

建築業界の専門用語を抽出・検索するシステムです。PDFドキュメントから専門用語を自動抽出し、高速検索可能なデータベースを構築します。

## 機能

- **PDF専門用語抽出**: 建築関連PDFから専門用語を自動抽出
- **ハイブリッド検索**: ベクトル検索とテキスト検索を組み合わせた高精度検索
- **REST API**: 他システムとの連携用API
- **リアルタイム用語検索**: 音声認識システムとの連携を想定した高速検索

## インストール

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt

# Sudachi辞書のダウンロード
python -m sudachipy link -t core
```

## 使い方

### 1. APIサーバーの起動

```bash
python main.py
```

サーバーは `http://localhost:8000` で起動します。

### 2. API エンドポイント

#### 用語検索
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "コンクリート",
    "search_type": "hybrid",
    "limit": 10
  }'
```

#### テキストから用語抽出
```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "鉄筋コンクリート造の基礎工事を実施します。"
  }'
```

#### PDFバッチ処理
```bash
curl -X POST "http://localhost:8000/api/v1/extract/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_folder": "/path/to/pdf/folder",
    "rebuild_db": true
  }'
```

### 3. テストスクリプト

```bash
# サンプルテキストでテスト
python test_extractor.py

# PDFフォルダでテスト
python test_extractor.py /path/to/pdf/folder
```

## API仕様

完全なAPI仕様は起動後に `http://localhost:8000/docs` で確認できます。

## システム構成

```
term_extractor/
├── api/           # FastAPI関連
├── core/          # コア機能
│   ├── pdf_extractor.py    # PDF用語抽出
│   └── term_database.py    # 検索データベース
├── data/          # データベースファイル
└── tests/         # テストコード
```

## 将来の連携

このシステムは以下の連携を想定しています：

1. **音声認識システム**: リアルタイム用語修正
2. **議事録生成システム**: 専門用語の標準化
3. **タグ付けシステム**: 抽出用語の自動分類

## ライセンス

本プロジェクトは検証用です。