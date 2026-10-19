# summary.json フォーマット契約

各ホストは実行単位で `results/<run_id>/summary.json` を生成する。1 実行は、1 つのホスト・Framework・モデル・ワークロード条件について、4 段階の vCPU スケーリングと各段階の繰り返し測定から構成する。条件別の結果は `scaling.results[]` に分離する。

本書と同ディレクトリの `summary.schema.json` を、ベンチマーク結果のデータ契約の基準とする。フィールド名、階層、型、単位、集計方法、欠測・失敗の表現をここで定義し、収集・Runner・集計・Dashboard の各スクリプトをこの仕様に従わせる。スクリプトの都合で独自フィールドや解釈を先行導入しない。

### 仕様を先に変更する運用

追加・変更は必ず次の順序で行う。

1. **本セクションを更新する**：変更する階層・フィールド、意味、型、単位、必須/任意、欠測時の値・理由、集計方法、互換性への影響を定義し、JSON 例と `schema_version` を必要に応じて更新する。
2. **機械検証用スキーマを更新する**：`specs/summary.schema.json` を本セクションに合わせ、正常・欠測・失敗・複数スケーリング条件の検証用サンプルを更新する。JSON Schema だけで表現できない参照整合性・計算式は検証処理で扱う。
3. **生成側を更新する**：Provider、Host 検出、Runner、perf 収集、集計、料金計算が新仕様を出力するように変更する。
4. **利用側を更新する**：Dashboard と比較・分析スクリプトの参照先を合わせる。本書の他セクションと実装後の README.md はこの仕様を参照し、別の定義を持たせない。
5. **整合性を検証する**：生成 JSON のスキーマ適合、4 段階の結果・各反復・各 vCPU の対応、集計と費用計算、Dashboard の欠測表示、対応する旧版の読み込みを確認する。

仕様・スキーマ・生成側・利用側が一致して初めて変更完了とする。差異を発見した場合は本セクションを基準に修正し、仕様そのものを変える必要があれば手順 1 に戻る。既存の結果ファイルを新仕様に合わせて暗黙に書き換えない。

### 運用区分・ホストとコンテナ OS の記録

以下を初期スキーマ `1.0.0` の必須項目とする。

| フィールド | 型・値 | 意味 |
| --- | --- | --- |
| `execution.profile` | string: `production` / `experimental` | 性能評価と開発実験の区分。実行設定で明示指定 |
| `environment.os` | object: `name`, `version` は string | 実際のホストディストリビューション。コンテナの OS で上書きしない |
| `environment.kernel_release` | string | 実際の実行ホストのカーネルリリース |
| `environment.virtualization` | object: `kind`, `status`, `reason` | `kind` は `wsl2` / `vm` / `bare_metal` / `unknown`。取得不能理由を記録 |
| `execution.container_os` | object: `name`, `version` は string | コンテナ内で検証した `Ubuntu` / `26.04` |

運用区分は単なる欠測フラグではなく、比較条件の一部とする。Dashboard は区分を表示し、`production` と `experimental` を同じ比較系列に混在させない。

### バージョンと互換性

- `schema_version` は `MAJOR.MINOR.PATCH` 形式の文字列とし、初期版は `1.0.0` とする。
- 階層・フィールド名・型・単位・計算の意味の変更、削除、必須項目追加など、旧版の読み書きと互換性を保てない変更は MAJOR を上げる。
- 既存項目の意味を変えない任意項目追加は MINOR を上げる。互換性を維持する利用側は未知の任意項目を無視できるようにする。
- データ契約を変えない記述の明確化・スキーマの誤記修正は PATCH とし、単なる本書のレイアウト変更では更新しない。
- 利用側は対応する版を明示し、未対応 MAJOR はエラーとして報告する。旧版対応は明示的な変換処理を通し、不足する値を推測して補完しない。
- Schema から作る合成サンプルと実測データを区別する。型・必須性は`specs/summary.schema.json` に従い、検証用サンプルは再生成時に作成する。


### run_id の命名規則

結果ディレクトリを一覧しただけで環境・LLM・実施日時を判別できるよう、次の形式に統一する。

```text
<provider>__<platform>__<arch>__<framework>__<model>__<quantization>__<timestamp>__<nonce>
```

| 要素 | 内容 |
| --- | --- |
| `provider` | `native` または `aws` |
| `platform` | AWS はインスタンスタイプ、Native は設定したホスト表示名を正規化した文字列 |
| `arch` | `x86_64` または `arm64` |
| `framework` | `ollama` または `vllm` |
| `model` | `qwen3-30b-a3b`、`gpt-oss-20b` などのモデル識別名 |
| `quantization` | 実際の量子化方式。未確定なら `unknown`、非量子化なら記録した精度名 |
| `timestamp` | 実行開始時刻。UTC の `YYYYMMDDTHHMMSSmmmZ`（ミリ秒付き） |
| `nonce` | 実行ごとに生成する 8 桁の小文字 16 進数。並列実行・同時刻の衝突を回避 |

例（量子化名は命名例であり、採用設定を指定するものではない）：

```text
results/aws__m8g.4xlarge__arm64__ollama__qwen3-30b-a3b__q4-k-m__20261016T010203456Z__a1b2c3d4/summary.json
results/native__lab-server-01__x86_64__vllm__gpt-oss-20b__unknown__20261016T020304567Z__e5f6a7b8/summary.json
```

- 可変の表示名は小文字化し、英数字・ハイフン・ドット以外をハイフンに置換する。連続するハイフンはまとめ、先頭・末尾のドットとハイフンを除去する。空になった場合は `unknown` とする。区切りの `__` は表示名に含めない。
- `platform` と `model` はそれぞれ最大 48 文字、`quantization` は最大 24 文字とする。長すぎる値は末尾を元の値の SHA-256 先頭 8 桁に置き換え、ハイフン込みで上限以内に収める。元の完全な名称は summary に保存する。
- 実行開始時に ID を一度確定し、`run.id` とディレクトリ名を一致させる。作成先が既存なら nonce を再生成し、既存結果を上書きしない。後からメタデータが判明しても ID は変更しない。
- 1 つの run に 1/4・1/2・3/4・4/4 と各反復を含めるため、使用 vCPU 数や反復番号は run_id に入れず `scaling.results[]` で区別する。
- run_id は人が整理するためのラベルとし、Dashboard は名前を解析して情報を補完しない。正式な環境情報、モデルのリビジョン、量子化、時刻は summary の各フィールドを参照する。

### JSON 階層の定義（現行 schema_version: 3.2.0）

**1 run = 1 ホスト・1 Framework・1 モデル・1 ワークロードの全スケーリング結果**とする。1/4・1/2・3/4・4/4 ごとに summary ファイルを分けない。初期スキーマ `1.0.0` の階層を維持し、2.0.0のモデル同一性・thinking検証を維持し、3.0.0で汎用Runnerと表示パスを採用する。

```text
summary.json
├── schema_version
├── run                         # 全体の ID・時刻・状態
├── environment                 # 共通：Provider・OS・カーネル・CPU トポロジー
├── platform                    # 共通：表示名・CPU 仕様・メモリ容量・帯域
├── toolchain                   # 共通：ツールのバージョン
├── framework / model / workload # 共通：全条件で変えない推論設定
├── execution / cache_policy    # 共通：実行・キャッシュ制御方針
├── profiling                   # 共通：収集設定のみ。測定値は置かない
├── pricing                     # 共通：単価・内訳・出典
├── cost                        # 全 run の時間・推定料金
├── scaling
│   ├── plan                    # nproc・要求比率・CPU 選択方針・基準条件
│   └── results[]               # 実使用 vCPU 数ごとに 1 要素
│       ├── condition_id / requested_ratios / status / reason
│       ├── resources           # 使用 vCPU 数・CPU ID・スレッド・メモリ設定
│       ├── metrics             # この条件の性能集計値
│       ├── profiling           # この条件の perf 比較用集計値
│       ├── cost                # この条件の全反復の時間・推定料金
│       └── repetitions[]
│           ├── repetition_id / status / reason / timing
│           ├── isolation      # 実効 CPU 設定・コンテナ・キャッシュ検証
│           ├── metrics        # この反復で実測した Token/s 等
│           ├── profiling      # この反復・各 vCPU の perf 実測値
│           ├── cost           # この反復の時間・推定料金
│           └── artifacts      # この反復のログ・時系列の参照
└── artifacts                   # 共通設定・共通ログの参照
```

環境情報は各条件にコピーせず、上位を唯一の参照元とする。`environment` は Provider・OS・カーネル・CPU ID とコア/NUMA の対応・能力検出を担当し、CPU 名・総 vCPU 数・メモリ仕様は `platform` に集約する。`environment.aws` は Native では `null` とする。

上位の `framework` にはバージョン・CPU バックエンド・固定起動設定のみを置く。CPU 数で変わる起動引数・スレッド数は `resources`、起動後の実効値は反復の `isolation` に保存する。共通の `cache_policy` と `profiling` は要求方針・収集設定だけを持ち、その成否や実測値は各反復に保存する。

Platform のクロック・メモリ帯域は事前に取得したホストの参考値である。推論中に取得するクロックや帯域などの変動値は反復の `profiling` に保存し、共通仕様を上書きしない。共通のモデル・ワークロード・環境が途中で変わった場合は同じ run に混在させず、新しい run を開始する。

### 条件・反復・vCPU の識別と比較

| 階層 / キー | 定義 |
| --- | --- |
| `scaling.plan` | `base_nproc`、`available_cpu_ids`、`requested_ratios`、丸め・CPU 選択方針、`baseline_condition_id`、実行順序 seed |
| `results[].condition_id` | run 内で一意な `vcpu-4` 等。配列の位置ではなくこの ID で参照 |
| `results[].requested_ratios` | `['1/4']` 等の要求比率。丸めで同じ CPU 数になる場合は複数の比率を同じ条件に対応付ける |
| `results[].resources` | `vcpu_count`、`cpu_ids`、`threads`、NUMA メモリ配置、メモリ上限等の要求値 |
| `results[].metrics` | `aggregation`、予定・成功・失敗反復数、Token/s の中央値、TTFT 等、`speedup`、`parallel_efficiency` |
| `results[].profiling.perf` | その条件だけの比較用集計。`per_vcpu[]` の各 CPU ごとにイベント率・IPC 等を集計 |
| `repetitions[].repetition_id` | 条件内で一意な正整数。実際の全体実行順序は `timing.sequence_index` に保存 |
| `repetitions[].timing` | UTC の開始・終了時刻、性能測定区間の時刻と `measurement_duration_seconds` |
| `repetitions[].metrics` | 生成トークン総数・成功/失敗リクエスト数・Token/s・遅延等の実測値 |
| `repetitions[].profiling.perf.per_vcpu[]` | `cpu_id`、`events`、`derived`。選択 CPU ごとの反復内実測値 |
| `events.<event_name>` | `value`、`unit`、`status`、`reason`、計測稼働時間・稼働率・多重化補正情報 |
| `derived` | IPC・ミス率等。各値にも状態・欠測理由を付ける |
| 各階層の `cost` | 反復 → 条件 → run の順に対象時間を集計。run には共通準備・待機時間も含む |

`results[]` は使用 vCPU 数の昇順、`per_vcpu[]` は CPU ID 順で保存する。実行順序とは分ける。`resources.vcpu_count` と CPU ID 数を一致させ、反復の perf には選択 CPU ごとの要素を用意する。取得不能な CPU / イベントも状態と `null` を残し、欠落とゼロを区別する。

条件ごとの perf 集計は、成功反復の有効値から算出する。イベントごとに「反復内カウンタ / 実測秒」の中央値を `events_per_second` として保存し、IPC 等は各反復内で正しく算出した比率の中央値を保存する。`aggregation`、`valid_samples`、`excluded_samples`、除外理由を付け、CPU 数の異なる条件の生カウンタを合算しない。反復内の生カウンタは必ず保持する。

推論状態と perf 状態は別管理とする。条件・run の状態は `pending` / `running` / `success` / `partial` / `failed` / `unsupported` / `cancelled` とし、未実行・失敗条件も `results[]` に残す。集計対象がなければ値は `null` とし、基準条件が無効なら向上率・並列効率も `null` にする。

### Platform・性能指標のフィールド定義

`platform` は Native / AWS 共通で収集し、AWS 仕様値がなくても構築できるようにする。

- `platform.name`、`platform.cpu.name`、`platform.vcpu_count`、`platform.memory.capacity_bytes` を保存する。表示名は収集時の設定から summary に取り込み、Dashboard がホスト名から推測しない。
- `platform.cpu.clock` は `hz`、`kind`、`source`、`status`、`reason` を持つ。実測時は取得方法・測定区間・集計方法も保存する。CPU 周波数が公開されない VM は `null` とし、公称値を実測値と混同しない。
- `platform.memory.bandwidth` は `bytes_per_second`、`kind: measured|published`、`source`、`status`、`reason` を持つ。実測値を優先し、公称値しかない場合はその旨を表示する。帯域はメモリ容量やクロックから推測しない。
- メモリ帯域の実測は推論前の独立したホスト検証として行い、使用ツール・バージョン・処理種別（read / copy / triad 等）・配列サイズ・反復数・集計方法・使用 CPU ID・スレッド数・NUMA 配置を保存する。共通手法を固定して比較し、異なる手法の値は同等として扱わない。測定ツールの選定は実装時に行う。
- `scaling.results[].metrics.output_tokens_per_second` は、成功リクエストの生成トークン総数を、その反復の負荷生成開始から全リクエスト完了・タイムアウト確定までの実測経過秒で割った値とする。並列リクエストの個別所要時間を足して分母にしない。反復の集計は中央値とし、各反復の生成トークン数・実測秒・Token/s と集計方法を保存する。エラー数・成功率を併記し、不完全な測定を正常結果と混同しない。

### 時間単価・利用料金の定義

価格の取得・設定は AWS Provider または summary 作成前のメタデータ収集で実施する。API から取得できない場合は、出典付きの明示設定を取り込めるようにする。Dashboard 生成時の価格再取得は行わない。

`pricing` には次を保存する。

- `status`、`reason`、`currency`、`region`、OS、tenancy、購入方式（On-Demand / Spot / 契約単価など）、価格の適用日時・取得日時・出典 URL または識別子。
- `compute_hourly_rate`：インスタンス全体の時間単価。
- `storage[]`：対象ディスクの種別・容量・課金単位、容量料金、追加 IOPS・スループット等の該当料金、各単価の出典と時間換算値。root とモデル・結果保存用の課金対象ストレージを含め、料金に含まれる instance store を重複加算しない。
- `storage_hourly_rate`：ストレージ内訳の時間換算値の合計。月単価を換算する場合は `monthly_conversion_hours` を必ず保存し、換算の前提を固定する。
- `total_hourly_rate = compute_hourly_rate + storage_hourly_rate`。必須内訳が不明なら合計は `null` とし、計算可能な内訳だけを別表示する。

料金は以下の式で summary 生成時に算出する。金額は十進数で計算・保存し、表示時のみ丸める。

```text
estimated_amount = total_hourly_rate × duration_seconds / 3600
```

CPU を 1/4 に制限しても同じインスタンスを利用しているため、時間単価を 1/4 に割り引かない。Native は標準で `pricing.status: not_applicable` とし、時間単価・利用料金は `null`（N/A）とする。

条件別の `cost.duration_seconds` は、その条件の全反復についてコンテナ作成開始から破棄完了までの経過時間の合計とする。ロード・ウォームアップ・推論・後処理を含み、性能測定区間の秒数とは別に保存する。共通の初回ビルド・モデル取得等は `cost.shared_setup_duration_seconds`、条件間の待機等は `cost.other_duration_seconds` として保存する。実行全体は共通準備開始から最終コンテナ破棄までを対象とし、条件別時間＋共通準備＋その他時間に分解できるようにする。Dashboard 生成時間は含めない。

この金額は **ベンチマーク実行区間に配賦した推定利用料金**であり、AWS の確定請求額ではない。AWS はリソースごとの課金期間・最小課金単位を持ち、ストレージの保持期間も推論実行時間と一致するとは限らない。[EC2 On-Demand](https://docs.aws.amazon.com/us_en/AWSEC2/latest/UserGuide/ec2-on-demand-instances.html)、[EBS 料金](https://aws.amazon.com/ebs/pricing/)

`cost` には対象開始・終了時刻、`duration_seconds`、適用時間単価、`estimated_amount`、通貨、`method: hourly_rate_times_elapsed`、対象範囲・除外項目を保存する。ベンチマーク外の起動時間、残置ストレージ、通信、スナップショット、税金等は標準計算に含めず明示する。変動価格は実行中固定の価格スナップショットによる推定と表示し、異なる通貨を合算しない。

### 初期実装の完全定義と状態値

[summary.schema.json](summary.schema.json)を本節に対応する機械検証可能な全フィールド定義として提供する。各 object は許可したフィールドのみを受け付け、必須キー、型、値域、enum、null 許容を定義する。説明用抜粋ではなく `tests/fixtures/` に有効な完全サンプルを置く。契約変更は本節を先に更新し、その後にスキーマと実装を同期する。

測定値・メタデータの取得状態は以下で統一し、`run.status` 等の実行状態とは別に管理する。

| status | 意味 | value と reason |
| --- | --- | --- |
| `ok` | 実装済みで実際に取得できた | value は実値、reason は null |
| `not_implemented` | 取得処理をまだ実装していない | value は null、reason に未実装機能 |
| `unavailable` | 取得処理はあるが環境・権限・機能不足で取得不能 | value は null、reason に権限不足や PMU 未提供等 |
| `not_applicable` | Native のクラウド料金等、適用対象外 | value は null、reason に対象外の理由 |
| `disabled` | 設定により明示的に無効 | value は null、reason に設定理由 |
| `error` | 取得を試みたが処理・解析等が異常終了 | value は null、reason に原因 |

数値計測値は `{value, unit, status, reason}` を基本形とし、perf イベントは計測稼働率・時間を追加する。条件 perf 全体では `partial`（一部取得）も使用する。クロックとメモリ帯域は従来定義の単位付きキーを維持し、同じ状態規則を適用する。費用の金額・単価は十進数文字列または null とする。

性能 metrics は条件集計と反復の型を分ける。取得失敗・未実行の metrics は null、失敗原因は当該条件・反復の reason に置く。成功 metrics では実トークン数、経過秒、Token/s、リクエスト件数、終了理由を必須にする。条件集計は成功反復のみを採用し、成功・失敗・予定反復数と集計方法を保存する。

CPU 数と ID 数、CPU 集合の包含関係、要求比率の網羅、ID の一意性、親子の状態整合、Token/s と向上率・効率の式、費用の時間内訳、Native の料金 null、成功反復の CPU 配置・キャッシュ検証を意味検証する。Runner snapshot の型も完全定義する。manifest/config の配布元が将来フィールドを変更した場合も、黙って無視せず Runner スキーマを更新して追従する。`not_implemented` を環境欠測に偽装しない。段階 A のメモリ帯域測定・Performix・Dashboard は未実装として明示する。段階 B では Dashboard を実装し、生成した相対パスを artifacts.dashboard に保存する。AWS の詳細課金メタデータと課金演算は後続段階で仕様・スキーマを追加する。初期実装では Native の費用フィールドを必須の null / not_applicable として検証し、実装していない AWS の料金を計算できるとは扱わない。

### 本番・WSL で同じモデルを使う固定契約

モデルごとに同じ Runner ファイルを本番と WSL に配布し、manifest SHA-256、全 blob の SHA-256、量子化、num_ctx を一致させる。タグ名だけの一致を同じ重みとは扱わない。配布元のタグが更新されても自動追従せず、不一致なら準備を中止する。モデルロード後の `/api/ps` でも digest・量子化・実効 context_length を照合し、違えば測定を開始しない。メモリ不足時にモデル・量子化・コンテキスト長を自動変更しない。

同じモデルの本番・実験条件をそろえることと、異なるモデル同士の量子化・thinking 機能を同一にすることは区別する。モデル固有の thinking 設定も Runner で固定し、対応値を `/api/show` で検証する。正式対象 Runner の作成は、実機動作確認完了や AWS Provider 対応完了を意味しない。

#### 旧 summary schema 2.0.0 の互換情報

モデル固有の thinking レベルを扱うため、旧flat Runner の `measurement.think` は boolean または `low` / `medium` / `high` とする。manifest の任意文字列 `runner` / `format`、blob の任意文字列 `from` を定義する。配布元の `model_config` は GPT-OSS の形式も許容し、architecture・os・rootfs 等がない場合に架空の値を補完しない。既存の厳密な Runner 型から変更するため schema の MAJOR を 2 に上げる。1.0.0 のスキーマは保存し、旧結果は旧スキーマで検証する。

新しい反復の `isolation` は `model_manifest_sha256`、`quantization`、`context_length` を必須とし、実際のモデル配置情報から取得する。metrics に `thinking_sha256`（推論過程の文字列ハッシュ）と `first_generated_chunk_seconds`（thinking または response の最初の非空チャンクまで）を追加する。既存の TTFT は response の最初の非空チャンクまでで、生成上限まで thinking のみだった場合は null。response_sha256 は従来どおり最終回答文字列だけのハッシュとする。

生成 Token/s は API の eval_count（thinking を含む生成トークン）/経過秒を使用する。thinking と回答のトークン数を API が分離しない場合、独自の文字数推定で内訳を作らない。think=false で thinking が返ったら失敗とする。メモリの事前判定値は Runner に置く保守的な運用下限であり、実測した最小必要量ではない。

### 完全スキーマとサンプルの再生成

配布用 Requirments.md に埋め込まれた specs の Schema ブロックを抽出する。外部 `schemas/` が存在しない状態でも復元できる。説明用の古い抜粋 JSON は基準にしない。テスト用の完全サンプルはこのスキーマに従って生成し、合成 fixture であることをテスト名・保存先で明記する。実測例は実際の run からのみ作成する。

JSON Schema だけで扱えない、CPU ID の数・集合・参照、比率の丸め、Token/s・集計・費用時間の式、状態・実測証跡を意味検証する。旧1.0.0/2.0.0/3.0.0/3.1.0は各compat Schema、現行3.2.0は現行 Schema で検証する。検証器が未知のバージョンを推測で受け付けないようにする。

### 共通 perf プロファイル（x86_64 / ARM64）

両アーキテクチャの本番 Ubuntu 26.04、および実験用 WSL2 / Ubuntu 24.04 で標準の `perf stat` を使用し、定常推論の測定区間に合わせて vCPU 別のカウンタを取得する。共通取得は標準で有効とし、ARM64 専用の Performix 詳細解析とは独立させる。ここでいうプロファイルはカウンタの定期取得であり、スタックサンプリングではない。

`perf stat` の `-a -A -C <CPU_LIST>` で選択 CPU を CPU 別に計測し、`-I 1000` による 1 秒間隔を初期値とする。対応を検証した JSON または区切り文字形式の出力を正規化する。取得開始・終了を推論測定区間と同期し、最後の 1 秒未満の区間も実測時間とともに保存する。オプションの仕様は [perf stat マニュアル](https://man7.org/linux/man-pages/man1/perf-stat.1.html) を参照。

この取得方式は **選択 CPU 上のシステム全体**を対象とし、他プロセスやカーネル処理も含む。`scope: system_wide_selected_cpus` と明記し、推論プロセスのみの値とは解釈しない。選択されていない vCPU は CPU 一覧で識別し、未測定をゼロと扱わない。

| 区分 | perf イベント / 指標 | 扱い |
| --- | --- | --- |
| 共通ソフトウェアイベント | `cpu-clock`, `context-switches`, `cpu-migrations`, `page-faults` | 両アーキテクチャで取得を試み、利用可否を記録 |
| 基本ハードウェアイベント | `cycles`, `instructions` | PMU が利用可能な場合に取得 |
| 追加ハードウェアイベント | `branches`, `branch-misses`, `cache-references`, `cache-misses` | 対応する場合に取得し、CPU / PMU による意味の違いを明記 |
| 派生指標 | IPC、分岐ミス率、キャッシュミス率 | 有効な同一区間のカウンタから計算。欠測・分母ゼロ時は `null` |

汎用イベント名があっても、AWS の PMU 公開状況、カーネル、権限、CPU によって取得できるとは限らない。`perf list` と短い実測で事前検証する。未対応イベントの失敗で取得可能なイベントまで失われないよう、イベント集合を構成する。アーキテクチャ固有の raw イベントを共通必須項目にしない。

各反復の `scaling.results[].repetitions[].profiling.perf` に以下を保存する。共通の perf バージョン・カーネル・PMU 定義は上位から参照し、以下の実行時情報を記録する。

- `status`、欠測理由、実効権限設定、計測範囲、実行オプション、実測区間。共通設定と異なる実効値があれば記録する。
- `per_vcpu[]`：`cpu_id`、イベント別の値・単位・状態・理由、派生指標。コア・ソケット・NUMA は共通の CPU トポロジーを `cpu_id` で参照する。
- イベントの計測稼働時間と稼働率（`time_running` / `time_enabled` 相当）、perf による多重化補正の有無。取得不能なメタデータも `null` と理由を残す。
- 時系列の生データ参照。1 秒ごとの値は生データとして保存し、`summary.json` には vCPU 別の測定区間合計を格納する。区間差分を合計し、終了時総計と二重加算しない。

イベントの状態は Schema の `ok` / `unavailable` / `not_implemented` / `not_applicable` / `disabled` / `error` に正規化する。unsupported / permission_denied / not_counted は unavailable の reason に区別して記録し、欠測値は `null` とする。取得失敗はプロファイルの不完全状態として残し、推論の成功・失敗と分ける。

IPC は `instructions / cycles`、ミス率は対応するミス数 / 参照数で算出し、区間比率の単純平均を避ける。比率に用いるイベントは可能なら同一グループで取得し、多重化の稼働率を比較品質の判断材料として保存する。キャッシュ指標などは同名でも CPU 間で意味が異なるため、無条件に同等とは扱わない。`cpu-clock` 単独を推論 CPU 使用率や物理 CPU 周波数に読み替えない。

反復ごとの vCPU 情報を保持し、異なる vCPU 数・反復のカウンタを無条件に合算しない。全スケーリング条件で perf 設定をそろえ、perf 無効の追加測定を行う場合は別条件として保存する。


## 現行3.2.0の正規定義

この契約の正本は `specs/summary.schema.json`。既存実行器の `schemas/summary.schema.json`（2.0.0）とは区別する。3.2.0 は今後本書から生成する実行器の対象であり、既存実行器が既に対応したとは扱わない。

- `workload.runner_config` は `specs/runner.schema.json` の **instance**。template は保存できない。
- `workload.runner_sha256` は具体化した Runner 全体の canonical JSON（sort_keys=True, separators=(',', ':'), ensure_ascii=True）の SHA-256。
- `workload.prompt_sha256` は `runner_config.workload.prompt` の UTF-8 バイト列の SHA-256。
- `artifacts.dashboard` は value が相対パス文字列または null、unit は path。ok の場合は非空文字列と reason=null、それ以外は value=null と非空 reason。
- `schema_version` は文字列3.2.0。旧結果は `specs/compat/summary-2.0.schema.json` と `summary-1.0.schema.json` で検証し、元の結果を書き換えない。
- 性能値・単位・状態値は既存2.0.0の意味を維持する。thinking と回答を混ぜてハッシュ化しない。コンテキスト長は Runner の workload.context_length と照合する。

## 必須の意味検証

1. template の混入、未束縛値、Runner snapshot のハッシュ不一致を拒否する。
2. 要求比率の網羅、丸め後 CPU 数、CPU ID の一意性・利用可能集合・包含関係、条件/反復 ID の一意性を検証する。
3. 成功反復には時刻、生成トークン、CPU-only、モデルdigest・量子化・実効context、キャッシュ検証、コンテナ削除証跡が必要。
4. Token/s=生成数/実測秒、集計=成功反復の中央値、speedup と parallel_efficiency、費用時間の分解を再計算する。浮動小数点の照合は rel_tol=1e-7 / abs_tol=1e-7、NaN・Infinity は拒否する。
5. perf の各 CPU と要求イベントを照合する。欠測・未実装をゼロと解釈しない。IPC は同一区間の instructions/cycles から算出する。
6. Native の料金は null/not_applicable。AWS の価格項目追加は別契約変更として行い、現行の最小形式で本番課金を実装したとは扱わない。
7. run 成功は全条件成功・終了コード0・errors空・JSON検証成功を必要とする。report のみ失敗した場合は推論結果を維持して run=partial、終了コード50とする。

契約変更は本書と Schema を先に更新し、版を決め、fixture・検証器・実行器・表示器の順に追従する。Schema が受理するだけでは意味検証合格とはしない。

新規3.0.0のperfには collection_started_at / collection_ended_at（UTC文字列またはnull）、collection_duration_seconds（非負数またはnull）を記録する。実カウンタが取得できた場合は実際の正の計測秒を必須とし、イベント率の分母に用いる。環境欠測ではnullを許容する。

## 3.1.0 の互換追加と監査

Runner snapshot の任意 `workload.template_date` を許容する。固定日付・全ワークロード値（seed、温度、生成上限、batch、context、thinking等）を比較条件に含める。既存3.0.0は `compat/summary-3.0.schema.json` で検証し、保存結果は変更しない。現行と旧3.0.0の共通項目は同じ意味検証を行う。1.0.0/2.0.0は各Schemaと、その版で存在する計算・CPU・キャッシュ項目の意味検証を行い、存在しない新項目を捏造しない。

validation.json は最終 summary のバイトハッシュに対応させる。HTMLの出典に保存する入力ハッシュも同じ最終版と一致させる。表示の再生成だけでは元の summary を変更しない。

### Dashboard 表示検査

単一HTMLを外部ネットワークなしの実ブラウザで読み、表・SVG・フィルタが描画されることを確認する。比較キーの完全なJSONは詳細表示へ置き、選択肢のラベルは短くして横幅を破綻させない。全件欠測時はグラフ内に理由を表示し、ゼロの性能点を生成しない。秒と時分秒を併記する。

## 3.2.0 の互換追加：性能のばらつき

現行生成版は3.2.0。3.1.0はcompat Schemaで保存・検証する。`scaling.results[].metrics.quality` を任意フィールドとして追加し、3.2.0生成器はmetricsが存在する条件で必ず保存する。旧結果にない値をDashboardが推測計算しない。

qualityは `policy: quality/v1`、`status: insufficient_samples|within_threshold|outside_threshold`、`sample_count`、`minimum_samples: 5`、`relative_spread_limit: 0.20`、`minimum_tokens_per_second`、`maximum_tokens_per_second`、`relative_spread` を持つ。単位は最小/最大値がtokens/s、相対幅は無次元。中央値は既存metricsの値を使用する。計算と判定はmeasurement-protocolを正本とし、意味検証器で再計算する。

推論のsuccessと品質判定を別表示する。品質フィールドがない旧結果は「未評価」と表示し、推論successを性能安定の証明と扱わない。
