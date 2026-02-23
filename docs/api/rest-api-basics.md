# REST API基本仕様

## リクエスト形式

- **Content-Type**: `application/json`
- **認証**: Bearer JWT（必須）

## レスポンス形式

すべてのAPIレスポンスはJSON形式で返却され、以下の最上位プロパティを含みます：

| プロパティ | 型 | 説明 |
|----------|-----|------|
| `results` | Array | クエリの結果セットの配列 |
| `parameters` | Object | ストアドプロシージャの出力/戻り値 |
| `error` | Object | エラー情報（エラーが発生した場合のみ） |

### 結果セット構造

各結果オブジェクトは以下を含みます：

```json
{
  "schema": [],      // カラムスキーマの配列
  "rows": [],        // 行データの配列（各行は値の配列）
  "affectedRows": 0  // 影響を受けた行数（-1の場合は非適用）
}
```

## エラーハンドリング

**重要：** HTTPステータスコード200が返された場合でも、レスポンス内の`error`プロパティを確認することが重要です。部分的な結果とエラー情報の両方が返される場合があります。

### エラーレスポンス例

```json
{
  "results": [...],
  "error": {
    "message": "エラーメッセージ",
    "code": "エラーコード"
  }
}
```

## サポートされるデータ型

以下の18種類のデータ型がサポートされています：

| データ型ID | データ型名 |
|----------|----------|
| 1 | BINARY |
| 2 | BIT |
| 3 | INTEGER |
| 4 | BIGINT |
| 5 | VARCHAR |
| 6 | DECIMAL |
| 7 | DOUBLE |
| 8 | FLOAT |
| 9 | BOOLEAN |
| 10 | DATE |
| 11 | TIME |
| 12 | TIMESTAMP |
| 13 | LONGVARCHAR |
| 14 | LONGVARBINARY |
| 15 | NULL |
| 16 | NUMERIC |
| 17 | CHAR |
| 18 | REAL |

---

[← トップに戻る](./README.md)
