# Runner 契約

契約 ID：`runner/v1`。現行設定形式：`runner_schema_version: 1.1.0`（1.0.0互換）。本書は特定モデル・テスト項目に依存しない。具体的な版、モデル、プロンプト、必要メモリは Runner instance にだけ置く。

## 仕様の役割

- `runner.template.json`：未束縛のテンプレート。kind=template、実行禁止。
- `runner.schema.json`：template/instance の型と制約。
- `measurement-protocol.md`：変更禁止の測定境界・キャッシュ・集計規則。
- `summary-format.md` と summary schema：結果の記録形式と意味検証。

Template の null は未束縛を表し、結果データの unavailable と混同しない。instance 化では必要値を全て埋め、kind=instance にして Schema と意味検証を通す。プレースホルダーを残したまま実行しない。

## 設定の責務

| グループ | 内容 | 禁止事項 |
| --- | --- | --- |
| identity | 一意 ID・用途 | 実行時に名称から設定を推測しない |
| adapter | Framework Adapter ID と版 | 任意シェルによる計測処理の上書きを認めない |
| runtime | CPU アーキテクチャ、Ubuntuベースdigest、配布物URL・SHA256 | latest追従、GPUへの自動切替 |
| model | モデルID、manifest URL/digest、全blob、量子化 | メモリ不足時の自動軽量化 |
| workload | prompt、context_length、生成上限、seed、温度、thinking | 共通Token/sの式の変更 |
| measurement | protocol、反復、同時実行、事前生成数、perfイベント | protocolと矛盾する値 |
| resources | 最低利用可能メモリ | 必要量を実測済みだと偽ること |
| timeouts | 共通準備・反復・後始末の上限 | 受信ごとに締切をリセット |

## 実行インターフェース

各操作は共通実行制御から呼び出す。Adapter固有APIは内側に閉じ込め、ProviderをモデルRunnerへ埋め込まない。

| 操作 | 入力・事前条件 | 出力・成功条件 | 失敗時 |
| --- | --- | --- | --- |
| validate | instanceとHost情報 | schema適合、必要能力、資源確認 | 設定2、環境10。状態変更しない |
| prepare | 検証済instance・共通締切 | hash検証済配布物、image ID | 準備20、時間切れ31。未検証ファイルを使わない |
| start | image、CPU集合、専用領域 | 所有ラベル付き新規コンテナ、接続先 | 30/31、stopへ進む |
| verify | 起動済サービス、instance | CPUのみ、digest・量子化・context一致、先行生成なし | 不一致30、キャッシュ契約違反32 |
| measure | verify成功、プロトコル | 時刻、原応答、生成量、終了状態 | 30/31、原記録を残す |
| collect | 計測ログ・perf | CPU別イベント、欠測理由、キャッシュ証跡 | 環境欠測は成功を妨げない。解析異常はerror |
| stop | 所有リソース識別子 | 自分のコンテナ削除と証跡 | 50、次条件を停止 |

各操作の内部の戻り値型は自由だが、summaryの契約に完全に写像できること。例外・中断でもstopと結果保存へ進む。権限昇格・WSL再起動・クラウドリソース作成はAdapterの責務ではない。

## instance の意味検証

同じinstanceを本番・実験で使う。manifestのconfig/layersとblob一覧・digest・サイズを照合し、取得時にチェックサム検証する。promptは空文字不可、contextは入力と出力に必要な範囲を確保する。モデルがサポートしないthinking値は拒否する。資源の違いで設定を書き換えない。

測定方式を追加する場合は新しい protocol ID と定義・検証テストを先に作る。Framework固有の追加引数を共通測定項目へ混入させない。新しいsystem依存やAPI形式が必要なら、設定追加だけで対応したと偽らずAdapterを版管理する。

## 旧 Runner との関係（互換性の説明）

既存 `runners/ollama-*.json` は flat な Ollama固有形式であり、この汎用instanceとは別形式。既存実行器はまだ汎用形式を読み込まない。互換形式は `specs/compat/ollama-runner.schema.json` に保存する。

再生成時に既存固定値を次のように移す。元の値を更新・再選定しない。

- id/purpose → identity。framework_version → adapter.version、adapter.id=ollama。
- architecture/base_image/archive_url/archive_sha256 → runtimeの同名相当項目。
- model/model_manifest_url/model_manifest_sha256/model_manifest/model_config.file_type → modelのid/manifest_url/manifest_sha256/manifest/quantization。
- manifest内のconfigとlayers → model.blobs（重複digestは1つに集約）。URLはmanifestと同じregistry/repositoryのblobs/digest。
- measurement.prompt/num_ctx/num_predict/seed/temperature/num_batch/think → workload.prompt/context_length/max_output_tokens/seed/temperature/batch_size/think。
- measurement.mode=fresh_request_preloaded → measurement.protocol=fresh_request_preloaded/v1。
- repetitions/concurrency/warmup_requests、perf_events、minimum_available_memory_bytesは対応グループへ移す。
- timeout_seconds → timeouts.preparation_seconds/repetition_seconds、cleanup_seconds=60。

汎用snapshotを採用するsummaryは3.0.0。旧summaryのRunner snapshotはそのまま旧スキーマで検証する。新旧を区別せず同じ型として読まない。

## 現行固定 instance

再生成の正本は `specs/runners/*.json`。この具体化済みファイルを `runners/` に配置し、値を再選定しない。旧flatからの写像は過去データの互換説明であり、現行Runnerを二重に生成しない。`workload.template_date` の意味と検証は [ollama-adapter.md](ollama-adapter.md) に従う。summary 3.1.0以降は現行instanceを保存する。
