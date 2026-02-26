# requirements.md

## 関連 Issue

[#16 bug: externalId に user.id を使用しているため環境再構築時に重複が発生する](https://github.com/sugimomoto/ConnectAIOEMSample/issues/16)

## 変更・追加する機能の説明

CData Connect AI に子アカウントを作成する際に使用する `externalId` の値を、
SQLite の自動採番 `user.id`（整数）から `user.email`（メールアドレス）に変更する。

## 背景・問題

現在の実装では `externalId = str(user.id)` を使用しているため、
Docker ボリュームを削除して環境を再構築すると `user.id` が 1 からリセットされる。
その結果、新しく登録したユーザーが過去に削除された別ユーザーと同じ `externalId` を持ち、
CData 側の子アカウントが意図せず再利用・衝突するバグが発生する。

## ユーザーストーリー

- SaaS 管理者として、環境を再構築した後に新規ユーザーが登録しても、
  既存の CData 子アカウントと衝突しないことを期待する。

## 受け入れ条件

- `externalId` として `user.email` が CData Connect AI API に送信されること
- メールアドレスの重複はアプリ側の DB `UNIQUE` 制約によりすでに防止されているため、
  `externalId` の衝突が起こらないこと
- 既存のテストがすべてパスすること
- `docs/glossary.md` の `externalId` の定義が実装と一致していること

## 制約事項

- このアプリではユーザーがメールアドレスを変更する機能を持たないため、
  `externalId` の変更リスクはない
- 既存の CData 子アカウント（`externalId = str(user.id)` で作成済みのもの）は
  本修正の対象外とする（サンプルアプリのため既存データ移行は不要）
