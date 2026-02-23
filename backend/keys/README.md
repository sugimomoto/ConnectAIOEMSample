# keys/

Connect AI API との通信に使用する RSA 鍵ペアを格納するディレクトリ。

## ファイル一覧

| ファイル名 | 内容 | Git管理 |
|-----------|------|---------|
| `private.key` | RSA 秘密鍵（4096bit）| **除外**（.gitignore） |
| `public.key` | RSA 公開鍵 | **除外**（.gitignore） |
| `parent_account_id.txt` | CData から発行された ParentAccountId | **除外**（.gitignore） |

## 鍵の生成方法

```bash
# 秘密鍵の生成（4096ビット）
openssl genrsa -out backend/keys/private.key 4096

# 公開鍵の生成
openssl rsa -in backend/keys/private.key -pubout -out backend/keys/public.key
```

## 登録手順

生成した `public.key` の内容を CData サポートチームに連携して登録します。
`private.key` は絶対に外部に共有しないこと。
