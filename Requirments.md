# llm_on_cpu 再生成仕様書

仕様整理日：2026-10-18（JST）。ファイル名は既存の `Requirments.md` を維持する。

## 1. この文書の目的と再生成の意味

**`Requirments.md` と `specs/` 一式を渡せば、実行スクリプト、Runner、JSON Schema、README、結果表示機能を生成し、実行・検証まで進められる状態を目指す。** 過去の会話や既存実装を必須入力にしない。本書は全体要件、独立した仕様・固定データは [specs/README.md](specs/README.md) を入口とする。本書単独では再生成入力が揃わない。

再生成とは、同じデータ契約・固定配布物・測定手順・失敗処理で動く機能的に同等の環境を構築すること。生成されるソースコードのバイト一致、異なるホスト間の性能値一致、LLM 出力のビット一致を保証する意味ではない。固定イメージ・モデル・依存パッケージの取得にはネットワークと外部配布元が必要である。

- 本文：生成する機能・手順・意味検証・表示・受入条件の基準。
- `specs/` の Schema：フィールド名・型・必須性・enum・null・互換性の基準。
- `specs/runners/` の Runner：モデル、バージョン、量子化、コンテキスト長、プロンプト等の具体値の基準。
- 生成後の実行ファイル：本書と `specs/` から作る成果物。本書の不足を既存実装から暗黙に補完しない。
- README：生成・検証した機能の使い方と実装状況。要件書や Runner を逆に規定する文書にしない。

本文と固定データが矛盾したら、その箇所を報告して本書を先に修正する。既存コードの挙動を無条件に正解として採用しない。新しい版への更新は`specs/` の固定データ更新と再検証を経て行い、再生成時に「最新」を再選定しない。

## 2. 生成範囲と実装段階

最終目標は AWS / Native、x86_64 / ARM64、Ollama / vLLM、共通結果表示、ARM64 詳細解析を含む全体である。これと最小構成を区別する。

| 段階 | 生成・検証対象 | 本書と specs/ での確定状況 |
| --- | --- | --- |
| A：最小の推論実行 | Native / experimental / x86_64、Ollama、Docker、全スケーリング、JSON 生成・検証 | 固定データを収録済み。実行先のメモリ・権限・ネットワークは実測検証 |
| B：最小の再生成一式 | A に README 生成、端末表示、オフライン HTML Dashboard を加える | 今回の再生成の既定目標。表示仕様・CLI・受入条件を本書で固定。現在の既存実装には未実装部分がある |
| C：本番比較 | AWS / production、ARM64、正式対象モデルの実測、メモリ帯域、課金 | 本文の目標仕様を維持。後述の未確定事項と配布物の固定が必要 |
| D：追加 Framework・解析 | vLLM、Performix → Grafana | 製品・バージョン・運用条件の追加決定が必要 |

「再生成する」だけの指示では B を対象とし、C/D を勝手に完了済みにしない。対象一覧で正式比較用に指定したモデルの Runner も生成するが、メモリ不足時の自動代替はしない。既定の小型 Runner によるスモーク成功と、正式対象の成功は別の検証結果として報告する。

2026-10-17 時点の既存実装は A の小型 Runner を実機検証済み、正式対象 Runner は固定・構文検証済み、大型推論・B の表示と README 自動生成・C/D は未完了。この情報は現状説明であり、再生成した成果物の検証証跡として流用しない。

## 3. 再生成時の入力・出力・実行入口

### 必須入力と外部前提

必須の設計入力は本書と `specs/` 一式。実行時入力は生成先ディレクトリ、Runner 選択、provider、profile、結果の保存先。既定は `~/work/llm_on_cpu`、[モデル一覧](specs/model-catalog.md) で指定する既定 Runner、`native`、`experimental`、プロジェクト配下 `results/` とする。

実行前に Ubuntu/WSL2、Python、Docker Engine、利用可能 CPU・メモリ・ディスク、ネットワーク、perf を検査する。WSL の `.wslconfig` 変更、Windows/WSL 再起動、ホストのメモリ増設、AWS アカウント・課金リソース作成は本書の生成処理に含めない。実行先の値をこの文書の過去の測定値から決め打ちしない。

初期ホスト Python は 3.12 以上で、Linux の venv・monotonic clock・SIGALRM が利用可能なこと。依存関係は`specs/bootstrap/requirements.lock` から導入し、導入に失敗したらバージョンを黙って緩めない。Docker Engine は CPU 制限・read-only bind mount・tmpfs を備え、収集処理と同じ Linux ホストで動くものを使用する。ホストツールの実際のバージョンを記録する。

オフライン再生成を必須とはしない。完全オフライン運用には Docker ベースイメージ、Framework archive、モデル全 blob、Python wheel 一式を別途保存する必要があり、Markdown だけでは代用できない。固定 digest が配布元から取得できなくなった場合は停止し、不足する配布物を報告する。

### 生成する成果物

| 成果物 | 生成要件 |
| --- | --- |
| `llmbench/` | Python パッケージと CLI。Host/Provider、Runtime、モデル Adapter、計測、集計、検証、表示を分離 |
| `runners/*.json` | `specs/runners/*.json` の全汎用 instance を `runners/` に配置する。件数やモデル名を実装に固定しない。モデル追加時は既存 Adapter で扱える限り設定追加だけで対応 |
| `schemas/*.json` | 現行 summary 3.2.0、旧3.1.0/3.0.0/2.0.0/1.0.0、汎用Runnerの完全スキーマをspecsから配置 |
| `docker/Dockerfile`、`.dockerignore` | 固定 Ubuntu ベースと CPU ランタイム。機密・結果・モデルをビルドコンテキストに入れない |
| `scripts/setup.sh` | venv・固定依存導入、前提確認。ホスト権限の不足を報告し、黙って変更しない |
| `scripts/generate_readme.py` | 下記の README 生成規則から実装状況に合う文書を生成 |
| `requirements.lock` | `specs/bootstrap/requirements.lock` をそのまま配置 |
| `tests/` | スキーマ・意味検証・異常系・表示・隔離のテスト。合成データと実測を明確に分離 |
| `README.md` | 実装済み機能、導入、CLI、生成物、失敗時の確認方法、制限 |
| `results/<run_id>/` | 実際に実行した場合だけ生成する summary・検証結果・ログ・生データ |
| `dashboards/<report_id>/index.html` | summary のみから作る結果表示。推論を再実行しなくても生成可能 |

モジュール分割・内部関数名は生成者が選べるが、外部 CLI とデータ契約を変えない。空ディレクトリやスタブを置いただけでは実装済みと扱わない。

### CLI 契約

```bash
python -m llmbench doctor --provider native --profile experimental
python -m llmbench run --runner runners/ollama-qwen3-smoke.json --provider native --profile experimental
python -m llmbench validate results/<run_id>/summary.json
python -m llmbench report results/<run_id>/summary.json --output dashboards/<report_id>/index.html
python -m llmbench report results/<run_a>/summary.json results/<run_b>/summary.json --output dashboards/comparison/index.html
python scripts/generate_readme.py
python -m unittest discover -s tests -v
```

- `doctor`：環境と選択可能な Runner の検査。必須不足と perf 等の欠測を分ける。モデルのダウンロードや推論は行わない。
- `run`：前提検査、固定配布物の準備、計測、JSON 検証、端末表示、HTML 生成を順に行う。段階 B では HTML 生成までを完了条件とする。
- `validate`：ホスト・ネットワーク不要で JSON の構造と意味を検証する。不適合は終了コード40。
- `report`：指定した summary だけを読み、端末の一覧と HTML を生成する。価格取得・生データ読込・モデル実行はしない。
- 実装段階で未対応の provider/profile は明示的に拒否する。入力不正2、前提不成立10、表示対象 JSON 不正40、HTML 保存失敗50を用いる。

### 生成・検証の順序

1. `python3 specs/check_inputs.py` で入力一式のハッシュ・JSON構文を検証し、JSON Schema 自身の妥当性と Runner 適合性を別途検証する。
2. [specs/README.md](specs/README.md) の配置表に従い、現行/旧スキーマ、Runner、Dockerfile、依存 lock を配置する。
3. 汎用instanceを生成し、CLI・前提検査・実行・収集・集計・検証・表示を生成し、ネットワーク不要のテストを実行する。
4. README 生成器を作り、実装済み範囲とテスト結果から README を生成する。
5. 実行環境で `doctor`、固定配布物のビルド・取得、小型 Runner の実推論を行う。必要な資源がなければ未検証として報告する。
6. 生成 summary を独立した `validate` で検証し、オフラインで `report` を再実行する。
7. 正式対象は資源条件を満たす場合に同じ手順で検証する。大型モデルを試していない場合はその旨を残す。
8. 最後に README の検証済み範囲を更新し、未完了機能と失敗原因を報告する。

生成先に既存ファイルがある場合は差分を確認して更新し、既存 results・ユーザー設定・キャッシュを一括削除しない。受入試験では本書と `specs/` だけを空ディレクトリへコピーして生成できることも確認する。

## 目的と範囲

- CPU アーキテクチャ、インスタンスタイプ、Framework、モデルごとの推論性能を比較する。
- OS とツールチェーンのバージョンを統一し、実行条件と結果を再現可能な形で保存する。
- 各インスタンスで共通形式の `summary.json` を生成し、横断的な集計・比較を可能にする。
- 共通の環境構築処理を変更せず、Runner の追加によって新しいモデルを測定対象にできるようにする。
- ARM64 では任意で詳細プロファイルを取得し、Performix CLI → Grafana による可視化手段を提供する。

初期スコープは単一ホスト内の推論とする。GPU 推論、モデルの学習・ファインチューニング、複数インスタンスにまたがる分散推論は初期スコープに含めない。

## 対象環境

| 項目 | 要件 |
| --- | --- |
| 実行基盤 | AWS インスタンス / Native（本プロジェクトをインストールした既存 Ubuntu ホスト） |
| 環境選択 | `environment.provider: native` または `aws`。既定値は `native` |
| 推論実行方式 | 両環境で共通の Docker コンテナ |
| CPU アーキテクチャ | x86_64、ARM64 |
| 本番ホスト OS | Ubuntu 26.04 に固定 |
| 実験ホスト OS | WSL2 上の Ubuntu 24.04 を許容 |
| コンテナ OS | 本番・実験とも Ubuntu 26.04 に統一 |
| 演算デバイス | CPU のみ |
| ツールチェーン | GCC などのバージョンを各インスタンスで統一 |
| 結果 | 共通スキーマの `summary.json` と実行ログ |
| 詳細解析 | ARM64 向けの任意機能として Performix CLI → Grafana を提供 |

段階 C の対象インスタンスタイプ、リージョン、AMI、ストレージ条件は未確定事項として管理する。アーキテクチャ別の AMI ID に加え、OS イメージのリリース、カーネル、CPU 情報、vCPU 数、メモリ容量を結果に記録する。

### 本番・実験の運用区分

本番は Ubuntu 26.04 のインスタンスを使用し、実験は現在の WSL2 / Ubuntu 24.04 / 16 vCPU / 約 15 GiB メモリのホストを使用する。コンテナのユーザー空間はどちらも Ubuntu 26.04 とし、共通 Dockerfile と固定依存関係を使用する。同一 Framework・アーキテクチャでは同じイメージを利用する。

コンテナは Docker Engine 側のカーネルを共有するため、ホストとコンテナの Ubuntu バージョンを同じにする必要はない。ただし、実験では WSL2 カーネル、本番では本番ホストのカーネルを使用し、カーネル・PMU・性能条件まで同一になるわけではない。[Docker containers](https://www.docker.com/resources/what-container/)、[WSL バージョンの比較](https://learn.microsoft.com/en-us/windows/wsl/compare-versions)

- `production` は本番性能評価、`experimental` は実行経路・CPU 制限・キャッシュ分離・JSON 生成と検証の確認に使用する。Provider とは独立した区分とし、WSL の Provider は `native` とする。
- 実験ではホスト Ubuntu 24.04 を許容するが、コンテナ Ubuntu 26.04 の要件は緩めない。本番ではホスト Ubuntu 26.04 を必須にする。
- WSL の CPU・メモリは実行時に再検出する。16 vCPU の場合は 4・8・12・16 vCPU で測定する。メモリ不足時に初期モデルの成功を保証せず、モデルの必要量と利用可能量を事前検証する。動作確認用の小型モデルを使う場合は別設定・別モデルとして記録し、正式対象を黙って置き換えない。
- perf は実際の Docker 実行ホストのカーネルに対応させる。WSL で取得不能なイベントは `null` と理由を保存し、利用可能なイベントで検証する。perf の欠測を推論失敗と混同しない。
- 最小実装では WSL ディストリビューション内の Docker Engine を使用し、CPU トポロジー検出・cpuset・ホスト perf が同じ Linux 環境を対象とする。Docker Desktop 等の別 VM・リモート Engine は実行ホストとの対応を検証するまで対象外とする。
- 実験結果を本番の性能比較に混ぜない。コンテナの起動互換性とモデル実行可否は実際のビルド・実行で確認する。

### バージョンと実行条件の統一

- GCC / G++、ビルドツール、Python、主要依存ライブラリなどのバージョンを共通の設定で管理する。
- Framework のバージョンと、ソースビルド時のリビジョン・コンパイラ・ビルドフラグを記録する。
- アーキテクチャ固有の最適化や依存関係の差異は明示し、比較時に確認できるようにする。
- CPU スレッド数、CPU affinity、NUMA 設定、同時実行数など、性能に影響する設定を記録する。
- 実行前に CPU バックエンドを検証する。必要な組み合わせが利用できない場合は、条件を黙って変更せず、未対応または実行失敗として記録する。

Ubuntu 26.04 と各 Framework・ツールチェーンの組み合わせについては、実装開始時に対応状況を検証し、採用バージョンを固定する。

## Framework とモデル選択

| 実行ストリーム | 優先順位 | 方針 |
| --- | --- | --- |
| Ollama | 最優先 | CPU 向けモデル運用の選択肢を重視し、最初の実行・比較基盤を構築する |
| vLLM | 次段階 | 共通の測定・結果形式を利用し、CPU 実行に必要な環境と Runner を追加する |

対象モデル、用途、既定 Runner、モデル追加手順は [specs/model-catalog.md](specs/model-catalog.md) に集約する。固定値の正本は `specs/runners/<runner_id>.json` とし、本書や README に複製しない。

モデル名だけで同一条件とは判断しない。配布元、モデル識別子、タグまたはリビジョン、重み形式、量子化方式、コンテキスト長を固定・記録する。各 Framework と CPU アーキテクチャでの実行可否や必要メモリは事前検証事項とし、全組み合わせでの動作を前提にしない。

## 全体構成

処理を「環境構築」「Runner」「共通測定・集計・perf 取得」「任意の詳細プロファイル」に分離する。

```text
実行設定（Provider / Framework / モデル / ワークロード / CPU 設定）
  ├─ Provider：Native / AWS 固有の検証・メタデータ
  ├─ 共通 Host 情報：OS・CPU・NUMA・メモリ・perf 対応状況
  ├─ 環境構築スクリプト：ホスト依存パッケージ・Docker・イメージビルド
  └─ 共通実行制御
       ├─ Runtime（Docker）：CPU 制限・コンテナ新設・破棄・書き込み領域管理
       ├─ Runner：モデル取得・起動設定・正常性確認・キャッシュ制御
       ├─ 共通測定：vCPU スケーリング・ウォームアップ・負荷生成・perf 取得・繰り返し測定
       ├─ 結果集計：summary.json・生データ・ログ
       └─ ARM64 任意機能：Performix CLI → Grafana
```

### Native / AWS を切り替える境界

Native は「本プロジェクトをインストールした既存 Ubuntu ホスト（本番は 26.04、実験用 WSL2 は 24.04）で、AWS に依存せず実行できる」ことを意味する。Docker を使わないホスト直接推論を意味するものではない。x86_64 / ARM64 の両方で、既に採用した Docker・CPU スケーリング・キャッシュ分離・perf・結果形式を共通利用する。

環境差分を **Provider**、コンテナ操作を **Runtime**、モデル差分を **Runner** に分ける。Framework × モデル × Provider ごとに Runner を複製しない。

| 層 | 責務 | 依存の制約 |
| --- | --- | --- |
| 共通 Host 検出 | OS、アーキテクチャ、利用可能 CPU、NUMA、メモリ、Docker・perf の利用可否 | AWS API・メタデータサービスに依存しない |
| Native Provider | 既存ホストの識別と環境設定。共通 Host 情報を利用 | AWS CLI / SDK・認証情報を要求せず、クラウドの検出通信をしない |
| AWS Provider | AWS 固有メタデータの取得・検証 | AWS 依存はこの層に閉じ込め、明示選択時のみロードする |
| Docker Runtime | イメージ準備、新規コンテナ作成、cpuset、mount、停止・削除 | Provider によらず同じ処理を使う |
| Runner | モデル準備、起動パラメータ、正常性確認、キャッシュ制御 | ホスト種別を分岐条件にしない。コンテナ操作は Runtime に委譲する |
| 共通実行・集計 | 4 段階のスケーリング、反復、perf、summary.json | 正規化された Host 情報・Provider 情報のみを参照する |
| Provisioning | AWS インスタンス・関連リソースの作成など | 任意の前処理。既存ホストでの測定に必要としない |

Provider の共通インターフェースは `validate_environment` と `collect_metadata` を基本とし、共通形式の情報と取得状態を返す。CPU 選択や perf イベント可否は Provider 名で決めず、実機の能力を検出する。Native の物理マシン・VM のどちらでも、検出した論理 CPU と既存制限を基準にする。

設定例（設計案）：

```yaml
environment:
  provider: native  # AWS で測定するときは aws に変更
runtime:
  type: docker
```

設定ファイルと CLI の `--provider native|aws` で明示的に選択できる設計とし、CLI 指定を優先する。自動検出は行わず、未指定時は `native` とする。AWS 上でも Native モードでの実行を許容するが、その場合は AWS 固有情報を取得しない。無効な Provider 名はエラーにし、暗黙のフォールバックはしない。

AWS メタデータ取得にはタイムアウトを設定し、取得不能時は理由を保存する。測定に必要な CPU・メモリ等が共通検出で確認できれば、AWS メタデータの欠測だけで推論を中止しない。取得状態を明示し、Native の結果に架空のインスタンスタイプを設定しない。

### Native のインストール・実行要件

「インストール後にすぐ動作可能」は、AWS アカウント、クラウドリソース作成、環境別コード変更を要求せず、共通の実行入口からベンチマークを開始できることとする。初回の依存導入、イメージビルド、モデル取得の所要時間は含意しない。

- 共通セットアップで運用区分に応じたホスト OS・アーキテクチャ・必要メモリ・空き容量を検証し、Docker とホストカーネルに対応する perf を準備する。固定ツールチェーンと Framework は共通 Dockerfile で整備する。
- 検証コマンドを用意し、Docker 実行権限、cpuset、perf 権限・PMU、モデル準備状況を一覧化する。推論に必須の不足条件と、欠測として継続できる perf の制約を分ける。
- Native の標準インストールでは AWS CLI / SDK を必須依存にしない。AWS のリソース作成や認証を伴う機能に必要な依存だけを追加導入可能にする。
- 共通実行入口が初回のイメージ・モデル準備を行い、以後は固定イメージとモデル配布物を再利用する。各条件・各反復の新規コンテナ作成は維持する。
- Runner の選択、CPU スケーリング、キャッシュ分離、perf 取得、summary.json 生成まで同じ処理を通し、Provider 設定だけで環境を切り替えられるようにする。

実行コマンドと Python パッケージ方式は冒頭の CLI 契約に従う。既存コードの有無に依存せず、必要な入口を生成する。

### 環境構築スクリプト

- OS とアーキテクチャを検出し、固定したバージョンの依存関係を導入する。
- 共通環境と Framework 固有の環境を分離し、モデル名による分岐を持たせない。
- 再実行可能にし、既存環境のバージョン不一致を検出する。
- インストールと環境検証を担当し、ベンチマークの負荷生成や結果集計は行わない。

### Runner と拡張方式

Runner は Framework とモデルの組み合わせに必要なデプロイ設定・処理をカプセル化する。Framework ごとの共通処理は再利用し、モデル固有の識別子や起動設定は各 Runner 内に閉じ込める。

共通インターフェース案：

| 操作 | 責務 |
| --- | --- |
| `validate` | モデル、アーキテクチャ、メモリ、必要な機能の検証 |
| `prepare` | モデルの取得・配置とモデル固有の準備 |
| `start` | CPU 推論サービスの起動 |
| `healthcheck` | 推論リクエストを受け付けられることの確認 |
| `describe` | 実際のモデル・Framework・起動条件を共通形式で返す |
| `stop` | サービス停止とリソース解放 |

Runner は一意の ID で選択でき、配置した Runner を自動検出する設計とする。既存 Framework に新しいモデルを追加する場合は、Runner パッケージの追加のみで対応し、共通の環境構築・実行制御・集計コードの変更を不要にする。新規 Framework や新たなシステム依存関係への対応は、別途基盤拡張として扱う。

### ディレクトリと責務

生成する物理パスは冒頭の成果物表に従う。`llmbench/` 内で Host、Provider、Docker Runtime、Framework Adapter、計測、検証、レポートを分ける。Runner の固定設定は `runners/` に置く。AWS リソース作成は段階 C の任意 provisioning として切り離し、既存ホストでの推論実行に必須としない。

## Small start の確定範囲と実行契約

初回は Native / experimental / WSL2 / x86_64、Ollama、メモリに収まる動作確認用モデル 1 種、4 段階スケーリング、実推論、summary.json の生成・構造検証・意味検証までを実装する。AWS、ARM64 実機検証、vLLM、Dashboard、Performix はこの段階の完了条件から分離する。未対応 Provider・アーキテクチャ・本番指定は明示的に拒否し、実装済みと表示しない。

### Runner が管理する固定設定

Framework の正式リリース、配布物チェックサム、Ubuntu ベースイメージ digest、モデルタグと manifest/blob digest、量子化、測定プロンプト、生成上限、seed、温度、コンテキスト長、同時実行数、反復数、タイムアウトは `runners/<runner_id>.json` に固定する。README に値を複製しない。実行時にタグを最新へ追従せず、内容が固定値と異なる配布物は拒否する。実行時の Runner 全体と、キー順をソートし空白を除いた canonical JSON の SHA-256 を summary に保存する。Runner の型・必須項目は `schemas/runner.schema.json` で検証する。

新しい仕様版を作る際は最新正式リリースを選定の出発点とし、実際のスモークテストを採用条件とする。未検証の「最も安定した版」とは断定しない。バージョン更新は Runner の固定値変更と再検証を必要とする。

### 初回の測定方法

specs/measurement-protocol.md の fresh_request_preloaded/v1 に従う。前提条件検証でrun開始前に拒否する場合は終了コードと標準エラーを返し、run ID発行後は失敗結果もsummaryへ保存する。

### タイムアウト・後始末・終了コード

タイムアウトは共通準備（イメージ準備＋モデル準備）に合計3600秒、各条件の各反復にそれぞれ3600秒とする。各反復では起動・ロード・推論を含む全体に同じ締切を適用し、ストリームの各チャンクで時間枠をリセットしない。run 全体は反復数に応じて 1 時間を超え得る。タイムアウト後の後始末には別途最大60秒の猶予を設ける。

条件内の失敗は summary に保存し、後始末が成功すれば次の条件へ進む。共通準備の失敗、整合性違反、後始末失敗は以後の実行を止める。中断時も可能な限り summary とログを保存し、run が所有するコンテナだけを削除する。

| 終了コード | 意味 |
| --- | --- |
| 0 | 全条件の推論成功、JSON 構造・意味検証成功。perf の環境欠測は許容 |
| 2 | CLI・Runner 設定不正 |
| 10 | OS・アーキテクチャ・Docker・メモリ等の前提条件不成立 |
| 20 | イメージ・モデル準備失敗、固定配布物の不一致 |
| 30 | 推論・API・CPU 実行確認失敗 |
| 31 | 1 時間のタイムアウト |
| 32 | キャッシュ分離契約の検証失敗 |
| 40 | JSON Schema または意味検証の失敗 |
| 50 | 出力保存・後始末・予期しない内部エラー |
| 130 | ユーザー中断 |

run に複数の失敗がある場合は `130 > 50 > 40 > 31 > 32 > 30 > 20 > 10 > 2` の優先順で終了コードを選び、個々の原因は `run.errors[]` に残す。perf 権限不足・カウンタ未提供は終了コードを悪化させない。

## 測定・集計の参照規則

測定方法の正本は specs/measurement-protocol.md。Runnerはプロトコルを選択し、許可されたパラメータだけを具体化する。CPU比率、計測境界、Token/sの式、欠測処理、キャッシュ確認をAdapterごとに変更しない。

## Ollama Adapter と Docker Runtime の生成仕様

1. Runner は `specs/runner.schema.json` で検証し、欠落キー・未知キー・不正な値を拒否する。全 Runner を列挙できるようにし、既定選択はモデル一覧の指定に従う。
2. ベースイメージ digest、Framework archive SHA-256 を検証する。archive は安全な展開パスを検証し、`bin/` と CPU 用 `lib/ollama/` を配置する。CUDA/ROCm/Vulkan ライブラリを使わない。イメージの再利用キーは Framework 配布物・アーキテクチャ・ベースイメージ・Dockerfile のハッシュから作り、モデルや CPU 数では変えない。
3. manifest URL を取得し生バイトの SHA-256 を固定値と照合する。config と各 layer の blob を digest で取得・検証し、モデルキャッシュを manifest digest 単位で保存する。途中ファイルは検証後に rename し、未検証ファイルを完成品として使わない。
4. 重み blob は read-only で共有する。Ollama が更新する manifest 管理情報は専用 tmpfs に配置してからサービスを起動し、ホーム・一時領域もコンテナごとに新設する。ルートファイルシステムは read-only にする。Ollama は並列1、同時常駐モデル1、クラウド無効、GPU 無効で起動する。
5. コンテナは run 所有ラベル、一意名、cpuset を持ち、API はループバックの動的ポートへ公開する。Docker info とホスト検出が同じ実行ホストを示すことを検証する。子ワーカーにも CPU 制限が継承されることを確認する。
6. `GET /api/version` で起動と固定版を確認。コンテナ内 `/etc/os-release` で Ubuntu 26.04 を確認。`POST /api/show` の thinking.values で対応値を確認し、named level が未検証なら停止する。specs/ollama-adapter.md のテンプレート日付固定を適用する。
7. `POST /api/generate` に model、空 prompt、stream=false、keep_alive=-1 と Runner の options を渡してロードする。options は seed、num_ctx、num_predict、temperature、num_batch、num_thread=選択 CPU 数、num_gpu=0。ロード応答に生成トークン・thinking・response がないことを確認する。
8. `GET /api/ps` で常駐モデル1、size_vram=0、manifest digest、quantization_level、context_length を検証する。一致した実測値を isolation に保存する。
9. 計測を開始し、同じ options、固定 prompt、think、shift=false、stream=true を持つ生成リクエストを1回送る。NDJSON を逐次保存し、API error・終了応答欠落・生成数ゼロは失敗とする。時刻には UTC、経過時間には monotonic clock を使う。
10. thinking と response を別々に連結して SHA-256 を保存する。Ollama の eval_count、prompt_eval_count、eval_duration、done_reason を用い、thinking を回答文字列に混ぜない。
11. コンテナログを保存し、`cached n_tokens = 0` と `n_threads = K` を確認する。期待する証跡がない場合は成功扱いにせず、互換性を調べてから仕様を更新する。所有ラベルを確認して停止・削除し、失敗しても無関係なコンテナを操作しない。
12. 反復を集計して summary を原子的に更新する。構造・意味検証後に report を呼び、表示失敗時は条件の推論結果を維持し、artifacts.dashboard を error、run を partial、exit_code=50 として原因を追記する。表示失敗と推論失敗を区別して報告する。ネットワーク再試行で測定リクエストを二重送信しない。

## 独立したデータ契約と実行契約（正本）

| 仕様 | 正本 | 役割 |
| --- | --- | --- |
| 結果形式 | [summary-format.md](specs/summary-format.md)、[summary.schema.json](specs/summary.schema.json) | フィールドの意味・型・欠測・集計・意味検証 |
| Runner | [runner-contract.md](specs/runner-contract.md)、[runner.schema.json](specs/runner.schema.json) | 対象非依存の設定構造とライフサイクル |
| Template | [runner.template.json](specs/runner.template.json) | 未束縛の雛形。実行禁止 |
| 測定方法 | [measurement-protocol.md](specs/measurement-protocol.md) | 計測区間・キャッシュ分離・集計規則 |
| 旧形式 | specs/compat/ | 既存実行器の2.0.0/1.0.0とflat Runnerの検証 |

生成AIはこれらの仕様を変更せずに実行器・検証器・表示器を実装する。未定義事項を独自解釈で補完してはならない。新たな方式が必要なら契約を先に更新し、版・テストを変更してから実装する。

現行の生成ターゲットは summary 3.2.0 + Runner設定1.1.0（runner/v1） + fresh_request_preloaded/v1。既存実行器は summary 2.0.0 とflat Runnerを使用しており、この文書整理では移行していない。生成ターゲットの機能を既に実装済みと記載しない。

## Dashboard の自動生成仕様

表示データの定義・集計式・費用計算は、specs/summary-format.mdに従う。本セクションは生成方法と表示形式のみを定義する。

Dashboard は本書および README.md とは別の静的 HTML として生成する。**入力データは各実行の `summary.json` のみ**とし、Dashboard 生成時に AWS API、価格サイト、ホスト情報、perf 生データ、外部設定ファイルから表示情報を補完しない。ファイル名は小文字の `summary.json` に統一する。

### 生成手段と出力

- `reporting/` に生成器を実装し、ベンチマーク終了時に summary の検証・保存後、自動で生成する。失敗・未対応の結果も表示対象とする。
- 過去の複数の `summary.json` を指定して横断 Dashboard を再生成できる入口も用意する。CLI は `python -m llmbench report` とする。
- 出力先は `dashboards/<report_id>/index.html` とする。CSS・JavaScript・表示用データを埋め込み、CDN・バックエンド・ネットワーク接続なしでブラウザから閲覧できる形式にする。
- 使用した run ID、schema version、入力 summary のハッシュ、生成器バージョンを表示する。同じ run ID の重複は二重集計せず、内容が異なれば衝突として報告する。
- 必須スキーマ不整合はファイル単位で報告する。未取得値は「N/A」と理由を表示し、0 や推測値で埋めない。旧スキーマは明示的に対応する項目だけ表示する。
- Dashboard は表示・フィルタ・並べ替えに専念する。Token/s、時間単価、費用などの正式な集計値は summary 生成時に確定して保存し、画面から追跡できるようにする。

### 表示フォーマット

Platform ごとの概要と、スケーリング結果の表・折れ線グラフを表示する。フィルタは運用区分（production / experimental）、Framework、モデル・リビジョン、量子化、ワークロード、同時実行数、測定モード、キャッシュ方針を対象とし、条件の異なる結果を同じ系列に混ぜない。

| 表示項目 | summary.json の参照先 | 表示仕様 |
| --- | --- | --- |
| Platform（インスタンス名） | `platform.name` | AWS はインスタンスタイプを基本名にし、必要なら表示ラベルを付与。Native は設定したホスト表示名 |
| 環境 | `environment.provider`, `environment.host_id`, `environment.aws` | Native / AWS、ホスト識別子、AWS の場合はリージョン等 |
| CPU name | `platform.cpu.name` | 検出した CPU モデル名 |
| CPU Clock | `platform.cpu.clock` | GHz 表示と、base / max / observed / published の種別・出典 |
| vCPU 数 | `platform.vcpu_count` | ホスト総論理 CPU 数。`scaling.plan.base_nproc` と `scaling.results[].resources.vcpu_count` も併記 |
| メモリサイズ | `platform.memory.capacity_bytes` | GiB 表示（bytes / 2^30） |
| メモリ帯域 | `platform.memory.bandwidth` | GB/s 表示（bytes/s / 10^9）、実測 / 公称の種別と測定条件 |
| vCPU 別スケーリング | `scaling.results[].resources`, `scaling.results[].metrics` | 比率、実使用 vCPU 数、生成 Token/s、反復数、状態 |
| perf 比較・詳細 | `scaling.results[].profiling.perf`, `scaling.results[].repetitions[].profiling.perf` | 条件別集計から反復別・CPU 別の実測値へ展開 |
| 時間利用料 | `pricing.total_hourly_rate` | インスタンス＋ストレージの合計、通貨/時。内訳も展開表示 |
| 実行時間 | `scaling.results[].cost.duration_seconds`, `cost.duration_seconds` | 各条件と実行全体を分離し、秒と時分秒を表示 |
| インスタンス利用料金 | `scaling.results[].cost.estimated_amount`, `cost.estimated_amount` | 時間利用料 × 対象時間。推定額と明記 |

結果表は「Platform / モデル・Framework / 比率 / 使用 vCPU / Token/s / 実行時間 / 時間利用料 / 推定利用料金」を基本列とし、Platform の CPU・メモリ詳細は概要欄にまとめる。グラフは横軸を実際の使用 vCPU 数、縦軸を生成 Token/s とする。失敗点は 0 Token/s として描画しない。

### 自動表示の具体的な規則

report の端末表は Platform、Framework、モデル、使用 vCPU、Token/s、実行時間、時間単価、推定料金、状態を表示する。小数の表示桁は Token/s・秒を3桁、料金を6桁とし、元データは丸め直さない。元の通貨を表示し、異なる通貨を合算しない。

HTML は UTF-8 の単一ファイルとし、CSS・JavaScript・SVG グラフを埋め込む。外部フォント・CDN・fetch を使わない。自由文字列は HTML エスケープし、埋込 JSON の `</script>` 等を安全に処理する。summary 内の文字列を HTML/JavaScript として実行しない。

系列の比較キーは provider/profile、Framework の版、モデル digest・量子化、context、prompt hash、thinking、template_date、seed・温度・生成上限・batchを含む全ワークロード、同時実行数、測定モード、キャッシュ方針。Platform は系列ラベルとして残す。同じ名称のモデルでも digest が異なれば別系列にする。全件欠測の場合も概要表と理由を表示する。

run の自動生成先は `dashboards/<run_id>/index.html`。表示成功後に dashboard の参照を summary に保存し、再検証する。検証結果ファイルの summary hash は最終保存版と一致させる。外部 report の再生成では元の summary を変更しない。生成器・入力ハッシュ等の出典情報は出力 HTML 内に置き、HTML 自身のハッシュを summary と相互参照させて循環を作らない。

## README.md の生成仕様

README は本書とは別に生成する。具体的なモデル版・量子化・測定数値は複製せず Runner へリンクする。生成器は機能と CLI の実装検査、および新しく実行したテスト・検証結果を使い、未実施の検証を成功と記載しない。

必須構成：目的と対応範囲、要件書へのリンク、ホスト前提と導入コマンド、doctor/run/validate/report、Runner 選択方法、結果ディレクトリとログ、終了コード、取得状態、キャッシュ測定の制限、実装済み/未実装/未検証の一覧、検証の実施日時と証跡。

README 生成自体はモデル取得・推論・クラウド操作を起動しない。数値設定は Runner から読むか参照先を示すだけとする。再生成で手書きのユーザー文書を消さないよう README を生成物と明記し、カスタム説明は別文書へ分離する。

## 受入条件と再生成監査

| 対象 | 合格条件 |
| --- | --- |
| 入力一式の独立性 | 本書と `specs/` だけを空ディレクトリへコピーし、既存コード・会話・外部設定を読まず必要成果物を生成できる |
| 固定データ | 入力マニフェストのハッシュ一致、全固定 Runner のスキーマ適合、重み・量子化・num_ctx が勝手に変更されない |
| 環境 | 不足メモリ・OS・Docker 不一致を測定前に検出し、WSL を自動再起動しない |
| 実測 | 全スケーリングの CPU 集合と反復数が正しく、新規コンテナ・CPU 実行・キャッシュ証跡を記録する |
| データ | 1 run の全条件を1 summaryに保存。Schema・意味検証と過去版検証が成功する |
| 失敗処理 | 権限不足perf、タイムアウト、中断、APIエラー、破損配布物、書込失敗、後始末失敗を試験し、誤って成功にしない |
| 表示 | ネットワーク遮断下でも summaryだけで表・HTMLを生成できる。成功・partial・失敗・全欠測・悪意ある文字列・旧版を検証する |
| README | 生成した CLI と記載が一致し、未実装/未検証が識別できる。モデル設定値が複製されていない |
| 後始末 | 自分が作ったコンテナだけを削除し、既存結果・キャッシュ・他サービスを破壊しない |

合成データの成功、WSL 小型モデルの成功、正式モデルの成功、AWS/ARM64の成功は別々に報告する。性能が vCPU 数に比例することや生成ハッシュが必ず一致することを合格条件にしない。

## ARM64 の詳細プロファイルと可視化

ARM64 の実行では、オプションで Performix CLI によるプロファイル取得と Grafana での可視化を利用できるようにする。

- 通常のベンチマークは共通 perf 取得のみで完結し、Performix を必須としない。
- Performix 付き測定は通常の共通 perf 測定と区別し、計測オーバーヘッドを含む結果として記録する。
- プロファイル成果物を実行 ID と関連付ける。
- Performix CLI の導入・取得手順と、Grafana で参照するまでの手順を提供する。

Performix CLI の対象製品・配布元・バージョン、必要権限、取得形式、Grafana 用のデータソース・保存先・取り込み方式は今後確認する。CLI から Grafana への直接連携を前提とせず、必要な中間処理を検証したうえで設計する。

## 未確定事項・追加で必要な情報

A/B の再生成を始めるためにユーザーが追加決定しなければならない事項はない。B は表示と README 自動生成を含む新たな生成目標であり、既存コードが既に満たすという意味ではない。

全体目標 C/D を確定するには次が必要。未確定項目を適当な実測値・価格・対応版で埋めない。

| 項目 | 不足情報 | 提案と再生成への影響 |
| --- | --- | --- |
| AWS 対象 | リージョン、インスタンスタイプ、AMI、EBS 種別・容量・IOPS・帯域、購入方式 | 既存インスタンスで実行する方式を先行。価格は取得日時付きの設定入力として固定可能にする |
| AWS 作成範囲 | 自動作成まで必要か、既存ホストのみか | 当面は既存ホスト。アカウント・IAM・ネットワーク・削除方針は自動作成を採用する時点で必要 |
| ARM64 の固定配布物 | 検証する実機、Framework archive/digest、依存差分 | x86_64 のバイナリを転用しない。検証後に`specs/` へ ARM64 Runner/runtime lock を追加 |
| メモリ帯域 | STREAM 等の測定ツール、版、read/copy/triad、配列サイズ、NUMA 方針 | 共通手法を1つ選び版・条件を固定する。決定までは not_implemented。ユーザーの既存測定標準があれば優先 |
| vLLM | CPU backend、版、ビルド条件、対応モデル形式 | Ollama の計測と意味が一致するか検証してから固定データを追加 |
| Performix | 正式製品/配布元、CLI版、取得形式・必要権限、Grafanaデータソース/保存先 | 製品の特定が必要。名前だけから導入・可視化方式を推測しない |
| 長期・オフライン再現 | 配布物のミラー保存先、保存期間、完全オフライン必須か | 現在は公開配布元へアクセス可能な再生成。配布物自体の保存は別途必要 |

本番の反復数・同時実行数・負荷生成ホスト等は「動作確認」と別の Runner として確定し、その設定を `specs/runners/` へ追加してから正式性能比較を行う。固定版と測定条件は既に A/B について決定済みであり、未確定事項として毎回聞き直さない。

## 仕様の編集と配布

配布単位は `Requirments.md` と `specs/` 一式。編集と検証の手順は [specs/README.md](specs/README.md) に従う。本文への再埋め込みは行わず、旧 `scripts/bundle_requirements.py` は使用しない。

仕様・モデル定義を先に変更し、Schema・テンプレート・Runner・検証テストを整合させる。レビューした変更について `python3 specs/check_inputs.py --update` で入力マニフェストを更新し、`python3 specs/check_inputs.py` で再確認する。ハッシュ更新だけで Schema や意味検証を合格にしてはならない。

## Docker 実走行からの仕様修正（2026-10-17）

- manifest 配置と Ollama 起動の順序を固定し、起動時整理処理との競合を防止する。
- thinking 設定は実際の API の `thinking.values` を検証する。
- 日付を読むテンプレートの入力変動を防ぐため、任意 `workload.template_date` を追加。具体値は specs/runners のみを正本とし、モデル重みや量子化は変えない。
- 事前生成0回のプロトコルと矛盾したウォームアップ記述を訂正する。
- summary 3.1.0 / Runner設定1.1.0 を生成対象とし、既存結果の互換Schemaを保存する。
- 生成後に実行ログと再実行の証跡を監査する。1反復のスモークを性能の統計的再現性検証と表現しない。

Adapter の具体的な検証は [specs/ollama-adapter.md](specs/ollama-adapter.md)、再現性監査は [specs/measurement-protocol.md](specs/measurement-protocol.md) に従う。

## 性能再現性の追加検査

同じ設定・同じ生成結果でも単発のToken/sに大きな差が出たため、summary 3.2.0で性能品質を推論成否から分離する。仕様はspecs/measurement-protocol.mdのquality/v1とspecs/summary-format.mdに従う。追加確認用Runnerをspecs/runnersへ固定し、閾値を満たすまで恣意的に測り直さない。未評価・閾値外の性能を安定したベンチマークと表現しない。

## 公開する入力と可搬性の範囲

GitHubで管理する設計入力は Requirments.md と specs/ のみでよい。Dockerfile・依存lockは `specs/bootstrap/`、配布物digest・固定Runnerは `specs/runners/` に置く。再生成時には配置表に従って固定データを配置し、実行コード・README・結果表示を生成する。既存の実装や過去の結果ファイルを必須入力にしない。

「どこでも再現」は対応条件を満たす環境で同じ契約・配布物・測定手順を構築できるという意味で、任意OS/CPUへの無条件対応や性能数値の一致を保証しない。現在検証した最小構成はNative/experimental/x86_64のWSL Ubuntuと固定Ubuntuコンテナ。AWS/ARM64等の未対応範囲は本文の段階C/Dに従う。公開配布元の停止・権限・資源不足は理由付きで停止する。

実走行の反復で性能品質が閾値外となる条件を確認した。品質判定は推論successと分離し、外れ値を除外して合格へ変更しない。生成AIは「テスト成功」を「性能が安定して再現する」と言い換えない。
