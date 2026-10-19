# ベンチマーク対象モデルと追加手順

対象モデルの案内を本書に集約する。バージョン、重み revision/digest、量子化、コンテキスト長、プロンプト、反復数、資源要件の正本は各 Runner JSON であり、一覧や README に固定値を複製しない。

## 対象一覧

| モデル | 用途 | Runner の正本 |
| --- | --- | --- |
| Qwen3-30B-A3B | 正式比較対象 | [ollama-qwen3-30b-a3b.json](runners/ollama-qwen3-30b-a3b.json) |
| gpt-oss-20B | 正式比較対象 | [ollama-gpt-oss-20b.json](runners/ollama-gpt-oss-20b.json) |
| Qwen3 小型モデル | 実行経路の動作確認（既定） | [ollama-qwen3-smoke.json](runners/ollama-qwen3-smoke.json) |
| Qwen3 小型モデル | 性能ばらつきの追加確認 | [ollama-qwen3-stability.json](runners/ollama-qwen3-stability.json) |

Runner 未指定時の既定 ID は `ollama-qwen3-smoke`。明示指定された Runner が環境条件を満たさなければ理由を報告して停止し、小型モデルへ自動代替しない。正式比較には本番・実験とも同じ Runner を使用する。スモーク成功から正式対象の実行成功や性能の安定性を推定しない。

一覧への掲載は実機検証済みを意味しない。検証済み範囲は生成後の README と実行証跡に記載する。

## モデルまたは測定条件を追加する手順

1. [runner.template.json](runner.template.json) を元に `specs/runners/<runner_id>.json` を作る。同じモデルでも測定条件・用途が異なれば別 ID とする。
2. `kind=instance` にして、Framework・CPU アーキテクチャ・配布物 URL/digest・モデル manifest/blob・量子化・測定条件・資源・タイムアウトを全て固定する。モデル名だけを既存 Runner で置換しない。未束縛の null や latest 自動追従は認めない。
3. [runner.schema.json](runner.schema.json) と [runner-contract.md](runner-contract.md) で型・意味を検証する。必要に応じて [ollama-adapter.md](ollama-adapter.md) の能力とテンプレートを検証する。
4. 本書の一覧に追加する。共通実行器は `specs/runners/*.json` を生成先 `runners/` へ配置し、全 JSON を検証して `identity.id` で列挙・選択する。ファイル名の stem と ID は一致させ、重複 ID は入力エラーとして拒否する。固定のモデル件数・名前による分岐を増やさない。
5. [入力更新手順](README.md) に従い manifest を更新する。既存 Adapter で扱える追加では要件書・Schema・共通計測コードを変更しない。新しい Framework/API/測定方式が必要なら、先に契約と Adapter を拡張する。
6. 実環境の前提確認、固定データの取得・検証、スケーリング測定、summary 検証、ログ監査を行い、未検証・環境上取得不能・失敗を区別して記録する。資源不足を検証成功と扱わない。

モデル追加で Token/s の式、perf 計測区間、キャッシュ分離、品質判定を変更しない。これらは measurement-protocol.md と summary-format.md に従う。
