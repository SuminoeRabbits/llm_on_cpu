# Ollama Adapter の検証規則

この仕様は共通 Runner 契約と測定プロトコルの Ollama 向け写像である。具体的な配布物・モデル・設定は `specs/runners/*.json` を正本とする。

## コンテナ起動前の準備

モデルの blob は検証済み read-only bind mount、manifest 管理情報は各コンテナ専用 tmpfs とする。**manifest のディレクトリ作成と配置を完了してから Ollama serve を起動する。** 起動後に mkdir/cp すると、Ollama の不要ファイル整理と競合して消される場合がある。競合に対する再試行を推論測定へ混ぜない。イメージは再ビルドせず、初期化コマンドを起動時に渡せる。

コンテナの作成・cpuset・mount・所有ラベル・停止削除は Runtime、API・モデル照合・リクエスト生成は Adapter の責務。両者のコードを分離する。

## thinking 能力確認

`/api/show` の応答を反復の `show.json` に保存する。固定配布物で確認された能力一覧は `capabilities`、thinking 設定の許容値は **`thinking.values`**、既定値は `thinking.default`。存在しない `thinking_levels` を仮定しない。

named level を指定した Runner は、その文字列が `thinking.values` に存在することを確認する。bool 値は実際の応答で型・対応値を確認する。設定が未対応・未確認なら推論前に終了コード30で停止し、代替値へ変更しない。think=false なのに生成途中で thinking が返る場合も終了コード30。

## 動的テンプレートの固定（Runner 1.1.0 の追加項目）

モデルの重み・量子化・ユーザープロンプトが一致しても、モデルテンプレートに `{{ currentDate }}` が含まれる場合、実行日で実効入力が変わる。実行時の現在日付を再現性のある固定入力とみなさない。

`workload.template_date` は任意の ISO 日付文字列（YYYY-MM-DD）または null。日付の具体値は Runner にだけ記述する。未指定/null は日付上書きなしを意味し、動的日付を含むテンプレートでは実行を拒否する。

1. チェックサム検証済みのモデルテンプレートと `/api/show.template` の一致を確認する。
2. `{{ currentDate }}`（空白、左右の trim ハイフンを含む）を Runner の固定日付へ置換する。他のテンプレート機能・モデルパラメータは変更しない。
3. `/api/generate` の `template` に置換後の全文を渡す。元の blob/manifest は変更しない。
4. `currentDate` を含む未対応の式や、確認不能な他の動的入力は明示的に停止する。ホスト時計を暗黙入力にしない。
5. 実際に送った要求を反復の `request.json` に保存する。Runner snapshot に template_date を含め、Dashboard の比較条件にも含める。

この追加は Runner 1.1.0 / summary 3.1.0。既存 1.0.0 / summary 3.0.0 のファイルを変更せず互換検証する。新フィールドは任意であり、動的テンプレートを使わない旧 Runner の入力は変更しない。

## 実測の証跡

空プロンプトによるロードでは生成しない。`/api/ps` の digest・量子化・context_length・size_vram を検証し、生応答を保存する。生成前後の時刻、NDJSON、ログ、実際の要求、CPU制限の検証情報を保存する。ログの cached n_tokens と n_threads を照合し、証跡欠落を推定で補わない。

perf が利用可能な環境の制御用 FIFO 応答待ちと、その失敗時のプロセス回収もテストする。WSL 上で全イベントが unavailable の場合、取得成功経路を実機検証済みとは記載しない。

## キャッシュログの要求境界

`cached n_tokens` の全行がゼロであることは要求しない。固定モデルでは同じ生成タスクの初期化・チェックポイント処理で、同一要求内の非ゼロ値が記録される場合がある。これはプロトコルが許容する同一要求内KVと区別する。

反復あたり1件の `new prompt`、その task ID、同taskの **最初の** `cached n_tokens = 0` を確認する。その後の同taskの値は原ログとcache_evidenceに残す。別task、複数のnew prompt、開始時の非ゼロ、taskを特定できない証跡は未検証として終了コード32にする。単にログ中にゼロが1行あるだけでは合格しない。
