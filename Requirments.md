# llm_on_cpu 再生成仕様書

仕様整理日：2026-10-17（JST）。ファイル名は既存の `Requirments.md` を維持する。

## 1. この文書の目的と再生成の意味

**本書1ファイルを渡せば、実行スクリプト、Runner、JSON Schema、README、結果表示機能を生成し、実行・検証まで進められる状態を目指す。** 過去の会話、既存コード、別ファイルの設定を必須入力にしない。末尾に固定データを収録する。

再生成とは、同じデータ契約・固定配布物・測定手順・失敗処理で動く機能的に同等の環境を構築すること。生成されるソースコードのバイト一致、異なるホスト間の性能値一致、LLM 出力のビット一致を保証する意味ではない。固定イメージ・モデル・依存パッケージの取得にはネットワークと外部配布元が必要である。

- 本文：生成する機能・手順・意味検証・表示・受入条件の基準。
- 文書内の Schema：フィールド名・型・必須性・enum・null・互換性の基準。
- 文書内の Runner：モデル、バージョン、量子化、コンテキスト長、プロンプト等の具体値の基準。
- 生成後の実行ファイル：本書から作る成果物。本書の不足を既存実装から暗黙に補完しない。
- README：生成・検証した機能の使い方と実装状況。要件書や Runner を逆に規定する文書にしない。

本文と固定データが矛盾したら、その箇所を報告して本書を先に修正する。既存コードの挙動を無条件に正解として採用しない。新しい版への更新は本書の固定データ更新と再検証を経て行い、再生成時に「最新」を再選定しない。

## 2. 生成範囲と実装段階

最終目標は AWS / Native、x86_64 / ARM64、Ollama / vLLM、共通結果表示、ARM64 詳細解析を含む全体である。これと最小構成を区別する。

| 段階 | 生成・検証対象 | 本書単独での確定状況 |
| --- | --- | --- |
| A：最小の推論実行 | Native / experimental / x86_64、Ollama、Docker、全スケーリング、JSON 生成・検証 | 固定データを収録済み。実行先のメモリ・権限・ネットワークは実測検証 |
| B：最小の再生成一式 | A に README 生成、端末表示、オフライン HTML Dashboard を加える | 今回の再生成の既定目標。表示仕様・CLI・受入条件を本書で固定。現在の既存実装には未実装部分がある |
| C：本番比較 | AWS / production、ARM64、正式対象モデルの実測、メモリ帯域、課金 | 本文の目標仕様を維持。後述の未確定事項と配布物の固定が必要 |
| D：追加 Framework・解析 | vLLM、Performix → Grafana | 製品・バージョン・運用条件の追加決定が必要 |

「再生成する」だけの指示では B を対象とし、C/D を勝手に完了済みにしない。正式対象2モデルの Runner も生成するが、メモリ不足時の自動代替はしない。既定の小型 Runner によるスモーク成功と、正式対象の成功は別の検証結果として報告する。

2026-10-17 時点の既存実装は A の小型 Runner を実機検証済み、正式対象 Runner は固定・構文検証済み、大型推論・B の表示と README 自動生成・C/D は未完了。この情報は現状説明であり、再生成した成果物の検証証跡として流用しない。

## 3. 再生成時の入力・出力・実行入口

### 必須入力と外部前提

必須の設計入力は本書だけ。実行時入力は生成先ディレクトリ、Runner 選択、provider、profile、結果の保存先。既定は `~/work/llm_on_cpu`、内包する smoke Runner、`native`、`experimental`、プロジェクト配下 `results/` とする。

実行前に Ubuntu/WSL2、Python、Docker Engine、利用可能 CPU・メモリ・ディスク、ネットワーク、perf を検査する。WSL の `.wslconfig` 変更、Windows/WSL 再起動、ホストのメモリ増設、AWS アカウント・課金リソース作成は本書の生成処理に含めない。実行先の値をこの文書の過去の測定値から決め打ちしない。

初期ホスト Python は 3.12 以上で、Linux の venv・monotonic clock・SIGALRM が利用可能なこと。依存関係は内包の `requirements.lock` から導入し、導入に失敗したらバージョンを黙って緩めない。Docker Engine は CPU 制限・read-only bind mount・tmpfs を備え、収集処理と同じ Linux ホストで動くものを使用する。ホストツールの実際のバージョンを記録する。

オフライン再生成を必須とはしない。完全オフライン運用には Docker ベースイメージ、Framework archive、モデル全 blob、Python wheel 一式を別途保存する必要があり、Markdown だけでは代用できない。固定 digest が配布元から取得できなくなった場合は停止し、不足する配布物を報告する。

### 生成する成果物

| 成果物 | 生成要件 |
| --- | --- |
| `llmbench/` | Python パッケージと CLI。Host/Provider、Runtime、モデル Adapter、計測、集計、検証、表示を分離 |
| `runners/*.json` | 本書に内包する specs/runners/*.json の4つの汎用instanceを runners/ に配置する。モデル追加時は既存 Adapter で扱える限り設定追加だけで対応 |
| `schemas/*.json` | 現行 summary 3.2.0、旧3.1.0/3.0.0/2.0.0/1.0.0、汎用Runnerの完全スキーマをspecsから配置 |
| `docker/Dockerfile`、`.dockerignore` | 固定 Ubuntu ベースと CPU ランタイム。機密・結果・モデルをビルドコンテキストに入れない |
| `scripts/setup.sh` | venv・固定依存導入、前提確認。ホスト権限の不足を報告し、黙って変更しない |
| `scripts/generate_readme.py` | 下記の README 生成規則から実装状況に合う文書を生成 |
| `requirements.lock` | 内包したバージョンをそのまま復元 |
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

1. 本書の内包データを抽出し、ハッシュ・JSON構文・Schema 自身の妥当性を検証する。
2. 現行/旧スキーマ、Runner、Dockerfile、依存 lock を配置する。
3. 汎用instanceを生成し、CLI・前提検査・実行・収集・集計・検証・表示を生成し、ネットワーク不要のテストを実行する。
4. README 生成器を作り、実装済み範囲とテスト結果から README を生成する。
5. 実行環境で `doctor`、固定配布物のビルド・取得、小型 Runner の実推論を行う。必要な資源がなければ未検証として報告する。
6. 生成 summary を独立した `validate` で検証し、オフラインで `report` を再実行する。
7. 正式対象は資源条件を満たす場合に同じ手順で検証する。大型モデルを試していない場合はその旨を残す。
8. 最後に README の検証済み範囲を更新し、未完了機能と失敗原因を報告する。

生成先に既存ファイルがある場合は差分を確認して更新し、既存 results・ユーザー設定・キャッシュを一括削除しない。受入試験では本書だけを空ディレクトリへコピーして生成できることも確認する。

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

## Framework と初期モデル

| 実行ストリーム | 優先順位 | 方針 |
| --- | --- | --- |
| Ollama | 最優先 | CPU 向けモデル運用の選択肢を重視し、最初の実行・比較基盤を構築する |
| vLLM | 次段階 | 共通の測定・結果形式を利用し、CPU 実行に必要な環境と Runner を追加する |

初期モデルは以下の 2 つとする。

- **Qwen3-30B-A3B**（要件中の `Qen3-30B-A3B` はこのモデル名として扱う）
- **gpt-oss-20B**

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

1. Runner は内包する `runner.schema.json` で検証し、欠落キー・未知キー・不正な値を拒否する。全 Runner を列挙できるようにし、既定選択は smoke の1つとする。
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
| 文書単独性 | 本書だけを空ディレクトリへコピーし、既存コード・会話・外部設定を読まず必要成果物を生成できる |
| 固定データ | 内包ブロックのハッシュ一致、全固定 Runner のスキーマ適合、重み・量子化・num_ctx が勝手に変更されない |
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
| ARM64 の固定配布物 | 検証する実機、Framework archive/digest、依存差分 | x86_64 のバイナリを転用しない。検証後に本書へ ARM64 Runner/runtime lock を収録 |
| メモリ帯域 | STREAM 等の測定ツール、版、read/copy/triad、配列サイズ、NUMA 方針 | 共通手法を1つ選び版・条件を固定する。決定までは not_implemented。ユーザーの既存測定標準があれば優先 |
| vLLM | CPU backend、版、ビルド条件、対応モデル形式 | Ollama の計測と意味が一致するか検証してから固定データを追加 |
| Performix | 正式製品/配布元、CLI版、取得形式・必要権限、Grafanaデータソース/保存先 | 製品の特定が必要。名前だけから導入・可視化方式を推測しない |
| 長期・オフライン再現 | 配布物のミラー保存先、保存期間、完全オフライン必須か | 現在は公開配布元へアクセス可能な再生成。配布物自体の保存は別途必要 |

本番の反復数・同時実行数・負荷生成ホスト等は「動作確認」と別の Runner として確定し、その設定を本書へ収録してから正式性能比較を行う。固定版と測定条件は既に A/B について決定済みであり、未確定事項として毎回聞き直さない。

## 仕様の編集と単一文書への配布

編集元は specs/ 内の仕様ファイル、specs/runners の具体値、Dockerfile、依存lock。本書末尾は生成領域であり直接編集しない。

```bash
python3 scripts/bundle_requirements.py
python3 scripts/bundle_requirements.py --check
```

仕様変更時は specs を先に更新し、Schema・テンプレート・具体的Runner・検証テストを整合させ、その後に埋込領域を更新する。--check は古い埋込内容・ハッシュ不一致を検出し、書込をせず非0終了する。

Requirments.md だけを配布する場合、末尾の各ブロックを path の位置に復元する。JSON はキー順・空白を除く内容、テキストはUTF-8/LFのバイト一致を要求する。各 path は生成ルート配下へ限定し、絶対パス・..を拒否する。Markdownを含む内包ブロックは外側に4個のバッククォートを使う。

固定データの canonical JSON は json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)。生成・編集の違いで契約を二重管理しない。

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

GitHubで管理する設計入力は Requirments.md と specs/ のみでよい。Dockerfile・依存lock・配布物digest・固定Runner・再梱包スクリプトは本書に内包する。再生成時には本文の手順で抽出し、実行コード・README・結果表示を生成する。既存の実装や過去の結果ファイルを必須入力にしない。

「どこでも再現」は対応条件を満たす環境で同じ契約・配布物・測定手順を構築できるという意味で、任意OS/CPUへの無条件対応や性能数値の一致を保証しない。現在検証した最小構成はNative/experimental/x86_64のWSL Ubuntuと固定Ubuntuコンテナ。AWS/ARM64等の未対応範囲は本文の段階C/Dに従う。公開配布元の停止・権限・資源不足は理由付きで停止する。

実走行の反復で性能品質が閾値外となる条件を確認した。品質判定は推論successと分離し、外れ値を除外して合格へ変更しない。生成AIは「テスト成功」を「性能が安定して再現する」と言い換えない。

<!-- BEGIN GENERATED CONTRACT BUNDLE -->

## 内包データ（自動生成・直接編集禁止）

<details>
<summary>specs/compat/ollama-runner.schema.json</summary>

<!-- artifact path="specs/compat/ollama-runner.schema.json" sha256="4ceb9600187a4c5e67c4620285eee3324c35192a2195e7073cd55b911ddd9896" canonical="json" -->

````json
{"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"architecture":{"const":"x86_64"},"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"archive_url":{"format":"uri","type":"string"},"base_image":{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"},"framework_version":{"type":"string"},"id":{"type":"string"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"mode":{"const":"fresh_request_preloaded"},"num_batch":{"minimum":1,"type":"integer"},"num_ctx":{"minimum":1,"type":"integer"},"num_predict":{"minimum":1,"type":"integer"},"prompt":{"minLength":1,"type":"string"},"repetitions":{"minimum":1,"type":"integer"},"seed":{"minimum":0,"type":"integer"},"temperature":{"const":0},"think":{"enum":[false,true,"low","medium","high"]},"timeout_seconds":{"const":3600},"warmup_requests":{"const":0}},"required":["mode","repetitions","concurrency","warmup_requests","timeout_seconds","seed","num_ctx","num_predict","temperature","num_batch","think","prompt"],"type":"object"},"minimum_available_memory_bytes":{"minimum":0,"type":"integer"},"model":{"type":"string"},"model_config":{"additionalProperties":false,"properties":{"architecture":{"type":"string"},"file_type":{"type":"string"},"model_families":{"items":{"type":"string"},"type":"array"},"model_family":{"type":"string"},"model_format":{"type":"string"},"model_type":{"type":"string"},"os":{"type":"string"},"requires":{"type":"string"},"rootfs":{"additionalProperties":false,"properties":{"diff_ids":{"items":{"type":"string"},"type":"array"},"type":{"type":"string"}},"required":["type","diff_ids"],"type":"object"}},"required":["model_format","model_family","model_families","model_type","file_type"],"type":"object"},"model_manifest":{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},"model_manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"model_manifest_url":{"format":"uri","type":"string"},"perf_events":{"items":{"type":"string"},"minItems":1,"type":"array","uniqueItems":true},"purpose":{"const":"experimental_smoke"},"release_source":{"format":"uri","type":"string"}},"required":["id","purpose","framework_version","release_source","base_image","architecture","archive_url","archive_sha256","model","model_manifest_sha256","model_manifest_url","model_manifest","model_config","measurement","perf_events","minimum_available_memory_bytes"],"type":"object"}
````

</details>

<details>
<summary>specs/compat/runner-1.0.schema.json</summary>

<!-- artifact path="specs/compat/runner-1.0.schema.json" sha256="a9bac77d45183a59c52edbd95edba207971c292a19b6bc546ce11ce31ab156cb" canonical="json" -->

````json
{"$id":"urn:llm-on-cpu:runner:1.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":[{"additionalProperties":false,"properties":{"adapter":{"additionalProperties":false,"properties":{"id":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]},"version":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]}},"required":["id","version"],"type":"object"},"contract":{"const":"runner/v1"},"identity":{"additionalProperties":false,"properties":{"id":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]},"purpose":{"anyOf":[{"enum":["smoke","benchmark"]},{"type":"null"}]}},"required":["id","purpose"],"type":"object"},"kind":{"const":"template"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"perf_events":{"anyOf":[{"items":{"minLength":1,"type":"string"},"minItems":1,"type":"array","uniqueItems":true},{"type":"null"}]},"protocol":{"const":"fresh_request_preloaded/v1"},"repetitions":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]},"warmup_requests":{"const":0}},"required":["protocol","repetitions","concurrency","warmup_requests","perf_events"],"type":"object"},"model":{"additionalProperties":false,"properties":{"blobs":{"anyOf":[{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"size_bytes":{"minimum":0,"type":"integer"},"url":{"format":"uri","pattern":"^https://","type":"string"}},"required":["digest","size_bytes","url"],"type":"object"},"minItems":1,"type":"array"},{"type":"null"}]},"id":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]},"manifest":{"anyOf":[{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},{"type":"null"}]},"manifest_sha256":{"anyOf":[{"pattern":"^[a-f0-9]{64}$","type":"string"},{"type":"null"}]},"manifest_url":{"anyOf":[{"format":"uri","pattern":"^https://","type":"string"},{"type":"null"}]},"quantization":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]}},"required":["id","manifest_url","manifest_sha256","manifest","blobs","quantization"],"type":"object"},"resources":{"additionalProperties":false,"properties":{"minimum_available_memory_bytes":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]}},"required":["minimum_available_memory_bytes"],"type":"object"},"runner_schema_version":{"const":"1.0.0"},"runtime":{"additionalProperties":false,"properties":{"architecture":{"anyOf":[{"enum":["x86_64","arm64"]},{"type":"null"}]},"archive_sha256":{"anyOf":[{"pattern":"^[a-f0-9]{64}$","type":"string"},{"type":"null"}]},"archive_url":{"anyOf":[{"format":"uri","pattern":"^https://","type":"string"},{"type":"null"}]},"base_image":{"anyOf":[{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"},{"type":"null"}]}},"required":["architecture","base_image","archive_url","archive_sha256"],"type":"object"},"timeouts":{"additionalProperties":false,"properties":{"cleanup_seconds":{"const":60},"preparation_seconds":{"const":3600},"repetition_seconds":{"const":3600}},"required":["preparation_seconds","repetition_seconds","cleanup_seconds"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"batch_size":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]},"context_length":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]},"max_output_tokens":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]},"prompt":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]},"seed":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"temperature":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"think":{"anyOf":[{"enum":[false,true,"low","medium","high"],"type":["boolean","string"]},{"type":"null"}]}},"required":["prompt","context_length","max_output_tokens","seed","temperature","batch_size","think"],"type":"object"}},"required":["runner_schema_version","contract","kind","identity","adapter","runtime","model","workload","measurement","resources","timeouts"],"type":"object"},{"additionalProperties":false,"properties":{"adapter":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"version":{"minLength":1,"type":"string"}},"required":["id","version"],"type":"object"},"contract":{"const":"runner/v1"},"identity":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"purpose":{"enum":["smoke","benchmark"]}},"required":["id","purpose"],"type":"object"},"kind":{"const":"instance"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"perf_events":{"items":{"minLength":1,"type":"string"},"minItems":1,"type":"array","uniqueItems":true},"protocol":{"const":"fresh_request_preloaded/v1"},"repetitions":{"minimum":1,"type":"integer"},"warmup_requests":{"const":0}},"required":["protocol","repetitions","concurrency","warmup_requests","perf_events"],"type":"object"},"model":{"additionalProperties":false,"properties":{"blobs":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"size_bytes":{"minimum":0,"type":"integer"},"url":{"format":"uri","pattern":"^https://","type":"string"}},"required":["digest","size_bytes","url"],"type":"object"},"minItems":1,"type":"array"},"id":{"minLength":1,"type":"string"},"manifest":{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"manifest_url":{"format":"uri","pattern":"^https://","type":"string"},"quantization":{"minLength":1,"type":"string"}},"required":["id","manifest_url","manifest_sha256","manifest","blobs","quantization"],"type":"object"},"resources":{"additionalProperties":false,"properties":{"minimum_available_memory_bytes":{"minimum":1,"type":"integer"}},"required":["minimum_available_memory_bytes"],"type":"object"},"runner_schema_version":{"const":"1.0.0"},"runtime":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64"]},"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"archive_url":{"format":"uri","pattern":"^https://","type":"string"},"base_image":{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"}},"required":["architecture","base_image","archive_url","archive_sha256"],"type":"object"},"timeouts":{"additionalProperties":false,"properties":{"cleanup_seconds":{"const":60},"preparation_seconds":{"const":3600},"repetition_seconds":{"const":3600}},"required":["preparation_seconds","repetition_seconds","cleanup_seconds"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"batch_size":{"minimum":1,"type":"integer"},"context_length":{"minimum":1,"type":"integer"},"max_output_tokens":{"minimum":1,"type":"integer"},"prompt":{"minLength":1,"type":"string"},"seed":{"minimum":0,"type":"integer"},"temperature":{"minimum":0,"type":"number"},"think":{"enum":[false,true,"low","medium","high"],"type":["boolean","string"]}},"required":["prompt","context_length","max_output_tokens","seed","temperature","batch_size","think"],"type":"object"}},"required":["runner_schema_version","contract","kind","identity","adapter","runtime","model","workload","measurement","resources","timeouts"],"type":"object"}]}
````

</details>

<details>
<summary>specs/compat/summary-1.0.schema.json</summary>

<!-- artifact path="specs/compat/summary-1.0.schema.json" sha256="6209a05ad68505fdb2c85517e08c1b2c5b0128dd16c84fa5adbb69062a723cbd" canonical="json" -->

````json
{"$defs":{"aggregate_events":{"additionalProperties":{"$ref":"#/$defs/aggregate_measure"},"minProperties":1,"type":"object"},"aggregate_measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"excluded_samples":{"minimum":0,"type":"integer"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"valid_samples":{"minimum":0,"type":"integer"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","valid_samples","excluded_samples"],"type":"object"},"bandwidth":{"additionalProperties":false,"properties":{"bytes_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["measured","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["bytes_per_second","kind","source","status","reason"],"type":"object"},"clock":{"additionalProperties":false,"properties":{"hz":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["observed","base","max","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["hz","kind","source","status","reason"],"type":"object"},"condition":{"additionalProperties":false,"properties":{"condition_id":{"pattern":"^vcpu-[1-9][0-9]*$","type":"string"},"cost":{"$ref":"#/$defs/cost"},"metrics":{"anyOf":[{"$ref":"#/$defs/metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_aggregate"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetitions":{"items":{"$ref":"#/$defs/repetition"},"type":"array"},"requested_ratios":{"items":{"enum":["1/4","1/2","3/4","4/4"]},"type":"array"},"resources":{"additionalProperties":false,"properties":{"cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"memory_limit_bytes":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"memory_policy":{"type":"string"},"threads":{"minimum":0,"type":"integer"},"vcpu_count":{"minimum":1,"type":"integer"}},"required":["vcpu_count","cpu_ids","threads","memory_policy","memory_limit_bytes"],"type":"object"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["condition_id","requested_ratios","status","reason","resources","metrics","profiling","cost","repetitions"],"type":"object"},"cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method"],"type":"object"},"event":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"multiplex_scaled":{"anyOf":[{"type":"boolean"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"running_percent":{"anyOf":[{"maximum":100,"minimum":0,"type":"number"},{"type":"null"}]},"running_time_ns":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","running_time_ns","running_percent","multiplex_scaled"],"type":"object"},"events":{"additionalProperties":{"$ref":"#/$defs/event"},"minProperties":1,"type":"object"},"external_object":{"additionalProperties":true,"description":"Opaque upstream manifest/config or Runner snapshot; hashes validated separately.","type":"object"},"isolation":{"additionalProperties":false,"properties":{"cache_evidence":{"anyOf":[{"type":"string"},{"type":"null"}]},"cache_verified":{"type":"boolean"},"container_id":{"pattern":"^[a-f0-9]{64}$","type":"string"},"container_name":{"type":"string"},"cpu_only_verified":{"type":"boolean"},"deleted":{"type":"boolean"},"effective_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"effective_num_thread":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"model_read_only":{"type":"boolean"},"new_container":{"type":"boolean"},"num_thread":{"minimum":0,"type":"integer"},"preload_output_tokens":{"minimum":0,"type":"integer"},"prior_generation_requests":{"minimum":0,"type":"integer"},"process_allowed_list":{"type":"string"}},"required":["container_id","container_name","new_container","deleted","effective_cpu_ids","process_allowed_list","num_thread","cpu_only_verified","cache_verified","cache_evidence","effective_num_thread","prior_generation_requests","preload_output_tokens","model_read_only"],"type":"object"},"measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason"],"type":"object"},"metrics":{"additionalProperties":false,"properties":{"aggregation":{"const":"median"},"failed_repetitions":{"minimum":0,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"parallel_efficiency":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"planned_repetitions":{"minimum":1,"type":"integer"},"speedup":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"successful_repetitions":{"minimum":0,"type":"integer"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["aggregation","planned_repetitions","successful_repetitions","failed_repetitions","output_tokens_per_second","ttft_seconds","speedup","parallel_efficiency"],"type":"object"},"os":{"additionalProperties":false,"properties":{"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version"],"type":"object"},"perf_aggregate":{"additionalProperties":false,"properties":{"aggregation":{"const":"median_of_successful_repetitions"},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/aggregate_measure"}},"required":["ipc"],"type":"object"},"events_per_second":{"$ref":"#/$defs/aggregate_events"}},"required":["cpu_id","events_per_second","derived"],"type":"object"},"type":"array"}},"required":["aggregation","per_vcpu"],"type":"object"},"perf_config":{"additionalProperties":false,"properties":{"binary":{"anyOf":[{"type":"string"},{"type":"null"}]},"events":{"additionalProperties":{"additionalProperties":false,"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["status","reason"],"type":"object"},"minProperties":1,"type":"object"},"interval_ms":{"minimum":1,"type":"integer"},"scope":{"const":"system_wide_selected_cpus"},"version":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["binary","version","events","interval_ms","scope"],"type":"object"},"perf_raw":{"additionalProperties":false,"properties":{"artifact":{"type":"string"},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/measure"}},"required":["ipc"],"type":"object"},"events":{"$ref":"#/$defs/events"}},"required":["cpu_id","events","derived"],"type":"object"},"type":"array"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"scope":{"const":"system_wide_selected_cpus"},"status":{"enum":["ok","partial","unavailable","error"]}},"required":["status","reason","scope","per_vcpu","artifact"],"type":"object"},"raw_metrics":{"additionalProperties":false,"properties":{"decode_tokens_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"done_reason":{"type":"string"},"error_count":{"minimum":0,"type":"integer"},"input_tokens":{"minimum":0,"type":"integer"},"latency_seconds":{"minimum":0,"type":"number"},"output_tokens":{"minimum":1,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"request_count":{"minimum":0,"type":"integer"},"response_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"success_count":{"minimum":0,"type":"integer"},"ttft_method":{"const":"first_nonempty_content_chunk"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["output_tokens","input_tokens","output_tokens_per_second","request_count","success_count","error_count","ttft_seconds","ttft_method","latency_seconds","decode_tokens_per_second","response_sha256","done_reason"],"type":"object"},"repetition":{"additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"log":{"type":"string"},"response":{"type":"string"}},"required":["response","log"],"type":"object"},"cost":{"$ref":"#/$defs/cost"},"isolation":{"anyOf":[{"$ref":"#/$defs/isolation"},{"type":"null"}]},"metrics":{"anyOf":[{"$ref":"#/$defs/raw_metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_raw"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetition_id":{"minimum":1,"type":"integer"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]},"timing":{"$ref":"#/$defs/timing"}},"required":["repetition_id","status","reason","timing","isolation","metrics","profiling","cost","artifacts"],"type":"object"},"runner":{"additionalProperties":false,"properties":{"architecture":{"const":"x86_64"},"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"archive_url":{"format":"uri","type":"string"},"base_image":{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"},"framework_version":{"type":"string"},"id":{"type":"string"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"mode":{"const":"fresh_request_preloaded"},"num_batch":{"minimum":1,"type":"integer"},"num_ctx":{"minimum":1,"type":"integer"},"num_predict":{"minimum":1,"type":"integer"},"prompt":{"minLength":1,"type":"string"},"repetitions":{"minimum":1,"type":"integer"},"seed":{"minimum":0,"type":"integer"},"temperature":{"const":0},"think":{"const":false},"timeout_seconds":{"const":3600},"warmup_requests":{"const":0}},"required":["mode","repetitions","concurrency","warmup_requests","timeout_seconds","seed","num_ctx","num_predict","temperature","num_batch","think","prompt"],"type":"object"},"minimum_available_memory_bytes":{"minimum":0,"type":"integer"},"model":{"type":"string"},"model_config":{"additionalProperties":false,"properties":{"architecture":{"type":"string"},"file_type":{"type":"string"},"model_families":{"items":{"type":"string"},"type":"array"},"model_family":{"type":"string"},"model_format":{"type":"string"},"model_type":{"type":"string"},"os":{"type":"string"},"rootfs":{"additionalProperties":false,"properties":{"diff_ids":{"items":{"type":"string"},"type":"array"},"type":{"type":"string"}},"required":["type","diff_ids"],"type":"object"}},"required":["model_format","model_family","model_families","model_type","file_type","architecture","os","rootfs"],"type":"object"},"model_manifest":{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},"model_manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"model_manifest_url":{"format":"uri","type":"string"},"perf_events":{"items":{"type":"string"},"minItems":1,"type":"array","uniqueItems":true},"purpose":{"const":"experimental_smoke"},"release_source":{"format":"uri","type":"string"}},"required":["id","purpose","framework_version","release_source","base_image","architecture","archive_url","archive_sha256","model","model_manifest_sha256","model_manifest_url","model_manifest","model_config","measurement","perf_events","minimum_available_memory_bytes"],"type":"object"},"storage":{"additionalProperties":false,"properties":{"capacity_bytes":{"minimum":0,"type":"integer"},"hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"id":{"type":"string"},"source":{"type":"string"},"type":{"type":"string"}},"required":["id","type","capacity_bytes","hourly_rate","source"],"type":"object"},"timing":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_duration_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"measurement_ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_started_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"sequence_index":{"minimum":1,"type":"integer"},"started_at":{"format":"date-time","type":"string"}},"required":["sequence_index","started_at","ended_at","measurement_started_at","measurement_ended_at","measurement_duration_seconds"],"type":"object"},"total_cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"other_duration_seconds":{"minimum":0,"type":"number"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"shared_setup_duration_seconds":{"minimum":0,"type":"number"},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method","shared_setup_duration_seconds","other_duration_seconds"],"type":"object"}},"$id":"urn:llm-on-cpu:summary:1.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"dashboard":{"$ref":"#/$defs/measure"},"logs":{"type":"string"}},"required":["logs","dashboard"],"type":"object"},"cache_policy":{"additionalProperties":false,"properties":{"hardware_cache":{"type":"string"},"model_files":{"type":"string"},"page_cache":{"type":"string"},"strategy":{"type":"string"},"verification":{"type":"string"},"warmup_requests":{"minimum":0,"type":"integer"},"within_request_kv":{"type":"string"}},"required":["strategy","warmup_requests","model_files","page_cache","hardware_cache","within_request_kv","verification"],"type":"object"},"cost":{"$ref":"#/$defs/total_cost"},"environment":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64","aarch64"]},"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"aws":{"anyOf":[{"additionalProperties":false,"properties":{"ami":{"anyOf":[{"type":"string"},{"type":"null"}]},"instance_type":{"anyOf":[{"type":"string"},{"type":"null"}]},"region":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["instance_type","region","ami"],"type":"object"},{"type":"null"}]},"cpu_quota":{"anyOf":[{"type":"string"},{"type":"null"}]},"cpu_topology":{"items":{"additionalProperties":false,"properties":{"core_id":{"minimum":0,"type":"integer"},"cpu_id":{"minimum":0,"type":"integer"},"numa_node":{"minimum":0,"type":"integer"},"socket_id":{"minimum":0,"type":"integer"}},"required":["cpu_id","core_id","socket_id","numa_node"],"type":"object"},"type":"array"},"host_id":{"type":"string"},"kernel_release":{"type":"string"},"os":{"$ref":"#/$defs/os"},"provider":{"enum":["native","aws"]},"virtualization":{"additionalProperties":false,"properties":{"kind":{"enum":["wsl2","vm","bare_metal","unknown"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["kind","status","reason"],"type":"object"}},"required":["provider","host_id","architecture","os","kernel_release","virtualization","aws","cpu_topology","available_cpu_ids","cpu_quota"],"type":"object"},"execution":{"additionalProperties":false,"properties":{"container_os":{"anyOf":[{"$ref":"#/$defs/os"},{"type":"null"}]},"docker_version":{"type":"string"},"dockerfile_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"image_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"load_generator":{"type":"string"},"mode":{"type":"string"},"profile":{"enum":["experimental","production"]},"timeout_seconds":{"const":3600}},"required":["profile","mode","docker_version","image_id","dockerfile_sha256","container_os","load_generator","timeout_seconds"],"type":"object"},"framework":{"additionalProperties":false,"properties":{"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"backend":{"const":"cpu"},"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version","backend","archive_sha256"],"type":"object"},"model":{"additionalProperties":false,"properties":{"format":{"type":"string"},"id":{"type":"string"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"quantization":{"type":"string"}},"required":["id","manifest_sha256","quantization","format"],"type":"object"},"platform":{"additionalProperties":false,"properties":{"cpu":{"additionalProperties":false,"properties":{"clock":{"$ref":"#/$defs/clock"},"name":{"type":"string"}},"required":["name","clock"],"type":"object"},"memory":{"additionalProperties":false,"properties":{"available_bytes_at_start":{"minimum":0,"type":"integer"},"bandwidth":{"$ref":"#/$defs/bandwidth"},"capacity_bytes":{"minimum":0,"type":"integer"}},"required":["capacity_bytes","available_bytes_at_start","bandwidth"],"type":"object"},"name":{"type":"string"},"vcpu_count":{"minimum":0,"type":"integer"}},"required":["name","vcpu_count","cpu","memory"],"type":"object"},"pricing":{"additionalProperties":false,"properties":{"compute_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"storage":{"items":{"$ref":"#/$defs/storage"},"type":"array"},"storage_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","compute_hourly_rate","storage_hourly_rate","total_hourly_rate","storage"],"type":"object"},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_config"},{"type":"null"}]},"performix":{"$ref":"#/$defs/measure"}},"required":["perf","performix"],"type":"object"},"run":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"errors":{"items":{"additionalProperties":false,"properties":{"code":{"enum":[2,10,20,30,31,32,40,50,130]},"condition_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"message":{"type":"string"},"phase":{"type":"string"}},"required":["code","phase","message","condition_id"],"type":"object"},"type":"array"},"exit_code":{"anyOf":[{"enum":[0,2,10,20,30,31,32,40,50,130]},{"type":"null"}]},"id":{"type":"string"},"started_at":{"format":"date-time","type":"string"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["id","started_at","ended_at","status","exit_code","errors"],"type":"object"},"scaling":{"additionalProperties":false,"properties":{"plan":{"additionalProperties":false,"properties":{"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"base_nproc":{"minimum":1,"type":"integer"},"baseline_condition_id":{"type":"string"},"cpu_selection":{"type":"string"},"requested_ratios":{"const":["1/4","1/2","3/4","4/4"]},"rounding":{"type":"string"},"sequence_seed":{"minimum":0,"type":"integer"}},"required":["base_nproc","available_cpu_ids","requested_ratios","baseline_condition_id","rounding","cpu_selection","sequence_seed"],"type":"object"},"results":{"items":{"$ref":"#/$defs/condition"},"type":"array"}},"required":["plan","results"],"type":"object"},"schema_version":{"const":"1.0.0"},"toolchain":{"additionalProperties":false,"properties":{"compiler":{"$ref":"#/$defs/measure"},"distribution":{"type":"string"},"python_version":{"type":"string"}},"required":["distribution","compiler","python_version"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"prompt_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"runner_config":{"$ref":"#/$defs/runner"},"runner_id":{"type":"string"},"runner_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"}},"required":["runner_id","runner_sha256","runner_config","prompt_sha256"],"type":"object"}},"required":["schema_version","run","environment","platform","toolchain","framework","model","workload","execution","cache_policy","profiling","pricing","cost","scaling","artifacts"],"title":"llm_on_cpu summary 1.0.0","type":"object"}
````

</details>

<details>
<summary>specs/compat/summary-2.0.schema.json</summary>

<!-- artifact path="specs/compat/summary-2.0.schema.json" sha256="a28854ce39646390dbaef9a39fb05a95cbc89ce24907b9d412162f7c83ef40ec" canonical="json" -->

````json
{"$defs":{"aggregate_events":{"additionalProperties":{"$ref":"#/$defs/aggregate_measure"},"minProperties":1,"type":"object"},"aggregate_measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"excluded_samples":{"minimum":0,"type":"integer"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"valid_samples":{"minimum":0,"type":"integer"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","valid_samples","excluded_samples"],"type":"object"},"bandwidth":{"additionalProperties":false,"properties":{"bytes_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["measured","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["bytes_per_second","kind","source","status","reason"],"type":"object"},"clock":{"additionalProperties":false,"properties":{"hz":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["observed","base","max","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["hz","kind","source","status","reason"],"type":"object"},"condition":{"additionalProperties":false,"properties":{"condition_id":{"pattern":"^vcpu-[1-9][0-9]*$","type":"string"},"cost":{"$ref":"#/$defs/cost"},"metrics":{"anyOf":[{"$ref":"#/$defs/metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_aggregate"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetitions":{"items":{"$ref":"#/$defs/repetition"},"type":"array"},"requested_ratios":{"items":{"enum":["1/4","1/2","3/4","4/4"]},"type":"array"},"resources":{"additionalProperties":false,"properties":{"cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"memory_limit_bytes":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"memory_policy":{"type":"string"},"threads":{"minimum":0,"type":"integer"},"vcpu_count":{"minimum":1,"type":"integer"}},"required":["vcpu_count","cpu_ids","threads","memory_policy","memory_limit_bytes"],"type":"object"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["condition_id","requested_ratios","status","reason","resources","metrics","profiling","cost","repetitions"],"type":"object"},"cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method"],"type":"object"},"event":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"multiplex_scaled":{"anyOf":[{"type":"boolean"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"running_percent":{"anyOf":[{"maximum":100,"minimum":0,"type":"number"},{"type":"null"}]},"running_time_ns":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","running_time_ns","running_percent","multiplex_scaled"],"type":"object"},"events":{"additionalProperties":{"$ref":"#/$defs/event"},"minProperties":1,"type":"object"},"external_object":{"additionalProperties":true,"description":"Opaque upstream manifest/config or Runner snapshot; hashes validated separately.","type":"object"},"isolation":{"additionalProperties":false,"properties":{"cache_evidence":{"anyOf":[{"type":"string"},{"type":"null"}]},"cache_verified":{"type":"boolean"},"container_id":{"pattern":"^[a-f0-9]{64}$","type":"string"},"container_name":{"type":"string"},"context_length":{"minimum":1,"type":"integer"},"cpu_only_verified":{"type":"boolean"},"deleted":{"type":"boolean"},"effective_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"effective_num_thread":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"model_manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"model_read_only":{"type":"boolean"},"new_container":{"type":"boolean"},"num_thread":{"minimum":0,"type":"integer"},"preload_output_tokens":{"minimum":0,"type":"integer"},"prior_generation_requests":{"minimum":0,"type":"integer"},"process_allowed_list":{"type":"string"},"quantization":{"type":"string"}},"required":["container_id","container_name","new_container","deleted","effective_cpu_ids","process_allowed_list","num_thread","cpu_only_verified","cache_verified","cache_evidence","effective_num_thread","prior_generation_requests","preload_output_tokens","model_read_only","model_manifest_sha256","quantization","context_length"],"type":"object"},"measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason"],"type":"object"},"metrics":{"additionalProperties":false,"properties":{"aggregation":{"const":"median"},"failed_repetitions":{"minimum":0,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"parallel_efficiency":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"planned_repetitions":{"minimum":1,"type":"integer"},"speedup":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"successful_repetitions":{"minimum":0,"type":"integer"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["aggregation","planned_repetitions","successful_repetitions","failed_repetitions","output_tokens_per_second","ttft_seconds","speedup","parallel_efficiency"],"type":"object"},"os":{"additionalProperties":false,"properties":{"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version"],"type":"object"},"perf_aggregate":{"additionalProperties":false,"properties":{"aggregation":{"const":"median_of_successful_repetitions"},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/aggregate_measure"}},"required":["ipc"],"type":"object"},"events_per_second":{"$ref":"#/$defs/aggregate_events"}},"required":["cpu_id","events_per_second","derived"],"type":"object"},"type":"array"}},"required":["aggregation","per_vcpu"],"type":"object"},"perf_config":{"additionalProperties":false,"properties":{"binary":{"anyOf":[{"type":"string"},{"type":"null"}]},"events":{"additionalProperties":{"additionalProperties":false,"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["status","reason"],"type":"object"},"minProperties":1,"type":"object"},"interval_ms":{"minimum":1,"type":"integer"},"scope":{"const":"system_wide_selected_cpus"},"version":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["binary","version","events","interval_ms","scope"],"type":"object"},"perf_raw":{"additionalProperties":false,"properties":{"artifact":{"type":"string"},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/measure"}},"required":["ipc"],"type":"object"},"events":{"$ref":"#/$defs/events"}},"required":["cpu_id","events","derived"],"type":"object"},"type":"array"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"scope":{"const":"system_wide_selected_cpus"},"status":{"enum":["ok","partial","unavailable","error"]}},"required":["status","reason","scope","per_vcpu","artifact"],"type":"object"},"raw_metrics":{"additionalProperties":false,"properties":{"decode_tokens_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"done_reason":{"type":"string"},"error_count":{"minimum":0,"type":"integer"},"first_generated_chunk_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"input_tokens":{"minimum":0,"type":"integer"},"latency_seconds":{"minimum":0,"type":"number"},"output_tokens":{"minimum":1,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"request_count":{"minimum":0,"type":"integer"},"response_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"success_count":{"minimum":0,"type":"integer"},"thinking_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"ttft_method":{"const":"first_nonempty_content_chunk"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["output_tokens","input_tokens","output_tokens_per_second","request_count","success_count","error_count","ttft_seconds","ttft_method","latency_seconds","decode_tokens_per_second","response_sha256","done_reason","thinking_sha256","first_generated_chunk_seconds"],"type":"object"},"repetition":{"additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"log":{"type":"string"},"response":{"type":"string"}},"required":["response","log"],"type":"object"},"cost":{"$ref":"#/$defs/cost"},"isolation":{"anyOf":[{"$ref":"#/$defs/isolation"},{"type":"null"}]},"metrics":{"anyOf":[{"$ref":"#/$defs/raw_metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_raw"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetition_id":{"minimum":1,"type":"integer"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]},"timing":{"$ref":"#/$defs/timing"}},"required":["repetition_id","status","reason","timing","isolation","metrics","profiling","cost","artifacts"],"type":"object"},"runner":{"additionalProperties":false,"properties":{"architecture":{"const":"x86_64"},"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"archive_url":{"format":"uri","type":"string"},"base_image":{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"},"framework_version":{"type":"string"},"id":{"type":"string"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"mode":{"const":"fresh_request_preloaded"},"num_batch":{"minimum":1,"type":"integer"},"num_ctx":{"minimum":1,"type":"integer"},"num_predict":{"minimum":1,"type":"integer"},"prompt":{"minLength":1,"type":"string"},"repetitions":{"minimum":1,"type":"integer"},"seed":{"minimum":0,"type":"integer"},"temperature":{"const":0},"think":{"enum":[false,true,"low","medium","high"]},"timeout_seconds":{"const":3600},"warmup_requests":{"const":0}},"required":["mode","repetitions","concurrency","warmup_requests","timeout_seconds","seed","num_ctx","num_predict","temperature","num_batch","think","prompt"],"type":"object"},"minimum_available_memory_bytes":{"minimum":0,"type":"integer"},"model":{"type":"string"},"model_config":{"additionalProperties":false,"properties":{"architecture":{"type":"string"},"file_type":{"type":"string"},"model_families":{"items":{"type":"string"},"type":"array"},"model_family":{"type":"string"},"model_format":{"type":"string"},"model_type":{"type":"string"},"os":{"type":"string"},"requires":{"type":"string"},"rootfs":{"additionalProperties":false,"properties":{"diff_ids":{"items":{"type":"string"},"type":"array"},"type":{"type":"string"}},"required":["type","diff_ids"],"type":"object"}},"required":["model_format","model_family","model_families","model_type","file_type"],"type":"object"},"model_manifest":{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},"model_manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"model_manifest_url":{"format":"uri","type":"string"},"perf_events":{"items":{"type":"string"},"minItems":1,"type":"array","uniqueItems":true},"purpose":{"const":"experimental_smoke"},"release_source":{"format":"uri","type":"string"}},"required":["id","purpose","framework_version","release_source","base_image","architecture","archive_url","archive_sha256","model","model_manifest_sha256","model_manifest_url","model_manifest","model_config","measurement","perf_events","minimum_available_memory_bytes"],"type":"object"},"storage":{"additionalProperties":false,"properties":{"capacity_bytes":{"minimum":0,"type":"integer"},"hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"id":{"type":"string"},"source":{"type":"string"},"type":{"type":"string"}},"required":["id","type","capacity_bytes","hourly_rate","source"],"type":"object"},"timing":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_duration_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"measurement_ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_started_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"sequence_index":{"minimum":1,"type":"integer"},"started_at":{"format":"date-time","type":"string"}},"required":["sequence_index","started_at","ended_at","measurement_started_at","measurement_ended_at","measurement_duration_seconds"],"type":"object"},"total_cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"other_duration_seconds":{"minimum":0,"type":"number"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"shared_setup_duration_seconds":{"minimum":0,"type":"number"},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method","shared_setup_duration_seconds","other_duration_seconds"],"type":"object"}},"$id":"urn:llm-on-cpu:summary:2.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"dashboard":{"$ref":"#/$defs/measure"},"logs":{"type":"string"}},"required":["logs","dashboard"],"type":"object"},"cache_policy":{"additionalProperties":false,"properties":{"hardware_cache":{"type":"string"},"model_files":{"type":"string"},"page_cache":{"type":"string"},"strategy":{"type":"string"},"verification":{"type":"string"},"warmup_requests":{"minimum":0,"type":"integer"},"within_request_kv":{"type":"string"}},"required":["strategy","warmup_requests","model_files","page_cache","hardware_cache","within_request_kv","verification"],"type":"object"},"cost":{"$ref":"#/$defs/total_cost"},"environment":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64","aarch64"]},"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"aws":{"anyOf":[{"additionalProperties":false,"properties":{"ami":{"anyOf":[{"type":"string"},{"type":"null"}]},"instance_type":{"anyOf":[{"type":"string"},{"type":"null"}]},"region":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["instance_type","region","ami"],"type":"object"},{"type":"null"}]},"cpu_quota":{"anyOf":[{"type":"string"},{"type":"null"}]},"cpu_topology":{"items":{"additionalProperties":false,"properties":{"core_id":{"minimum":0,"type":"integer"},"cpu_id":{"minimum":0,"type":"integer"},"numa_node":{"minimum":0,"type":"integer"},"socket_id":{"minimum":0,"type":"integer"}},"required":["cpu_id","core_id","socket_id","numa_node"],"type":"object"},"type":"array"},"host_id":{"type":"string"},"kernel_release":{"type":"string"},"os":{"$ref":"#/$defs/os"},"provider":{"enum":["native","aws"]},"virtualization":{"additionalProperties":false,"properties":{"kind":{"enum":["wsl2","vm","bare_metal","unknown"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["kind","status","reason"],"type":"object"}},"required":["provider","host_id","architecture","os","kernel_release","virtualization","aws","cpu_topology","available_cpu_ids","cpu_quota"],"type":"object"},"execution":{"additionalProperties":false,"properties":{"container_os":{"anyOf":[{"$ref":"#/$defs/os"},{"type":"null"}]},"docker_version":{"type":"string"},"dockerfile_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"image_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"load_generator":{"type":"string"},"mode":{"type":"string"},"profile":{"enum":["experimental","production"]},"timeout_seconds":{"const":3600}},"required":["profile","mode","docker_version","image_id","dockerfile_sha256","container_os","load_generator","timeout_seconds"],"type":"object"},"framework":{"additionalProperties":false,"properties":{"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"backend":{"const":"cpu"},"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version","backend","archive_sha256"],"type":"object"},"model":{"additionalProperties":false,"properties":{"format":{"type":"string"},"id":{"type":"string"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"quantization":{"type":"string"}},"required":["id","manifest_sha256","quantization","format"],"type":"object"},"platform":{"additionalProperties":false,"properties":{"cpu":{"additionalProperties":false,"properties":{"clock":{"$ref":"#/$defs/clock"},"name":{"type":"string"}},"required":["name","clock"],"type":"object"},"memory":{"additionalProperties":false,"properties":{"available_bytes_at_start":{"minimum":0,"type":"integer"},"bandwidth":{"$ref":"#/$defs/bandwidth"},"capacity_bytes":{"minimum":0,"type":"integer"}},"required":["capacity_bytes","available_bytes_at_start","bandwidth"],"type":"object"},"name":{"type":"string"},"vcpu_count":{"minimum":0,"type":"integer"}},"required":["name","vcpu_count","cpu","memory"],"type":"object"},"pricing":{"additionalProperties":false,"properties":{"compute_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"storage":{"items":{"$ref":"#/$defs/storage"},"type":"array"},"storage_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","compute_hourly_rate","storage_hourly_rate","total_hourly_rate","storage"],"type":"object"},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_config"},{"type":"null"}]},"performix":{"$ref":"#/$defs/measure"}},"required":["perf","performix"],"type":"object"},"run":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"errors":{"items":{"additionalProperties":false,"properties":{"code":{"enum":[2,10,20,30,31,32,40,50,130]},"condition_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"message":{"type":"string"},"phase":{"type":"string"}},"required":["code","phase","message","condition_id"],"type":"object"},"type":"array"},"exit_code":{"anyOf":[{"enum":[0,2,10,20,30,31,32,40,50,130]},{"type":"null"}]},"id":{"type":"string"},"started_at":{"format":"date-time","type":"string"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["id","started_at","ended_at","status","exit_code","errors"],"type":"object"},"scaling":{"additionalProperties":false,"properties":{"plan":{"additionalProperties":false,"properties":{"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"base_nproc":{"minimum":1,"type":"integer"},"baseline_condition_id":{"type":"string"},"cpu_selection":{"type":"string"},"requested_ratios":{"const":["1/4","1/2","3/4","4/4"]},"rounding":{"type":"string"},"sequence_seed":{"minimum":0,"type":"integer"}},"required":["base_nproc","available_cpu_ids","requested_ratios","baseline_condition_id","rounding","cpu_selection","sequence_seed"],"type":"object"},"results":{"items":{"$ref":"#/$defs/condition"},"type":"array"}},"required":["plan","results"],"type":"object"},"schema_version":{"const":"2.0.0"},"toolchain":{"additionalProperties":false,"properties":{"compiler":{"$ref":"#/$defs/measure"},"distribution":{"type":"string"},"python_version":{"type":"string"}},"required":["distribution","compiler","python_version"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"prompt_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"runner_config":{"$ref":"#/$defs/runner"},"runner_id":{"type":"string"},"runner_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"}},"required":["runner_id","runner_sha256","runner_config","prompt_sha256"],"type":"object"}},"required":["schema_version","run","environment","platform","toolchain","framework","model","workload","execution","cache_policy","profiling","pricing","cost","scaling","artifacts"],"title":"llm_on_cpu summary 2.0.0","type":"object"}
````

</details>

<details>
<summary>specs/compat/summary-3.0.schema.json</summary>

<!-- artifact path="specs/compat/summary-3.0.schema.json" sha256="fc678502a084fb438d5fac4f740b31278eb634b35710cba061a7f4759e3534c1" canonical="json" -->

````json
{"$defs":{"aggregate_events":{"additionalProperties":{"$ref":"#/$defs/aggregate_measure"},"minProperties":1,"type":"object"},"aggregate_measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"excluded_samples":{"minimum":0,"type":"integer"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"valid_samples":{"minimum":0,"type":"integer"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","valid_samples","excluded_samples"],"type":"object"},"bandwidth":{"additionalProperties":false,"properties":{"bytes_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["measured","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["bytes_per_second","kind","source","status","reason"],"type":"object"},"clock":{"additionalProperties":false,"properties":{"hz":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["observed","base","max","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["hz","kind","source","status","reason"],"type":"object"},"condition":{"additionalProperties":false,"properties":{"condition_id":{"pattern":"^vcpu-[1-9][0-9]*$","type":"string"},"cost":{"$ref":"#/$defs/cost"},"metrics":{"anyOf":[{"$ref":"#/$defs/metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_aggregate"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetitions":{"items":{"$ref":"#/$defs/repetition"},"type":"array"},"requested_ratios":{"items":{"enum":["1/4","1/2","3/4","4/4"]},"type":"array"},"resources":{"additionalProperties":false,"properties":{"cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"memory_limit_bytes":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"memory_policy":{"type":"string"},"threads":{"minimum":0,"type":"integer"},"vcpu_count":{"minimum":1,"type":"integer"}},"required":["vcpu_count","cpu_ids","threads","memory_policy","memory_limit_bytes"],"type":"object"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["condition_id","requested_ratios","status","reason","resources","metrics","profiling","cost","repetitions"],"type":"object"},"cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method"],"type":"object"},"dashboard_artifact":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minLength":1,"type":"string"}}}}],"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"const":"path"},"value":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]}},"required":["value","unit","status","reason"],"type":"object"},"event":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"multiplex_scaled":{"anyOf":[{"type":"boolean"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"running_percent":{"anyOf":[{"maximum":100,"minimum":0,"type":"number"},{"type":"null"}]},"running_time_ns":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","running_time_ns","running_percent","multiplex_scaled"],"type":"object"},"events":{"additionalProperties":{"$ref":"#/$defs/event"},"minProperties":1,"type":"object"},"external_object":{"additionalProperties":true,"description":"Opaque upstream manifest/config or Runner snapshot; hashes validated separately.","type":"object"},"isolation":{"additionalProperties":false,"properties":{"cache_evidence":{"anyOf":[{"type":"string"},{"type":"null"}]},"cache_verified":{"type":"boolean"},"container_id":{"pattern":"^[a-f0-9]{64}$","type":"string"},"container_name":{"type":"string"},"context_length":{"minimum":1,"type":"integer"},"cpu_only_verified":{"type":"boolean"},"deleted":{"type":"boolean"},"effective_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"effective_num_thread":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"model_manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"model_read_only":{"type":"boolean"},"new_container":{"type":"boolean"},"num_thread":{"minimum":0,"type":"integer"},"preload_output_tokens":{"minimum":0,"type":"integer"},"prior_generation_requests":{"minimum":0,"type":"integer"},"process_allowed_list":{"type":"string"},"quantization":{"type":"string"}},"required":["container_id","container_name","new_container","deleted","effective_cpu_ids","process_allowed_list","num_thread","cpu_only_verified","cache_verified","cache_evidence","effective_num_thread","prior_generation_requests","preload_output_tokens","model_read_only","model_manifest_sha256","quantization","context_length"],"type":"object"},"measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason"],"type":"object"},"metrics":{"additionalProperties":false,"properties":{"aggregation":{"const":"median"},"failed_repetitions":{"minimum":0,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"parallel_efficiency":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"planned_repetitions":{"minimum":1,"type":"integer"},"speedup":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"successful_repetitions":{"minimum":0,"type":"integer"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["aggregation","planned_repetitions","successful_repetitions","failed_repetitions","output_tokens_per_second","ttft_seconds","speedup","parallel_efficiency"],"type":"object"},"os":{"additionalProperties":false,"properties":{"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version"],"type":"object"},"perf_aggregate":{"additionalProperties":false,"properties":{"aggregation":{"const":"median_of_successful_repetitions"},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/aggregate_measure"}},"required":["ipc"],"type":"object"},"events_per_second":{"$ref":"#/$defs/aggregate_events"}},"required":["cpu_id","events_per_second","derived"],"type":"object"},"type":"array"}},"required":["aggregation","per_vcpu"],"type":"object"},"perf_config":{"additionalProperties":false,"properties":{"binary":{"anyOf":[{"type":"string"},{"type":"null"}]},"events":{"additionalProperties":{"additionalProperties":false,"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["status","reason"],"type":"object"},"minProperties":1,"type":"object"},"interval_ms":{"minimum":1,"type":"integer"},"scope":{"const":"system_wide_selected_cpus"},"version":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["binary","version","events","interval_ms","scope"],"type":"object"},"perf_raw":{"additionalProperties":false,"properties":{"artifact":{"type":"string"},"collection_duration_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"collection_ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"collection_started_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/measure"}},"required":["ipc"],"type":"object"},"events":{"$ref":"#/$defs/events"}},"required":["cpu_id","events","derived"],"type":"object"},"type":"array"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"scope":{"const":"system_wide_selected_cpus"},"status":{"enum":["ok","partial","unavailable","error"]}},"required":["status","reason","scope","per_vcpu","artifact","collection_started_at","collection_ended_at","collection_duration_seconds"],"type":"object"},"raw_metrics":{"additionalProperties":false,"properties":{"decode_tokens_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"done_reason":{"type":"string"},"error_count":{"minimum":0,"type":"integer"},"first_generated_chunk_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"input_tokens":{"minimum":0,"type":"integer"},"latency_seconds":{"minimum":0,"type":"number"},"output_tokens":{"minimum":1,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"request_count":{"minimum":0,"type":"integer"},"response_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"success_count":{"minimum":0,"type":"integer"},"thinking_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"ttft_method":{"const":"first_nonempty_content_chunk"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["output_tokens","input_tokens","output_tokens_per_second","request_count","success_count","error_count","ttft_seconds","ttft_method","latency_seconds","decode_tokens_per_second","response_sha256","done_reason","thinking_sha256","first_generated_chunk_seconds"],"type":"object"},"repetition":{"additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"log":{"type":"string"},"response":{"type":"string"}},"required":["response","log"],"type":"object"},"cost":{"$ref":"#/$defs/cost"},"isolation":{"anyOf":[{"$ref":"#/$defs/isolation"},{"type":"null"}]},"metrics":{"anyOf":[{"$ref":"#/$defs/raw_metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_raw"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetition_id":{"minimum":1,"type":"integer"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]},"timing":{"$ref":"#/$defs/timing"}},"required":["repetition_id","status","reason","timing","isolation","metrics","profiling","cost","artifacts"],"type":"object"},"runner":{"additionalProperties":false,"properties":{"adapter":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"version":{"minLength":1,"type":"string"}},"required":["id","version"],"type":"object"},"contract":{"const":"runner/v1"},"identity":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"purpose":{"enum":["smoke","benchmark"]}},"required":["id","purpose"],"type":"object"},"kind":{"const":"instance"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"perf_events":{"items":{"minLength":1,"type":"string"},"minItems":1,"type":"array","uniqueItems":true},"protocol":{"const":"fresh_request_preloaded/v1"},"repetitions":{"minimum":1,"type":"integer"},"warmup_requests":{"const":0}},"required":["protocol","repetitions","concurrency","warmup_requests","perf_events"],"type":"object"},"model":{"additionalProperties":false,"properties":{"blobs":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"size_bytes":{"minimum":0,"type":"integer"},"url":{"format":"uri","pattern":"^https://","type":"string"}},"required":["digest","size_bytes","url"],"type":"object"},"minItems":1,"type":"array"},"id":{"minLength":1,"type":"string"},"manifest":{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"manifest_url":{"format":"uri","pattern":"^https://","type":"string"},"quantization":{"minLength":1,"type":"string"}},"required":["id","manifest_url","manifest_sha256","manifest","blobs","quantization"],"type":"object"},"resources":{"additionalProperties":false,"properties":{"minimum_available_memory_bytes":{"minimum":1,"type":"integer"}},"required":["minimum_available_memory_bytes"],"type":"object"},"runner_schema_version":{"const":"1.0.0"},"runtime":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64"]},"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"archive_url":{"format":"uri","pattern":"^https://","type":"string"},"base_image":{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"}},"required":["architecture","base_image","archive_url","archive_sha256"],"type":"object"},"timeouts":{"additionalProperties":false,"properties":{"cleanup_seconds":{"const":60},"preparation_seconds":{"const":3600},"repetition_seconds":{"const":3600}},"required":["preparation_seconds","repetition_seconds","cleanup_seconds"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"batch_size":{"minimum":1,"type":"integer"},"context_length":{"minimum":1,"type":"integer"},"max_output_tokens":{"minimum":1,"type":"integer"},"prompt":{"minLength":1,"type":"string"},"seed":{"minimum":0,"type":"integer"},"temperature":{"minimum":0,"type":"number"},"think":{"enum":[false,true,"low","medium","high"],"type":["boolean","string"]}},"required":["prompt","context_length","max_output_tokens","seed","temperature","batch_size","think"],"type":"object"}},"required":["runner_schema_version","contract","kind","identity","adapter","runtime","model","workload","measurement","resources","timeouts"],"type":"object"},"storage":{"additionalProperties":false,"properties":{"capacity_bytes":{"minimum":0,"type":"integer"},"hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"id":{"type":"string"},"source":{"type":"string"},"type":{"type":"string"}},"required":["id","type","capacity_bytes","hourly_rate","source"],"type":"object"},"timing":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_duration_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"measurement_ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_started_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"sequence_index":{"minimum":1,"type":"integer"},"started_at":{"format":"date-time","type":"string"}},"required":["sequence_index","started_at","ended_at","measurement_started_at","measurement_ended_at","measurement_duration_seconds"],"type":"object"},"total_cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"other_duration_seconds":{"minimum":0,"type":"number"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"shared_setup_duration_seconds":{"minimum":0,"type":"number"},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method","shared_setup_duration_seconds","other_duration_seconds"],"type":"object"}},"$id":"urn:llm-on-cpu:summary:3.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"dashboard":{"$ref":"#/$defs/dashboard_artifact"},"logs":{"type":"string"}},"required":["logs","dashboard"],"type":"object"},"cache_policy":{"additionalProperties":false,"properties":{"hardware_cache":{"type":"string"},"model_files":{"type":"string"},"page_cache":{"type":"string"},"strategy":{"type":"string"},"verification":{"type":"string"},"warmup_requests":{"minimum":0,"type":"integer"},"within_request_kv":{"type":"string"}},"required":["strategy","warmup_requests","model_files","page_cache","hardware_cache","within_request_kv","verification"],"type":"object"},"cost":{"$ref":"#/$defs/total_cost"},"environment":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64","aarch64"]},"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"aws":{"anyOf":[{"additionalProperties":false,"properties":{"ami":{"anyOf":[{"type":"string"},{"type":"null"}]},"instance_type":{"anyOf":[{"type":"string"},{"type":"null"}]},"region":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["instance_type","region","ami"],"type":"object"},{"type":"null"}]},"cpu_quota":{"anyOf":[{"type":"string"},{"type":"null"}]},"cpu_topology":{"items":{"additionalProperties":false,"properties":{"core_id":{"minimum":0,"type":"integer"},"cpu_id":{"minimum":0,"type":"integer"},"numa_node":{"minimum":0,"type":"integer"},"socket_id":{"minimum":0,"type":"integer"}},"required":["cpu_id","core_id","socket_id","numa_node"],"type":"object"},"type":"array"},"host_id":{"type":"string"},"kernel_release":{"type":"string"},"os":{"$ref":"#/$defs/os"},"provider":{"enum":["native","aws"]},"virtualization":{"additionalProperties":false,"properties":{"kind":{"enum":["wsl2","vm","bare_metal","unknown"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["kind","status","reason"],"type":"object"}},"required":["provider","host_id","architecture","os","kernel_release","virtualization","aws","cpu_topology","available_cpu_ids","cpu_quota"],"type":"object"},"execution":{"additionalProperties":false,"properties":{"container_os":{"anyOf":[{"$ref":"#/$defs/os"},{"type":"null"}]},"docker_version":{"type":"string"},"dockerfile_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"image_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"load_generator":{"type":"string"},"mode":{"type":"string"},"profile":{"enum":["experimental","production"]},"timeout_seconds":{"const":3600}},"required":["profile","mode","docker_version","image_id","dockerfile_sha256","container_os","load_generator","timeout_seconds"],"type":"object"},"framework":{"additionalProperties":false,"properties":{"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"backend":{"const":"cpu"},"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version","backend","archive_sha256"],"type":"object"},"model":{"additionalProperties":false,"properties":{"format":{"type":"string"},"id":{"type":"string"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"quantization":{"type":"string"}},"required":["id","manifest_sha256","quantization","format"],"type":"object"},"platform":{"additionalProperties":false,"properties":{"cpu":{"additionalProperties":false,"properties":{"clock":{"$ref":"#/$defs/clock"},"name":{"type":"string"}},"required":["name","clock"],"type":"object"},"memory":{"additionalProperties":false,"properties":{"available_bytes_at_start":{"minimum":0,"type":"integer"},"bandwidth":{"$ref":"#/$defs/bandwidth"},"capacity_bytes":{"minimum":0,"type":"integer"}},"required":["capacity_bytes","available_bytes_at_start","bandwidth"],"type":"object"},"name":{"type":"string"},"vcpu_count":{"minimum":0,"type":"integer"}},"required":["name","vcpu_count","cpu","memory"],"type":"object"},"pricing":{"additionalProperties":false,"properties":{"compute_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"storage":{"items":{"$ref":"#/$defs/storage"},"type":"array"},"storage_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","compute_hourly_rate","storage_hourly_rate","total_hourly_rate","storage"],"type":"object"},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_config"},{"type":"null"}]},"performix":{"$ref":"#/$defs/measure"}},"required":["perf","performix"],"type":"object"},"run":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"errors":{"items":{"additionalProperties":false,"properties":{"code":{"enum":[2,10,20,30,31,32,40,50,130]},"condition_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"message":{"type":"string"},"phase":{"type":"string"}},"required":["code","phase","message","condition_id"],"type":"object"},"type":"array"},"exit_code":{"anyOf":[{"enum":[0,2,10,20,30,31,32,40,50,130]},{"type":"null"}]},"id":{"type":"string"},"started_at":{"format":"date-time","type":"string"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["id","started_at","ended_at","status","exit_code","errors"],"type":"object"},"scaling":{"additionalProperties":false,"properties":{"plan":{"additionalProperties":false,"properties":{"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"base_nproc":{"minimum":1,"type":"integer"},"baseline_condition_id":{"type":"string"},"cpu_selection":{"type":"string"},"requested_ratios":{"const":["1/4","1/2","3/4","4/4"]},"rounding":{"type":"string"},"sequence_seed":{"minimum":0,"type":"integer"}},"required":["base_nproc","available_cpu_ids","requested_ratios","baseline_condition_id","rounding","cpu_selection","sequence_seed"],"type":"object"},"results":{"items":{"$ref":"#/$defs/condition"},"type":"array"}},"required":["plan","results"],"type":"object"},"schema_version":{"const":"3.0.0"},"toolchain":{"additionalProperties":false,"properties":{"compiler":{"$ref":"#/$defs/measure"},"distribution":{"type":"string"},"python_version":{"type":"string"}},"required":["distribution","compiler","python_version"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"prompt_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"runner_config":{"$ref":"#/$defs/runner"},"runner_id":{"type":"string"},"runner_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"}},"required":["runner_id","runner_sha256","runner_config","prompt_sha256"],"type":"object"}},"required":["schema_version","run","environment","platform","toolchain","framework","model","workload","execution","cache_policy","profiling","pricing","cost","scaling","artifacts"],"title":"llm_on_cpu summary 3.0.0","type":"object"}
````

</details>

<details>
<summary>specs/compat/summary-3.1.schema.json</summary>

<!-- artifact path="specs/compat/summary-3.1.schema.json" sha256="8279e5114d477b94d6a5b06a04f4b283f88ac7db021a6b4393ebb730240f7665" canonical="json" -->

````json
{"$defs":{"aggregate_events":{"additionalProperties":{"$ref":"#/$defs/aggregate_measure"},"minProperties":1,"type":"object"},"aggregate_measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"excluded_samples":{"minimum":0,"type":"integer"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"valid_samples":{"minimum":0,"type":"integer"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","valid_samples","excluded_samples"],"type":"object"},"bandwidth":{"additionalProperties":false,"properties":{"bytes_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["measured","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["bytes_per_second","kind","source","status","reason"],"type":"object"},"clock":{"additionalProperties":false,"properties":{"hz":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["observed","base","max","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["hz","kind","source","status","reason"],"type":"object"},"condition":{"additionalProperties":false,"properties":{"condition_id":{"pattern":"^vcpu-[1-9][0-9]*$","type":"string"},"cost":{"$ref":"#/$defs/cost"},"metrics":{"anyOf":[{"$ref":"#/$defs/metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_aggregate"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetitions":{"items":{"$ref":"#/$defs/repetition"},"type":"array"},"requested_ratios":{"items":{"enum":["1/4","1/2","3/4","4/4"]},"type":"array"},"resources":{"additionalProperties":false,"properties":{"cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"memory_limit_bytes":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"memory_policy":{"type":"string"},"threads":{"minimum":0,"type":"integer"},"vcpu_count":{"minimum":1,"type":"integer"}},"required":["vcpu_count","cpu_ids","threads","memory_policy","memory_limit_bytes"],"type":"object"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["condition_id","requested_ratios","status","reason","resources","metrics","profiling","cost","repetitions"],"type":"object"},"cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method"],"type":"object"},"dashboard_artifact":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minLength":1,"type":"string"}}}}],"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"const":"path"},"value":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]}},"required":["value","unit","status","reason"],"type":"object"},"event":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"multiplex_scaled":{"anyOf":[{"type":"boolean"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"running_percent":{"anyOf":[{"maximum":100,"minimum":0,"type":"number"},{"type":"null"}]},"running_time_ns":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","running_time_ns","running_percent","multiplex_scaled"],"type":"object"},"events":{"additionalProperties":{"$ref":"#/$defs/event"},"minProperties":1,"type":"object"},"external_object":{"additionalProperties":true,"description":"Opaque upstream manifest/config or Runner snapshot; hashes validated separately.","type":"object"},"isolation":{"additionalProperties":false,"properties":{"cache_evidence":{"anyOf":[{"type":"string"},{"type":"null"}]},"cache_verified":{"type":"boolean"},"container_id":{"pattern":"^[a-f0-9]{64}$","type":"string"},"container_name":{"type":"string"},"context_length":{"minimum":1,"type":"integer"},"cpu_only_verified":{"type":"boolean"},"deleted":{"type":"boolean"},"effective_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"effective_num_thread":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"model_manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"model_read_only":{"type":"boolean"},"new_container":{"type":"boolean"},"num_thread":{"minimum":0,"type":"integer"},"preload_output_tokens":{"minimum":0,"type":"integer"},"prior_generation_requests":{"minimum":0,"type":"integer"},"process_allowed_list":{"type":"string"},"quantization":{"type":"string"}},"required":["container_id","container_name","new_container","deleted","effective_cpu_ids","process_allowed_list","num_thread","cpu_only_verified","cache_verified","cache_evidence","effective_num_thread","prior_generation_requests","preload_output_tokens","model_read_only","model_manifest_sha256","quantization","context_length"],"type":"object"},"measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason"],"type":"object"},"metrics":{"additionalProperties":false,"properties":{"aggregation":{"const":"median"},"failed_repetitions":{"minimum":0,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"parallel_efficiency":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"planned_repetitions":{"minimum":1,"type":"integer"},"speedup":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"successful_repetitions":{"minimum":0,"type":"integer"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["aggregation","planned_repetitions","successful_repetitions","failed_repetitions","output_tokens_per_second","ttft_seconds","speedup","parallel_efficiency"],"type":"object"},"os":{"additionalProperties":false,"properties":{"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version"],"type":"object"},"perf_aggregate":{"additionalProperties":false,"properties":{"aggregation":{"const":"median_of_successful_repetitions"},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/aggregate_measure"}},"required":["ipc"],"type":"object"},"events_per_second":{"$ref":"#/$defs/aggregate_events"}},"required":["cpu_id","events_per_second","derived"],"type":"object"},"type":"array"}},"required":["aggregation","per_vcpu"],"type":"object"},"perf_config":{"additionalProperties":false,"properties":{"binary":{"anyOf":[{"type":"string"},{"type":"null"}]},"events":{"additionalProperties":{"additionalProperties":false,"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["status","reason"],"type":"object"},"minProperties":1,"type":"object"},"interval_ms":{"minimum":1,"type":"integer"},"scope":{"const":"system_wide_selected_cpus"},"version":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["binary","version","events","interval_ms","scope"],"type":"object"},"perf_raw":{"additionalProperties":false,"properties":{"artifact":{"type":"string"},"collection_duration_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"collection_ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"collection_started_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/measure"}},"required":["ipc"],"type":"object"},"events":{"$ref":"#/$defs/events"}},"required":["cpu_id","events","derived"],"type":"object"},"type":"array"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"scope":{"const":"system_wide_selected_cpus"},"status":{"enum":["ok","partial","unavailable","error"]}},"required":["status","reason","scope","per_vcpu","artifact","collection_started_at","collection_ended_at","collection_duration_seconds"],"type":"object"},"raw_metrics":{"additionalProperties":false,"properties":{"decode_tokens_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"done_reason":{"type":"string"},"error_count":{"minimum":0,"type":"integer"},"first_generated_chunk_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"input_tokens":{"minimum":0,"type":"integer"},"latency_seconds":{"minimum":0,"type":"number"},"output_tokens":{"minimum":1,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"request_count":{"minimum":0,"type":"integer"},"response_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"success_count":{"minimum":0,"type":"integer"},"thinking_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"ttft_method":{"const":"first_nonempty_content_chunk"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["output_tokens","input_tokens","output_tokens_per_second","request_count","success_count","error_count","ttft_seconds","ttft_method","latency_seconds","decode_tokens_per_second","response_sha256","done_reason","thinking_sha256","first_generated_chunk_seconds"],"type":"object"},"repetition":{"additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"log":{"type":"string"},"response":{"type":"string"}},"required":["response","log"],"type":"object"},"cost":{"$ref":"#/$defs/cost"},"isolation":{"anyOf":[{"$ref":"#/$defs/isolation"},{"type":"null"}]},"metrics":{"anyOf":[{"$ref":"#/$defs/raw_metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_raw"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetition_id":{"minimum":1,"type":"integer"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]},"timing":{"$ref":"#/$defs/timing"}},"required":["repetition_id","status","reason","timing","isolation","metrics","profiling","cost","artifacts"],"type":"object"},"runner":{"additionalProperties":false,"properties":{"adapter":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"version":{"minLength":1,"type":"string"}},"required":["id","version"],"type":"object"},"contract":{"const":"runner/v1"},"identity":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"purpose":{"enum":["smoke","benchmark"]}},"required":["id","purpose"],"type":"object"},"kind":{"const":"instance"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"perf_events":{"items":{"minLength":1,"type":"string"},"minItems":1,"type":"array","uniqueItems":true},"protocol":{"const":"fresh_request_preloaded/v1"},"repetitions":{"minimum":1,"type":"integer"},"warmup_requests":{"const":0}},"required":["protocol","repetitions","concurrency","warmup_requests","perf_events"],"type":"object"},"model":{"additionalProperties":false,"properties":{"blobs":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"size_bytes":{"minimum":0,"type":"integer"},"url":{"format":"uri","pattern":"^https://","type":"string"}},"required":["digest","size_bytes","url"],"type":"object"},"minItems":1,"type":"array"},"id":{"minLength":1,"type":"string"},"manifest":{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"manifest_url":{"format":"uri","pattern":"^https://","type":"string"},"quantization":{"minLength":1,"type":"string"}},"required":["id","manifest_url","manifest_sha256","manifest","blobs","quantization"],"type":"object"},"resources":{"additionalProperties":false,"properties":{"minimum_available_memory_bytes":{"minimum":1,"type":"integer"}},"required":["minimum_available_memory_bytes"],"type":"object"},"runner_schema_version":{"enum":["1.0.0","1.1.0"]},"runtime":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64"]},"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"archive_url":{"format":"uri","pattern":"^https://","type":"string"},"base_image":{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"}},"required":["architecture","base_image","archive_url","archive_sha256"],"type":"object"},"timeouts":{"additionalProperties":false,"properties":{"cleanup_seconds":{"const":60},"preparation_seconds":{"const":3600},"repetition_seconds":{"const":3600}},"required":["preparation_seconds","repetition_seconds","cleanup_seconds"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"batch_size":{"minimum":1,"type":"integer"},"context_length":{"minimum":1,"type":"integer"},"max_output_tokens":{"minimum":1,"type":"integer"},"prompt":{"minLength":1,"type":"string"},"seed":{"minimum":0,"type":"integer"},"temperature":{"minimum":0,"type":"number"},"template_date":{"anyOf":[{"format":"date","pattern":"^\\d{4}-\\d{2}-\\d{2}$","type":"string"},{"type":"null"}]},"think":{"enum":[false,true,"low","medium","high"],"type":["boolean","string"]}},"required":["prompt","context_length","max_output_tokens","seed","temperature","batch_size","think"],"type":"object"}},"required":["runner_schema_version","contract","kind","identity","adapter","runtime","model","workload","measurement","resources","timeouts"],"type":"object"},"storage":{"additionalProperties":false,"properties":{"capacity_bytes":{"minimum":0,"type":"integer"},"hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"id":{"type":"string"},"source":{"type":"string"},"type":{"type":"string"}},"required":["id","type","capacity_bytes","hourly_rate","source"],"type":"object"},"timing":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_duration_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"measurement_ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_started_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"sequence_index":{"minimum":1,"type":"integer"},"started_at":{"format":"date-time","type":"string"}},"required":["sequence_index","started_at","ended_at","measurement_started_at","measurement_ended_at","measurement_duration_seconds"],"type":"object"},"total_cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"other_duration_seconds":{"minimum":0,"type":"number"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"shared_setup_duration_seconds":{"minimum":0,"type":"number"},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method","shared_setup_duration_seconds","other_duration_seconds"],"type":"object"}},"$id":"urn:llm-on-cpu:summary:3.1.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"dashboard":{"$ref":"#/$defs/dashboard_artifact"},"logs":{"type":"string"}},"required":["logs","dashboard"],"type":"object"},"cache_policy":{"additionalProperties":false,"properties":{"hardware_cache":{"type":"string"},"model_files":{"type":"string"},"page_cache":{"type":"string"},"strategy":{"type":"string"},"verification":{"type":"string"},"warmup_requests":{"minimum":0,"type":"integer"},"within_request_kv":{"type":"string"}},"required":["strategy","warmup_requests","model_files","page_cache","hardware_cache","within_request_kv","verification"],"type":"object"},"cost":{"$ref":"#/$defs/total_cost"},"environment":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64","aarch64"]},"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"aws":{"anyOf":[{"additionalProperties":false,"properties":{"ami":{"anyOf":[{"type":"string"},{"type":"null"}]},"instance_type":{"anyOf":[{"type":"string"},{"type":"null"}]},"region":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["instance_type","region","ami"],"type":"object"},{"type":"null"}]},"cpu_quota":{"anyOf":[{"type":"string"},{"type":"null"}]},"cpu_topology":{"items":{"additionalProperties":false,"properties":{"core_id":{"minimum":0,"type":"integer"},"cpu_id":{"minimum":0,"type":"integer"},"numa_node":{"minimum":0,"type":"integer"},"socket_id":{"minimum":0,"type":"integer"}},"required":["cpu_id","core_id","socket_id","numa_node"],"type":"object"},"type":"array"},"host_id":{"type":"string"},"kernel_release":{"type":"string"},"os":{"$ref":"#/$defs/os"},"provider":{"enum":["native","aws"]},"virtualization":{"additionalProperties":false,"properties":{"kind":{"enum":["wsl2","vm","bare_metal","unknown"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["kind","status","reason"],"type":"object"}},"required":["provider","host_id","architecture","os","kernel_release","virtualization","aws","cpu_topology","available_cpu_ids","cpu_quota"],"type":"object"},"execution":{"additionalProperties":false,"properties":{"container_os":{"anyOf":[{"$ref":"#/$defs/os"},{"type":"null"}]},"docker_version":{"type":"string"},"dockerfile_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"image_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"load_generator":{"type":"string"},"mode":{"type":"string"},"profile":{"enum":["experimental","production"]},"timeout_seconds":{"const":3600}},"required":["profile","mode","docker_version","image_id","dockerfile_sha256","container_os","load_generator","timeout_seconds"],"type":"object"},"framework":{"additionalProperties":false,"properties":{"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"backend":{"const":"cpu"},"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version","backend","archive_sha256"],"type":"object"},"model":{"additionalProperties":false,"properties":{"format":{"type":"string"},"id":{"type":"string"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"quantization":{"type":"string"}},"required":["id","manifest_sha256","quantization","format"],"type":"object"},"platform":{"additionalProperties":false,"properties":{"cpu":{"additionalProperties":false,"properties":{"clock":{"$ref":"#/$defs/clock"},"name":{"type":"string"}},"required":["name","clock"],"type":"object"},"memory":{"additionalProperties":false,"properties":{"available_bytes_at_start":{"minimum":0,"type":"integer"},"bandwidth":{"$ref":"#/$defs/bandwidth"},"capacity_bytes":{"minimum":0,"type":"integer"}},"required":["capacity_bytes","available_bytes_at_start","bandwidth"],"type":"object"},"name":{"type":"string"},"vcpu_count":{"minimum":0,"type":"integer"}},"required":["name","vcpu_count","cpu","memory"],"type":"object"},"pricing":{"additionalProperties":false,"properties":{"compute_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"storage":{"items":{"$ref":"#/$defs/storage"},"type":"array"},"storage_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","compute_hourly_rate","storage_hourly_rate","total_hourly_rate","storage"],"type":"object"},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_config"},{"type":"null"}]},"performix":{"$ref":"#/$defs/measure"}},"required":["perf","performix"],"type":"object"},"run":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"errors":{"items":{"additionalProperties":false,"properties":{"code":{"enum":[2,10,20,30,31,32,40,50,130]},"condition_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"message":{"type":"string"},"phase":{"type":"string"}},"required":["code","phase","message","condition_id"],"type":"object"},"type":"array"},"exit_code":{"anyOf":[{"enum":[0,2,10,20,30,31,32,40,50,130]},{"type":"null"}]},"id":{"type":"string"},"started_at":{"format":"date-time","type":"string"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["id","started_at","ended_at","status","exit_code","errors"],"type":"object"},"scaling":{"additionalProperties":false,"properties":{"plan":{"additionalProperties":false,"properties":{"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"base_nproc":{"minimum":1,"type":"integer"},"baseline_condition_id":{"type":"string"},"cpu_selection":{"type":"string"},"requested_ratios":{"const":["1/4","1/2","3/4","4/4"]},"rounding":{"type":"string"},"sequence_seed":{"minimum":0,"type":"integer"}},"required":["base_nproc","available_cpu_ids","requested_ratios","baseline_condition_id","rounding","cpu_selection","sequence_seed"],"type":"object"},"results":{"items":{"$ref":"#/$defs/condition"},"type":"array"}},"required":["plan","results"],"type":"object"},"schema_version":{"const":"3.1.0"},"toolchain":{"additionalProperties":false,"properties":{"compiler":{"$ref":"#/$defs/measure"},"distribution":{"type":"string"},"python_version":{"type":"string"}},"required":["distribution","compiler","python_version"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"prompt_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"runner_config":{"$ref":"#/$defs/runner"},"runner_id":{"type":"string"},"runner_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"}},"required":["runner_id","runner_sha256","runner_config","prompt_sha256"],"type":"object"}},"required":["schema_version","run","environment","platform","toolchain","framework","model","workload","execution","cache_policy","profiling","pricing","cost","scaling","artifacts"],"title":"CPU LLM benchmark summary 3.1.0","type":"object"}
````

</details>

<details>
<summary>specs/measurement-protocol.md</summary>

<!-- artifact path="specs/measurement-protocol.md" sha256="67a9354921d7e0f30a2e96a01fabdb22977e0bf39afb2c1f8a78c43cb13eaad3" canonical="text" -->

````text
# 測定・集計プロトコル

契約 ID：`fresh_request_preloaded/v1`。モデルや Framework に依存しない計測・集計の規則である。Runner はこの ID を指定し、計算式・計測境界・失敗扱いを変更してはならない。

## 計測の状態遷移

`validate → prepare → start → verify → measure → collect → stop → aggregate → validate_result → report`

prepare は固定配布物の準備、verify は空プロンプトによるモデルロードとモデル同一性・CPU制限の検証を含む。measure 前の生成要求は0回。モデルのロードのみを先行させ、実行する生成リクエストは反復あたり1回、同時実行1とする。stop は失敗時も必須。新しいプロセス・専用書込領域を各条件・各反復で作成する。

実行順序は反復ごとに条件一覧のコピーを `random.Random(seed + repetition_id).shuffle` 相当で並べ替え、実際の sequence_index を保存する。順序の完全な再現には保存した順序を用いる。

## 時刻・出力・集計

UTC の記録時刻と monotonic の経過時間を区別する。リクエスト送信開始から最終完了応答の受信までを性能測定区間とする。生成上限でなく、APIが返す実生成トークン数を使用する。

- output_tokens_per_second：thinking を含む eval_count / 性能測定区間秒。
- ttft_seconds：最初の非空 **回答**チャンクまで。回答がなければ null。
- first_generated_chunk_seconds：thinking または回答の最初の非空チャンクまで。
- decode_tokens_per_second：API 内部の eval_duration に基づく別指標。共通 Token/s の代用にしない。
- response_sha256 / thinking_sha256：それぞれの文字列を受信順に連結した UTF-8 の SHA-256。チャンク境界や JSON の空白を含めない。
- 条件の性能集計：成功反復の中央値。失敗値を0として平均せず、予定/成功/失敗件数を別保存する。
- speedup：最小の実測 vCPU 条件に対する性能比。parallel_efficiency：speedup / vCPU 数比。

EOS は正常終了。thinking のみで上限に達した場合も実生成量を保存し、存在しない回答TTFTを作らない。think=falseでthinkingが出た場合は設定違反として失敗する。タイムアウト・API error・完了応答欠落・生成数ゼロは失敗として保存する。

## perf の同期と集計

ホストの選択 CPU の system-wide 計測を使用する。ロード・起動は計測に含めない。計測開始の準備完了を確認してから推論を送信し、終了後に停止・回収する。開始/終了に制御上の差がある場合は実際の区間を記録し、完全同期したと偽らない。1秒区間の差分と最後の短い区間を保存し、最終総計を二重加算しない。

反復ごと・CPUごとのカウンタを保持する。条件間比較用のイベント率は各反復の値/計測秒の中央値、IPCは各反復内で求めた比率の中央値。計測区間が異なる場合は推論秒をカウンタの分母に代用しない。権限不足は unavailable、収集処理未実装は not_implemented、解析失敗は error。

## タイムアウト・再試行・後始末

共通準備に合計3600秒、各反復に3600秒の絶対締切。チャンク受信で延長しない。後始末は最大60秒。測定リクエストは再送しない。再試行が必要なら新規コンテナと別反復として記録する。所有コンテナだけを削除し、後始末失敗時は次条件へ進めない。

以下は vCPU 選択、キャッシュと通常測定の共通規則。将来のウォームアップ方式・コールドスタート方式は別プロトコル ID として定義し、v1 の結果と同一系列に混ぜない。

### vCPU スケーリング測定

CPU 制限を適用する前に取得した `nproc` を基準 `N` とし、各インスタンスで以下の 4 条件を測定する。vCPU は Linux の論理 CPU として扱い、物理コア数とは区別する。

| 条件 | 使用 vCPU 数 K | N = 16 の例 |
| --- | --- | --- |
| 1/4 | `max(1, floor(N / 4))` | 4 |
| 1/2 | `max(1, floor(N / 2))` | 8 |
| 3/4 | `max(1, floor(3 * N / 4))` | 12 |
| 4/4 | `N` | 16 |

- `nproc` はベンチマーク用のスレッド数環境変数や affinity を設定する前に取得する。ホストのオンライン CPU 数、利用可能 CPU ID、既存の cpuset・CPU quota も記録し、意図しない事前制限を検出する。
- 端数は切り捨て、最小 1 vCPU とする。使用数が重複する場合は一度だけ測定し、対応する比率をすべて記録する。
- 利用可能 CPU のトポロジーから固定の選択順序を作り、先頭 K 個を使用する。小さい条件の CPU 集合を大きい条件に含め、CPU ID が連番であるとは仮定しない。
- 初期の選択方針は NUMA ノード・ソケット順に物理コアを並べ、各コアの最初の SMT スレッドを先に選び、その後に兄弟スレッドを追加する。CPU ID、コア、ソケット、NUMA、SMT 構成と選択方針を保存する。メモリ配置方針も固定・記録する。
- cpuset / affinity で推論サービスと全ワーカーを選択 CPU に制限する。Framework のスレッド設定も K に合わせ、設定名・要求値・実効値を記録する。CPU quota のみで使用 vCPU 数を代用しない。
- 各条件・各反復で新規コンテナを作成し、CPU 制限と選択モードのキャッシュ分離を検証する。A/B の fresh_request_preloaded ではロードのみを事前実施し、推論ウォームアップは行わない。定常推論モードを将来追加する場合のみ、キャッシュ無効化を検証したウォームアップを行う。モデル・量子化・入力・生成条件・同時実行数・測定回数は固定する。
- 負荷生成は可能なら別ホストで行う。同一ホストの場合は配置と競合を記録し、4/4 条件だけ推論用 CPU を減らさない。
- 実行順序と反復番号を保存する。最小の実測 vCPU 数 `K0` を基準に、スループット向上率 `T(K) / T(K0)` と並列効率 `(T(K) / T(K0)) / (K / K0)` を算出する。1/4 条件を 1 vCPU 基準とは扱わない。

### コンテナとキャッシュの分離方針

**採用方針：イメージを一度ビルドし、スケーリング条件・反復ごとに新規コンテナを作成・破棄する。** 本プロジェクトで Framework 別 Dockerfile を提供し、ホスト上で対象アーキテクチャ向けにビルドする。実行中のコンテナや推論プロセス、書き込み可能なキャッシュ領域は使い回さない。

ビルドは Framework・アーキテクチャ・固定依存関係の組み合わせにつき一度とし、1/4・1/2・3/4・4/4 の全条件で同じイメージを使用する。各条件では起動時の CPU 割り当てとスレッド設定を変更し、再ビルドは行わない。Dockerfile や依存関係を変更した場合にのみ新しいイメージをビルドする。

Docker は同じイメージから作成したコンテナごとに書き込み層を作るため、実行状態の分離に毎回のイメージ再ビルドは必要ない。一方、外部ボリュームの内容はコンテナ削除後も残り得るため、共有範囲を明示的に制限する。[Docker storage drivers](https://docs.docker.com/engine/storage/drivers/)、[Docker volumes](https://docs.docker.com/engine/storage/volumes/)

| 方式 | 評価・採用方針 |
| --- | --- |
| 毎条件でイメージを再ビルド | ビルド時間が増え、ホストのページキャッシュも消去できない。依存関係・Dockerfile の変更時のみ実施 |
| 固定イメージから毎回新規コンテナ | 標準方式。環境を固定しながら推論プロセスと書き込み状態を分離できる |
| ホスト上でプロセス再起動＋毎回専用ディレクトリ | 軽量な代替案。ただし依存関係・子プロセス・保存先の管理が複雑になるため、初期実装では採用しない |
| 毎条件でインスタンス再作成・再起動 | 起動・環境構築を含む検証向け。通常の推論スケーリングには時間がかかるため採用しない |

#### 除外するキャッシュと維持する状態

「キャッシュなし」は **過去のリクエスト・測定による推論結果の再利用なし**を意味する。生成中に必要な同一リクエスト内の KV cache や CPU ハードウェアキャッシュまで無効にすることは求めない。

| 種類 | 標準測定での方針 |
| --- | --- |
| リクエスト間の KV / prefix / prompt / response cache、会話状態 | 無効化または確実に消去し、ウォームアップや前のリクエストから再利用しない |
| 同一リクエスト内の KV cache | 通常の推論処理として許容し、設定を固定 |
| モデル重み・トークナイザなど不変の配布物 | 一度取得し、チェックサム付きの読み取り専用領域として再利用 |
| Framework の実行時キャッシュ・JIT 成果物・一時ファイル | コンテナごとに空の専用領域を用意。必要な初期化は測定前に行い、条件間では共有しない |
| ホスト OS のページキャッシュ | コンテナ新設では消えない。v1 はモデルロードのみ先行し、事前生成は0回。ロード時間を除外 |
| CPU の L1 / L2 / LLC、TLB | 完全消去を保証せず、測定モード共通の準備と実行順序管理で条件をそろえる |

vLLM の prefix caching は過去の共通プレフィックスの計算を再利用する機能なので、採用バージョンで無効化設定と実効値を検証する。[vLLM Automatic Prefix Caching](https://docs.vllm.ai/en/v0.13.0/features/automatic_prefix_caching/)

Ollama を含め、キャッシュ制御の設定名・API・適用範囲は固定バージョンごとに Runner で検証する。新規コンテナだけでは、その中のウォームアップや複数リクエスト間の再利用を防げない。異なるプロンプトでも共通のシステム文などが再利用され得るため、入力を変更するだけで無効化できたとは判断しない。

無効化・消去の確実な方法がない Runner は、各測定リクエスト（同時実行時は独立した各ワーカー）について新規推論プロセスを用意し、先行する推論リクエストを送らずに測定する別モードを使用する。この場合はモデルロード・初回初期化の扱いを記録し、通常のウォームアップ後の結果と混ぜない。代替方式も検証できなければ、その Runner はキャッシュ再利用なしの測定を未対応とする。

#### 標準実行手順

1. ホスト OS を運用区分に従わせ、コンテナの Ubuntu 26.04 と依存関係を固定し、Framework・アーキテクチャごとにイメージを一度ビルドする。コンテナはホストのカーネルを使用するため、本番間のホスト OS 統一を継続し、実験との差異を記録する。
2. モデルを事前取得して検証する。イメージの ID / digest、Dockerfile のハッシュ、モデルのチェックサムを保存する。ビルド・ダウンロードは推論計測に含めない。
3. ホストで `nproc` と CPU トポロジーを取得し、4 条件の CPU 集合を確定する。測定順序は反復ごとに順序を入れ替え、seed と順序を保存する。
4. 各条件・反復に一意のコンテナと書き込み領域を新設する。モデル領域だけを読み取り専用で共有し、ホーム・一時領域・Framework キャッシュは共有しない。書き込みが必要なモデル管理情報は専用領域に分離する。
5. `--cpuset-cpus` 相当で CPU を割り当て、メモリ配置方針・メモリ上限・スワップ方針・共有メモリ設定をそろえる。CPU quota だけでスケーリングしない。キャッシュ無効化を設定してサービスを起動する。
6. モデルロードと正常性確認を実施する。A/B は事前の生成要求を送らず、定常推論モードではウォームアップのキャッシュを除去したことを検証してから、perf と推論計測を開始する。入力セットと順序は各 vCPU 条件で同一にする。
7. ログ・perf・結果をホストの実行別ディレクトリに保存し、コンテナと専用書き込み領域を削除する。次の反復でも新規作成する。既存コンテナの `restart` は代用にしない。

perf はホスト側で取得し、対象コンテナの CPU ID と対応付ける。計測範囲は従来どおり選択 CPU のシステム全体とし、ビルド・ダウンロード・コンテナ作成を測定区間に重ねない。

キャッシュ除外の検証では、同一入力を繰り返した際のキャッシュヒット数や実際に処理した入力トークン数などを、取得可能なログ・メトリクスで確認する。遅延の一致だけを証拠にしない。確認方法・結果・確認できない範囲を保存し、未検証の測定をキャッシュ再利用なしと断定しない。初回 Runner はログの `cached n_tokens = 0` と compute thread 数も照合し、`isolation.cache_evidence` と `effective_num_thread` に記録する。

#### コールドスタートを測る場合

OS ページキャッシュも冷えた状態からのモデルロード性能を測りたい場合は、別の `cold_start` モードとする。専用ホストで前の推論プロセスを終了したうえで、ホスト側の clean page cache の解放などを行い、ロード・起動時間を別指標として計測する。`drop_caches` はホスト全体に作用し、全キャッシュ層の消去を保証しないため、標準の定常推論モードでは実施しない。[Linux drop_caches](https://kernel.org/doc/html/v6.7/admin-guide/sysctl/vm.html)

## 再現性監査

固定 Runner の完全な内容、重み/配布物digest、入力/テンプレート、CPU集合・実行順序を照合する。seedだけで出力のビット一致や性能値の一致は保証しない。日時・環境変数等を読むテンプレートは Adapter 仕様に従い固定し、確認不能なら停止する。

スモークの1反復は動作確認であり、性能の分散・優劣を断定する根拠としない。同一条件の別runを再実行し、構成と検証証跡の再現を確認する。Token/s の差をゼロにするために結果を補正しない。統計的な比較に必要な反復数の変更は別 Runner として固定し、既存の測定条件を後から書き換えない。

再実行では出力・thinkingハッシュ、入力/生成トークン数、CPU制限、キャッシュ証跡、タイムアウト、終了コード、Dashboard入力ハッシュ、残留コンテナを監査する。ハッシュ不一致そのものを不正と断定せず、入力・数値計算・停止理由・設定差を調査する。修正前の失敗runを削除・成功へ上書きしない。

Ollamaのキャッシュ証跡はAdapter仕様の要求境界で評価する。新規要求開始時の再利用なしと、同一要求内のKV利用を区別する。ログの全カウンタをゼロにすることを目標としない。

## 性能値のばらつき判定（quality/v1）

WSL実走行では、同一Runner・同一出力でも単発のToken/sが約半分になる条件が観測された。構成・出力の再現と、所要時間の安定を分けて評価する。周波数の事前スナップショットだけで原因を熱・電源・競合等に断定しない。

条件ごとの成功反復のToken/sについて、最小値、最大値、中央値、および `(最大値−最小値)/中央値` を保存する。品質判定は `quality/v1` とし、最低5成功反復、相対幅の上限0.20を固定する。この閾値は本プロジェクトの検査方針であり、統計的信頼区間や一般的な標準ではない。

- 5成功反復未満：`insufficient_samples`。単発スモークも推論・契約検証は成功にできるが、性能の安定性は未評価。
- 5成功反復以上かつ相対幅が0.20以下：`within_threshold`。このrun内で閾値内だったという意味に限定し、別run・別ホストの性能一致を保証しない。
- 5成功反復以上かつ相対幅が0.20を超える：`outside_threshold`。中央値を隠さず全反復とばらつきを表示し、安定した比較結果として採用しない。

品質判定を満たすために失敗・遅い反復を捨てたり、Runnerを自動変更したり、成功するまで繰り返したりしない。閾値外でも正しく計測・保存できたrunの終了コードは0とし、性能品質の状態は別項目で明示する。

追加確認用の固定Runnerは `specs/runners/ollama-qwen3-stability.json`。小型スモークと重み・量子化・context・入力・生成設定を一致させ、反復数だけを変える。各反復で新規コンテナを使用する。本番性能評価の代替とはしない。
````

</details>

<details>
<summary>specs/ollama-adapter.md</summary>

<!-- artifact path="specs/ollama-adapter.md" sha256="cbcb1b7ba64a85b5e5c6f6182ed964d70fb65989fd649b79153802580abfdf0c" canonical="text" -->

````text
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
````

</details>

<details>
<summary>specs/runner-contract.md</summary>

<!-- artifact path="specs/runner-contract.md" sha256="bdbf69b18f33eceabed95dcd75bbb567a5a1e262bc59ce07e546f8f552e3d09f" canonical="text" -->

````text
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
````

</details>

<details>
<summary>specs/runner.schema.json</summary>

<!-- artifact path="specs/runner.schema.json" sha256="bae68a3d1d9b41349e37195ea615683e631d215e4989788a1b493eb119e17b27" canonical="json" -->

````json
{"$id":"urn:llm-on-cpu:runner:1.1.0","$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":[{"additionalProperties":false,"properties":{"adapter":{"additionalProperties":false,"properties":{"id":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]},"version":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]}},"required":["id","version"],"type":"object"},"contract":{"const":"runner/v1"},"identity":{"additionalProperties":false,"properties":{"id":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]},"purpose":{"anyOf":[{"enum":["smoke","benchmark"]},{"type":"null"}]}},"required":["id","purpose"],"type":"object"},"kind":{"const":"template"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"perf_events":{"anyOf":[{"items":{"minLength":1,"type":"string"},"minItems":1,"type":"array","uniqueItems":true},{"type":"null"}]},"protocol":{"const":"fresh_request_preloaded/v1"},"repetitions":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]},"warmup_requests":{"const":0}},"required":["protocol","repetitions","concurrency","warmup_requests","perf_events"],"type":"object"},"model":{"additionalProperties":false,"properties":{"blobs":{"anyOf":[{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"size_bytes":{"minimum":0,"type":"integer"},"url":{"format":"uri","pattern":"^https://","type":"string"}},"required":["digest","size_bytes","url"],"type":"object"},"minItems":1,"type":"array"},{"type":"null"}]},"id":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]},"manifest":{"anyOf":[{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},{"type":"null"}]},"manifest_sha256":{"anyOf":[{"pattern":"^[a-f0-9]{64}$","type":"string"},{"type":"null"}]},"manifest_url":{"anyOf":[{"format":"uri","pattern":"^https://","type":"string"},{"type":"null"}]},"quantization":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]}},"required":["id","manifest_url","manifest_sha256","manifest","blobs","quantization"],"type":"object"},"resources":{"additionalProperties":false,"properties":{"minimum_available_memory_bytes":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]}},"required":["minimum_available_memory_bytes"],"type":"object"},"runner_schema_version":{"enum":["1.0.0","1.1.0"]},"runtime":{"additionalProperties":false,"properties":{"architecture":{"anyOf":[{"enum":["x86_64","arm64"]},{"type":"null"}]},"archive_sha256":{"anyOf":[{"pattern":"^[a-f0-9]{64}$","type":"string"},{"type":"null"}]},"archive_url":{"anyOf":[{"format":"uri","pattern":"^https://","type":"string"},{"type":"null"}]},"base_image":{"anyOf":[{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"},{"type":"null"}]}},"required":["architecture","base_image","archive_url","archive_sha256"],"type":"object"},"timeouts":{"additionalProperties":false,"properties":{"cleanup_seconds":{"const":60},"preparation_seconds":{"const":3600},"repetition_seconds":{"const":3600}},"required":["preparation_seconds","repetition_seconds","cleanup_seconds"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"batch_size":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]},"context_length":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]},"max_output_tokens":{"anyOf":[{"minimum":1,"type":"integer"},{"type":"null"}]},"prompt":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]},"seed":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"temperature":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"template_date":{"anyOf":[{"format":"date","pattern":"^\\d{4}-\\d{2}-\\d{2}$","type":"string"},{"type":"null"}]},"think":{"anyOf":[{"enum":[false,true,"low","medium","high"],"type":["boolean","string"]},{"type":"null"}]}},"required":["prompt","context_length","max_output_tokens","seed","temperature","batch_size","think"],"type":"object"}},"required":["runner_schema_version","contract","kind","identity","adapter","runtime","model","workload","measurement","resources","timeouts"],"type":"object"},{"additionalProperties":false,"properties":{"adapter":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"version":{"minLength":1,"type":"string"}},"required":["id","version"],"type":"object"},"contract":{"const":"runner/v1"},"identity":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"purpose":{"enum":["smoke","benchmark"]}},"required":["id","purpose"],"type":"object"},"kind":{"const":"instance"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"perf_events":{"items":{"minLength":1,"type":"string"},"minItems":1,"type":"array","uniqueItems":true},"protocol":{"const":"fresh_request_preloaded/v1"},"repetitions":{"minimum":1,"type":"integer"},"warmup_requests":{"const":0}},"required":["protocol","repetitions","concurrency","warmup_requests","perf_events"],"type":"object"},"model":{"additionalProperties":false,"properties":{"blobs":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"size_bytes":{"minimum":0,"type":"integer"},"url":{"format":"uri","pattern":"^https://","type":"string"}},"required":["digest","size_bytes","url"],"type":"object"},"minItems":1,"type":"array"},"id":{"minLength":1,"type":"string"},"manifest":{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"manifest_url":{"format":"uri","pattern":"^https://","type":"string"},"quantization":{"minLength":1,"type":"string"}},"required":["id","manifest_url","manifest_sha256","manifest","blobs","quantization"],"type":"object"},"resources":{"additionalProperties":false,"properties":{"minimum_available_memory_bytes":{"minimum":1,"type":"integer"}},"required":["minimum_available_memory_bytes"],"type":"object"},"runner_schema_version":{"enum":["1.0.0","1.1.0"]},"runtime":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64"]},"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"archive_url":{"format":"uri","pattern":"^https://","type":"string"},"base_image":{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"}},"required":["architecture","base_image","archive_url","archive_sha256"],"type":"object"},"timeouts":{"additionalProperties":false,"properties":{"cleanup_seconds":{"const":60},"preparation_seconds":{"const":3600},"repetition_seconds":{"const":3600}},"required":["preparation_seconds","repetition_seconds","cleanup_seconds"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"batch_size":{"minimum":1,"type":"integer"},"context_length":{"minimum":1,"type":"integer"},"max_output_tokens":{"minimum":1,"type":"integer"},"prompt":{"minLength":1,"type":"string"},"seed":{"minimum":0,"type":"integer"},"temperature":{"minimum":0,"type":"number"},"template_date":{"anyOf":[{"format":"date","pattern":"^\\d{4}-\\d{2}-\\d{2}$","type":"string"},{"type":"null"}]},"think":{"enum":[false,true,"low","medium","high"],"type":["boolean","string"]}},"required":["prompt","context_length","max_output_tokens","seed","temperature","batch_size","think"],"type":"object"}},"required":["runner_schema_version","contract","kind","identity","adapter","runtime","model","workload","measurement","resources","timeouts"],"type":"object"}]}
````

</details>

<details>
<summary>specs/runner.template.json</summary>

<!-- artifact path="specs/runner.template.json" sha256="29a5c49c34ededea55b0a83f47f02e03370c2218b4a3db1fa9a22f1a9bcc3c7e" canonical="json" -->

````json
{"adapter":{"id":null,"version":null},"contract":"runner/v1","identity":{"id":null,"purpose":null},"kind":"template","measurement":{"concurrency":1,"perf_events":null,"protocol":"fresh_request_preloaded/v1","repetitions":null,"warmup_requests":0},"model":{"blobs":null,"id":null,"manifest":null,"manifest_sha256":null,"manifest_url":null,"quantization":null},"resources":{"minimum_available_memory_bytes":null},"runner_schema_version":"1.1.0","runtime":{"architecture":null,"archive_sha256":null,"archive_url":null,"base_image":null},"timeouts":{"cleanup_seconds":60,"preparation_seconds":3600,"repetition_seconds":3600},"workload":{"batch_size":null,"context_length":null,"max_output_tokens":null,"prompt":null,"seed":null,"temperature":null,"template_date":null,"think":null}}
````

</details>

<details>
<summary>specs/runners/ollama-gpt-oss-20b.json</summary>

<!-- artifact path="specs/runners/ollama-gpt-oss-20b.json" sha256="4ea86f1ce3e60322742b5297e13091dc4414491ebf83c7e0849b482ab2202d41" canonical="json" -->

````json
{"adapter":{"id":"ollama","version":"0.40.5"},"contract":"runner/v1","identity":{"id":"ollama-gpt-oss-20b","purpose":"smoke"},"kind":"instance","measurement":{"concurrency":1,"perf_events":["cpu-clock","context-switches","cpu-migrations","page-faults","cycles","instructions","branches","branch-misses","cache-references","cache-misses"],"protocol":"fresh_request_preloaded/v1","repetitions":1,"warmup_requests":0},"model":{"blobs":[{"digest":"sha256:e103573196b6deeff79ec124b4131b4fad700cee60b584a8f9d689ffed115038","size_bytes":139,"url":"https://registry.ollama.ai/v2/library/gpt-oss/blobs/sha256:e103573196b6deeff79ec124b4131b4fad700cee60b584a8f9d689ffed115038"},{"digest":"sha256:8ecb5d4ad6172c63f9cbf1a07a04e525985a8a11a6e516da02b674c4010de716","size_bytes":13793422816,"url":"https://registry.ollama.ai/v2/library/gpt-oss/blobs/sha256:8ecb5d4ad6172c63f9cbf1a07a04e525985a8a11a6e516da02b674c4010de716"},{"digest":"sha256:fa6710a93d78da62641e192361344be7a8c0a1c3737f139cf89f20ce1626b99c","size_bytes":7240,"url":"https://registry.ollama.ai/v2/library/gpt-oss/blobs/sha256:fa6710a93d78da62641e192361344be7a8c0a1c3737f139cf89f20ce1626b99c"},{"digest":"sha256:f60356777647e927149cbd4c0ec1314a90caba9400ad205ddc4ce47ed001c2d6","size_bytes":11353,"url":"https://registry.ollama.ai/v2/library/gpt-oss/blobs/sha256:f60356777647e927149cbd4c0ec1314a90caba9400ad205ddc4ce47ed001c2d6"},{"digest":"sha256:d8ba2f9a17b3bbdeb5690efaa409b3fcb0b56296a777c7a69c78aa33bbddf182","size_bytes":18,"url":"https://registry.ollama.ai/v2/library/gpt-oss/blobs/sha256:d8ba2f9a17b3bbdeb5690efaa409b3fcb0b56296a777c7a69c78aa33bbddf182"}],"id":"gpt-oss:20b","manifest":{"config":{"digest":"sha256:e103573196b6deeff79ec124b4131b4fad700cee60b584a8f9d689ffed115038","mediaType":"application/vnd.docker.container.image.v1+json","size":139},"format":"gguf","layers":[{"digest":"sha256:8ecb5d4ad6172c63f9cbf1a07a04e525985a8a11a6e516da02b674c4010de716","from":"dhiltgen/gpt-oss:20b-llamacpp","mediaType":"application/vnd.ollama.image.model","size":13793422816},{"digest":"sha256:fa6710a93d78da62641e192361344be7a8c0a1c3737f139cf89f20ce1626b99c","from":"dhiltgen/gpt-oss:20b-llamacpp","mediaType":"application/vnd.ollama.image.template","size":7240},{"digest":"sha256:f60356777647e927149cbd4c0ec1314a90caba9400ad205ddc4ce47ed001c2d6","from":"dhiltgen/gpt-oss:20b-llamacpp","mediaType":"application/vnd.ollama.image.license","size":11353},{"digest":"sha256:d8ba2f9a17b3bbdeb5690efaa409b3fcb0b56296a777c7a69c78aa33bbddf182","from":"dhiltgen/gpt-oss:20b-llamacpp","mediaType":"application/vnd.ollama.image.params","size":18}],"mediaType":"application/vnd.docker.distribution.manifest.v2+json","runner":"llamacpp","schemaVersion":2},"manifest_sha256":"f38aa0c53da5f8c49d08c43a99df24ff53167fe68e24664a7777288e7656fdfe","manifest_url":"https://registry.ollama.ai/v2/library/gpt-oss/manifests/20b","quantization":"MXFP4"},"resources":{"minimum_available_memory_bytes":19327352832},"runner_schema_version":"1.1.0","runtime":{"architecture":"x86_64","archive_sha256":"dc5eabc292f9949546c90a97c820f924b035e05243b0de13c7f366182562169c","archive_url":"https://github.com/ollama/ollama/releases/download/v0.40.5/ollama-linux-amd64.tar.zst","base_image":"ubuntu@sha256:678c6550cc43645e08669028bc177f50be4e7c5b8cca677067b1914d4afc7a03"},"timeouts":{"cleanup_seconds":60,"preparation_seconds":3600,"repetition_seconds":3600},"workload":{"batch_size":128,"context_length":2048,"max_output_tokens":128,"prompt":"Explain how a CPU executes a program. Describe instruction fetching, decoding, execution, registers, and memory access in clear English. Write a detailed explanation of approximately 200 words.","seed":42,"temperature":0,"template_date":"2026-10-17","think":"low"}}
````

</details>

<details>
<summary>specs/runners/ollama-qwen3-30b-a3b.json</summary>

<!-- artifact path="specs/runners/ollama-qwen3-30b-a3b.json" sha256="03c5c6bf6355fbedb6d976defcd3a55ea1bcd7ef7e067d67a7c23990fdcfd593" canonical="json" -->

````json
{"adapter":{"id":"ollama","version":"0.40.5"},"contract":"runner/v1","identity":{"id":"ollama-qwen3-30b-a3b","purpose":"smoke"},"kind":"instance","measurement":{"concurrency":1,"perf_events":["cpu-clock","context-switches","cpu-migrations","page-faults","cycles","instructions","branches","branch-misses","cache-references","cache-misses"],"protocol":"fresh_request_preloaded/v1","repetitions":1,"warmup_requests":0},"model":{"blobs":[{"digest":"sha256:3cdc64c2b371af88ae18b4cdac63d1097f76a8f6fd23d785aaaaa02c59450d61","size_bytes":494,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:3cdc64c2b371af88ae18b4cdac63d1097f76a8f6fd23d785aaaaa02c59450d61"},{"digest":"sha256:58574f2e94b99fb9e4391408b57e5aeaaaec10f6384e9a699fc2cb43a5c8eabf","size_bytes":18556685856,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:58574f2e94b99fb9e4391408b57e5aeaaaec10f6384e9a699fc2cb43a5c8eabf"},{"digest":"sha256:2d54db2b9bb29ce7db54fea63a891f5859603813c555b1f88b5e0994652897f9","size_bytes":1506,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:2d54db2b9bb29ce7db54fea63a891f5859603813c555b1f88b5e0994652897f9"},{"digest":"sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12","size_bytes":11338,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12"},{"digest":"sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb","size_bytes":120,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb"}],"id":"qwen3:30b-a3b","manifest":{"config":{"digest":"sha256:3cdc64c2b371af88ae18b4cdac63d1097f76a8f6fd23d785aaaaa02c59450d61","mediaType":"application/vnd.docker.container.image.v1+json","size":494},"layers":[{"digest":"sha256:58574f2e94b99fb9e4391408b57e5aeaaaec10f6384e9a699fc2cb43a5c8eabf","mediaType":"application/vnd.ollama.image.model","size":18556685856},{"digest":"sha256:2d54db2b9bb29ce7db54fea63a891f5859603813c555b1f88b5e0994652897f9","mediaType":"application/vnd.ollama.image.template","size":1506},{"digest":"sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12","mediaType":"application/vnd.ollama.image.license","size":11338},{"digest":"sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb","mediaType":"application/vnd.ollama.image.params","size":120}],"mediaType":"application/vnd.docker.distribution.manifest.v2+json","schemaVersion":2},"manifest_sha256":"ad815644918f0eaab341c12b67837cc6dd4562342cdaf118f83d5d554cb37226","manifest_url":"https://registry.ollama.ai/v2/library/qwen3/manifests/30b-a3b","quantization":"Q4_K_M"},"resources":{"minimum_available_memory_bytes":23622320128},"runner_schema_version":"1.1.0","runtime":{"architecture":"x86_64","archive_sha256":"dc5eabc292f9949546c90a97c820f924b035e05243b0de13c7f366182562169c","archive_url":"https://github.com/ollama/ollama/releases/download/v0.40.5/ollama-linux-amd64.tar.zst","base_image":"ubuntu@sha256:678c6550cc43645e08669028bc177f50be4e7c5b8cca677067b1914d4afc7a03"},"timeouts":{"cleanup_seconds":60,"preparation_seconds":3600,"repetition_seconds":3600},"workload":{"batch_size":128,"context_length":2048,"max_output_tokens":128,"prompt":"Explain how a CPU executes a program. Describe instruction fetching, decoding, execution, registers, and memory access in clear English. Write a detailed explanation of approximately 200 words.","seed":42,"temperature":0,"think":false}}
````

</details>

<details>
<summary>specs/runners/ollama-qwen3-smoke.json</summary>

<!-- artifact path="specs/runners/ollama-qwen3-smoke.json" sha256="4d145f86a0ca4ef2c9b351e8ac7761779cc076c7aee260b7d1e6ea2f15a12ed5" canonical="json" -->

````json
{"adapter":{"id":"ollama","version":"0.40.5"},"contract":"runner/v1","identity":{"id":"ollama-qwen3-smoke","purpose":"smoke"},"kind":"instance","measurement":{"concurrency":1,"perf_events":["cpu-clock","context-switches","cpu-migrations","page-faults","cycles","instructions","branches","branch-misses","cache-references","cache-misses"],"protocol":"fresh_request_preloaded/v1","repetitions":1,"warmup_requests":0},"model":{"blobs":[{"digest":"sha256:b0830f4ff6a0220cfd995455206353b0ed23c0aee865218b154b7a75087b4e55","size_bytes":490,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:b0830f4ff6a0220cfd995455206353b0ed23c0aee865218b154b7a75087b4e55"},{"digest":"sha256:7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa","size_bytes":522640096,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa"},{"digest":"sha256:ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4","size_bytes":1723,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4"},{"digest":"sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12","size_bytes":11338,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12"},{"digest":"sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb","size_bytes":120,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb"}],"id":"qwen3:0.6b","manifest":{"config":{"digest":"sha256:b0830f4ff6a0220cfd995455206353b0ed23c0aee865218b154b7a75087b4e55","mediaType":"application/vnd.docker.container.image.v1+json","size":490},"layers":[{"digest":"sha256:7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa","mediaType":"application/vnd.ollama.image.model","size":522640096},{"digest":"sha256:ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4","mediaType":"application/vnd.ollama.image.template","size":1723},{"digest":"sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12","mediaType":"application/vnd.ollama.image.license","size":11338},{"digest":"sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb","mediaType":"application/vnd.ollama.image.params","size":120}],"mediaType":"application/vnd.docker.distribution.manifest.v2+json","schemaVersion":2},"manifest_sha256":"7df6b6e09427a769808717c0a93cadc4ae99ed4eb8bf5ca557c90846becea435","manifest_url":"https://registry.ollama.ai/v2/library/qwen3/manifests/0.6b","quantization":"Q4_K_M"},"resources":{"minimum_available_memory_bytes":2147483648},"runner_schema_version":"1.1.0","runtime":{"architecture":"x86_64","archive_sha256":"dc5eabc292f9949546c90a97c820f924b035e05243b0de13c7f366182562169c","archive_url":"https://github.com/ollama/ollama/releases/download/v0.40.5/ollama-linux-amd64.tar.zst","base_image":"ubuntu@sha256:678c6550cc43645e08669028bc177f50be4e7c5b8cca677067b1914d4afc7a03"},"timeouts":{"cleanup_seconds":60,"preparation_seconds":3600,"repetition_seconds":3600},"workload":{"batch_size":128,"context_length":2048,"max_output_tokens":128,"prompt":"Explain how a CPU executes a program. Describe instruction fetching, decoding, execution, registers, and memory access in clear English. Write a detailed explanation of approximately 200 words.","seed":42,"temperature":0,"think":false}}
````

</details>

<details>
<summary>specs/runners/ollama-qwen3-stability.json</summary>

<!-- artifact path="specs/runners/ollama-qwen3-stability.json" sha256="f1ff023bca2050e48c9221eb089d5c05b73d7d0cb2cda40ab6d8e6d9e8996f71" canonical="json" -->

````json
{"adapter":{"id":"ollama","version":"0.40.5"},"contract":"runner/v1","identity":{"id":"ollama-qwen3-stability","purpose":"benchmark"},"kind":"instance","measurement":{"concurrency":1,"perf_events":["cpu-clock","context-switches","cpu-migrations","page-faults","cycles","instructions","branches","branch-misses","cache-references","cache-misses"],"protocol":"fresh_request_preloaded/v1","repetitions":5,"warmup_requests":0},"model":{"blobs":[{"digest":"sha256:b0830f4ff6a0220cfd995455206353b0ed23c0aee865218b154b7a75087b4e55","size_bytes":490,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:b0830f4ff6a0220cfd995455206353b0ed23c0aee865218b154b7a75087b4e55"},{"digest":"sha256:7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa","size_bytes":522640096,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa"},{"digest":"sha256:ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4","size_bytes":1723,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4"},{"digest":"sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12","size_bytes":11338,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12"},{"digest":"sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb","size_bytes":120,"url":"https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb"}],"id":"qwen3:0.6b","manifest":{"config":{"digest":"sha256:b0830f4ff6a0220cfd995455206353b0ed23c0aee865218b154b7a75087b4e55","mediaType":"application/vnd.docker.container.image.v1+json","size":490},"layers":[{"digest":"sha256:7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa","mediaType":"application/vnd.ollama.image.model","size":522640096},{"digest":"sha256:ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4","mediaType":"application/vnd.ollama.image.template","size":1723},{"digest":"sha256:d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12","mediaType":"application/vnd.ollama.image.license","size":11338},{"digest":"sha256:cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb","mediaType":"application/vnd.ollama.image.params","size":120}],"mediaType":"application/vnd.docker.distribution.manifest.v2+json","schemaVersion":2},"manifest_sha256":"7df6b6e09427a769808717c0a93cadc4ae99ed4eb8bf5ca557c90846becea435","manifest_url":"https://registry.ollama.ai/v2/library/qwen3/manifests/0.6b","quantization":"Q4_K_M"},"resources":{"minimum_available_memory_bytes":2147483648},"runner_schema_version":"1.1.0","runtime":{"architecture":"x86_64","archive_sha256":"dc5eabc292f9949546c90a97c820f924b035e05243b0de13c7f366182562169c","archive_url":"https://github.com/ollama/ollama/releases/download/v0.40.5/ollama-linux-amd64.tar.zst","base_image":"ubuntu@sha256:678c6550cc43645e08669028bc177f50be4e7c5b8cca677067b1914d4afc7a03"},"timeouts":{"cleanup_seconds":60,"preparation_seconds":3600,"repetition_seconds":3600},"workload":{"batch_size":128,"context_length":2048,"max_output_tokens":128,"prompt":"Explain how a CPU executes a program. Describe instruction fetching, decoding, execution, registers, and memory access in clear English. Write a detailed explanation of approximately 200 words.","seed":42,"temperature":0,"think":false}}
````

</details>

<details>
<summary>specs/summary-format.md</summary>

<!-- artifact path="specs/summary-format.md" sha256="3c2b18dec10b02e4af69b25af3adf27694388e512bddcb0d86b9c534020ee5a0" canonical="text" -->

````text
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
- Schema から作る合成サンプルと実測データを区別する。型・必須性は内包 Schema に従い、検証用サンプルは再生成時に作成する。


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
````

</details>

<details>
<summary>specs/summary.schema.json</summary>

<!-- artifact path="specs/summary.schema.json" sha256="61646de922f8b2c4f9d0f33ba06fc338d5fd7dcfaa02bab2de51a017b738da38" canonical="json" -->

````json
{"$defs":{"aggregate_events":{"additionalProperties":{"$ref":"#/$defs/aggregate_measure"},"minProperties":1,"type":"object"},"aggregate_measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"excluded_samples":{"minimum":0,"type":"integer"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"valid_samples":{"minimum":0,"type":"integer"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","valid_samples","excluded_samples"],"type":"object"},"bandwidth":{"additionalProperties":false,"properties":{"bytes_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["measured","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["bytes_per_second","kind","source","status","reason"],"type":"object"},"clock":{"additionalProperties":false,"properties":{"hz":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"kind":{"enum":["observed","base","max","published"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"source":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["hz","kind","source","status","reason"],"type":"object"},"condition":{"additionalProperties":false,"properties":{"condition_id":{"pattern":"^vcpu-[1-9][0-9]*$","type":"string"},"cost":{"$ref":"#/$defs/cost"},"metrics":{"anyOf":[{"$ref":"#/$defs/metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_aggregate"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetitions":{"items":{"$ref":"#/$defs/repetition"},"type":"array"},"requested_ratios":{"items":{"enum":["1/4","1/2","3/4","4/4"]},"type":"array"},"resources":{"additionalProperties":false,"properties":{"cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"memory_limit_bytes":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"memory_policy":{"type":"string"},"threads":{"minimum":0,"type":"integer"},"vcpu_count":{"minimum":1,"type":"integer"}},"required":["vcpu_count","cpu_ids","threads","memory_policy","memory_limit_bytes"],"type":"object"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["condition_id","requested_ratios","status","reason","resources","metrics","profiling","cost","repetitions"],"type":"object"},"cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method"],"type":"object"},"dashboard_artifact":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minLength":1,"type":"string"}}}}],"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"const":"path"},"value":{"anyOf":[{"minLength":1,"type":"string"},{"type":"null"}]}},"required":["value","unit","status","reason"],"type":"object"},"event":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"multiplex_scaled":{"anyOf":[{"type":"boolean"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"running_percent":{"anyOf":[{"maximum":100,"minimum":0,"type":"number"},{"type":"null"}]},"running_time_ns":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason","running_time_ns","running_percent","multiplex_scaled"],"type":"object"},"events":{"additionalProperties":{"$ref":"#/$defs/event"},"minProperties":1,"type":"object"},"external_object":{"additionalProperties":true,"description":"Opaque upstream manifest/config or Runner snapshot; hashes validated separately.","type":"object"},"isolation":{"additionalProperties":false,"properties":{"cache_evidence":{"anyOf":[{"type":"string"},{"type":"null"}]},"cache_verified":{"type":"boolean"},"container_id":{"pattern":"^[a-f0-9]{64}$","type":"string"},"container_name":{"type":"string"},"context_length":{"minimum":1,"type":"integer"},"cpu_only_verified":{"type":"boolean"},"deleted":{"type":"boolean"},"effective_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"effective_num_thread":{"anyOf":[{"minimum":0,"type":"integer"},{"type":"null"}]},"model_manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"model_read_only":{"type":"boolean"},"new_container":{"type":"boolean"},"num_thread":{"minimum":0,"type":"integer"},"preload_output_tokens":{"minimum":0,"type":"integer"},"prior_generation_requests":{"minimum":0,"type":"integer"},"process_allowed_list":{"type":"string"},"quantization":{"type":"string"}},"required":["container_id","container_name","new_container","deleted","effective_cpu_ids","process_allowed_list","num_thread","cpu_only_verified","cache_verified","cache_evidence","effective_num_thread","prior_generation_requests","preload_output_tokens","model_read_only","model_manifest_sha256","quantization","context_length"],"type":"object"},"measure":{"additionalProperties":false,"allOf":[{"else":{"properties":{"reason":{"minLength":1,"type":"string"},"value":{"type":"null"}}},"if":{"properties":{"status":{"const":"ok"}}},"then":{"properties":{"reason":{"type":"null"},"value":{"minimum":0,"type":"number"}}}}],"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"unit":{"type":"string"},"value":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["value","unit","status","reason"],"type":"object"},"metrics":{"additionalProperties":false,"properties":{"aggregation":{"const":"median"},"failed_repetitions":{"minimum":0,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"parallel_efficiency":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"planned_repetitions":{"minimum":1,"type":"integer"},"quality":{"$ref":"#/$defs/quality"},"speedup":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"successful_repetitions":{"minimum":0,"type":"integer"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["aggregation","planned_repetitions","successful_repetitions","failed_repetitions","output_tokens_per_second","ttft_seconds","speedup","parallel_efficiency"],"type":"object"},"os":{"additionalProperties":false,"properties":{"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version"],"type":"object"},"perf_aggregate":{"additionalProperties":false,"properties":{"aggregation":{"const":"median_of_successful_repetitions"},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/aggregate_measure"}},"required":["ipc"],"type":"object"},"events_per_second":{"$ref":"#/$defs/aggregate_events"}},"required":["cpu_id","events_per_second","derived"],"type":"object"},"type":"array"}},"required":["aggregation","per_vcpu"],"type":"object"},"perf_config":{"additionalProperties":false,"properties":{"binary":{"anyOf":[{"type":"string"},{"type":"null"}]},"events":{"additionalProperties":{"additionalProperties":false,"properties":{"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["status","reason"],"type":"object"},"minProperties":1,"type":"object"},"interval_ms":{"minimum":1,"type":"integer"},"scope":{"const":"system_wide_selected_cpus"},"version":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["binary","version","events","interval_ms","scope"],"type":"object"},"perf_raw":{"additionalProperties":false,"properties":{"artifact":{"type":"string"},"collection_duration_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"collection_ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"collection_started_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"per_vcpu":{"items":{"additionalProperties":false,"properties":{"cpu_id":{"minimum":0,"type":"integer"},"derived":{"additionalProperties":false,"properties":{"ipc":{"$ref":"#/$defs/measure"}},"required":["ipc"],"type":"object"},"events":{"$ref":"#/$defs/events"}},"required":["cpu_id","events","derived"],"type":"object"},"type":"array"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"scope":{"const":"system_wide_selected_cpus"},"status":{"enum":["ok","partial","unavailable","error"]}},"required":["status","reason","scope","per_vcpu","artifact","collection_started_at","collection_ended_at","collection_duration_seconds"],"type":"object"},"quality":{"additionalProperties":false,"properties":{"maximum_tokens_per_second":{"exclusiveMinimum":0,"type":"number"},"minimum_samples":{"const":5},"minimum_tokens_per_second":{"exclusiveMinimum":0,"type":"number"},"policy":{"const":"quality/v1"},"relative_spread":{"minimum":0,"type":"number"},"relative_spread_limit":{"const":0.2},"sample_count":{"minimum":1,"type":"integer"},"status":{"enum":["insufficient_samples","within_threshold","outside_threshold"]}},"required":["policy","status","sample_count","minimum_samples","relative_spread_limit","minimum_tokens_per_second","maximum_tokens_per_second","relative_spread"],"type":"object"},"raw_metrics":{"additionalProperties":false,"properties":{"decode_tokens_per_second":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"done_reason":{"type":"string"},"error_count":{"minimum":0,"type":"integer"},"first_generated_chunk_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"input_tokens":{"minimum":0,"type":"integer"},"latency_seconds":{"minimum":0,"type":"number"},"output_tokens":{"minimum":1,"type":"integer"},"output_tokens_per_second":{"minimum":0,"type":"number"},"request_count":{"minimum":0,"type":"integer"},"response_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"success_count":{"minimum":0,"type":"integer"},"thinking_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"ttft_method":{"const":"first_nonempty_content_chunk"},"ttft_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]}},"required":["output_tokens","input_tokens","output_tokens_per_second","request_count","success_count","error_count","ttft_seconds","ttft_method","latency_seconds","decode_tokens_per_second","response_sha256","done_reason","thinking_sha256","first_generated_chunk_seconds"],"type":"object"},"repetition":{"additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"log":{"type":"string"},"response":{"type":"string"}},"required":["response","log"],"type":"object"},"cost":{"$ref":"#/$defs/cost"},"isolation":{"anyOf":[{"$ref":"#/$defs/isolation"},{"type":"null"}]},"metrics":{"anyOf":[{"$ref":"#/$defs/raw_metrics"},{"type":"null"}]},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_raw"},{"type":"null"}]}},"required":["perf"],"type":"object"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"repetition_id":{"minimum":1,"type":"integer"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]},"timing":{"$ref":"#/$defs/timing"}},"required":["repetition_id","status","reason","timing","isolation","metrics","profiling","cost","artifacts"],"type":"object"},"runner":{"additionalProperties":false,"properties":{"adapter":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"version":{"minLength":1,"type":"string"}},"required":["id","version"],"type":"object"},"contract":{"const":"runner/v1"},"identity":{"additionalProperties":false,"properties":{"id":{"minLength":1,"type":"string"},"purpose":{"enum":["smoke","benchmark"]}},"required":["id","purpose"],"type":"object"},"kind":{"const":"instance"},"measurement":{"additionalProperties":false,"properties":{"concurrency":{"const":1},"perf_events":{"items":{"minLength":1,"type":"string"},"minItems":1,"type":"array","uniqueItems":true},"protocol":{"const":"fresh_request_preloaded/v1"},"repetitions":{"minimum":1,"type":"integer"},"warmup_requests":{"const":0}},"required":["protocol","repetitions","concurrency","warmup_requests","perf_events"],"type":"object"},"model":{"additionalProperties":false,"properties":{"blobs":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"size_bytes":{"minimum":0,"type":"integer"},"url":{"format":"uri","pattern":"^https://","type":"string"}},"required":["digest","size_bytes","url"],"type":"object"},"minItems":1,"type":"array"},"id":{"minLength":1,"type":"string"},"manifest":{"additionalProperties":false,"properties":{"config":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"format":{"type":"string"},"layers":{"items":{"additionalProperties":false,"properties":{"digest":{"pattern":"^sha256:[a-f0-9]{64}$","type":"string"},"from":{"type":"string"},"mediaType":{"type":"string"},"size":{"minimum":0,"type":"integer"}},"required":["mediaType","digest","size"],"type":"object"},"type":"array"},"mediaType":{"type":"string"},"runner":{"type":"string"},"schemaVersion":{"const":2}},"required":["schemaVersion","mediaType","config","layers"],"type":"object"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"manifest_url":{"format":"uri","pattern":"^https://","type":"string"},"quantization":{"minLength":1,"type":"string"}},"required":["id","manifest_url","manifest_sha256","manifest","blobs","quantization"],"type":"object"},"resources":{"additionalProperties":false,"properties":{"minimum_available_memory_bytes":{"minimum":1,"type":"integer"}},"required":["minimum_available_memory_bytes"],"type":"object"},"runner_schema_version":{"enum":["1.0.0","1.1.0"]},"runtime":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64"]},"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"archive_url":{"format":"uri","pattern":"^https://","type":"string"},"base_image":{"pattern":"^ubuntu@sha256:[a-f0-9]{64}$","type":"string"}},"required":["architecture","base_image","archive_url","archive_sha256"],"type":"object"},"timeouts":{"additionalProperties":false,"properties":{"cleanup_seconds":{"const":60},"preparation_seconds":{"const":3600},"repetition_seconds":{"const":3600}},"required":["preparation_seconds","repetition_seconds","cleanup_seconds"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"batch_size":{"minimum":1,"type":"integer"},"context_length":{"minimum":1,"type":"integer"},"max_output_tokens":{"minimum":1,"type":"integer"},"prompt":{"minLength":1,"type":"string"},"seed":{"minimum":0,"type":"integer"},"temperature":{"minimum":0,"type":"number"},"template_date":{"anyOf":[{"format":"date","pattern":"^\\d{4}-\\d{2}-\\d{2}$","type":"string"},{"type":"null"}]},"think":{"enum":[false,true,"low","medium","high"],"type":["boolean","string"]}},"required":["prompt","context_length","max_output_tokens","seed","temperature","batch_size","think"],"type":"object"}},"required":["runner_schema_version","contract","kind","identity","adapter","runtime","model","workload","measurement","resources","timeouts"],"type":"object"},"storage":{"additionalProperties":false,"properties":{"capacity_bytes":{"minimum":0,"type":"integer"},"hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"id":{"type":"string"},"source":{"type":"string"},"type":{"type":"string"}},"required":["id","type","capacity_bytes","hourly_rate","source"],"type":"object"},"timing":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_duration_seconds":{"anyOf":[{"minimum":0,"type":"number"},{"type":"null"}]},"measurement_ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"measurement_started_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"sequence_index":{"minimum":1,"type":"integer"},"started_at":{"format":"date-time","type":"string"}},"required":["sequence_index","started_at","ended_at","measurement_started_at","measurement_ended_at","measurement_duration_seconds"],"type":"object"},"total_cost":{"additionalProperties":false,"properties":{"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"duration_seconds":{"minimum":0,"type":"number"},"estimated_amount":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"method":{"const":"hourly_rate_times_elapsed"},"other_duration_seconds":{"minimum":0,"type":"number"},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"shared_setup_duration_seconds":{"minimum":0,"type":"number"},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","total_hourly_rate","duration_seconds","estimated_amount","method","shared_setup_duration_seconds","other_duration_seconds"],"type":"object"}},"$id":"urn:llm-on-cpu:summary:3.2.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifacts":{"additionalProperties":false,"properties":{"dashboard":{"$ref":"#/$defs/dashboard_artifact"},"logs":{"type":"string"}},"required":["logs","dashboard"],"type":"object"},"cache_policy":{"additionalProperties":false,"properties":{"hardware_cache":{"type":"string"},"model_files":{"type":"string"},"page_cache":{"type":"string"},"strategy":{"type":"string"},"verification":{"type":"string"},"warmup_requests":{"minimum":0,"type":"integer"},"within_request_kv":{"type":"string"}},"required":["strategy","warmup_requests","model_files","page_cache","hardware_cache","within_request_kv","verification"],"type":"object"},"cost":{"$ref":"#/$defs/total_cost"},"environment":{"additionalProperties":false,"properties":{"architecture":{"enum":["x86_64","arm64","aarch64"]},"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"aws":{"anyOf":[{"additionalProperties":false,"properties":{"ami":{"anyOf":[{"type":"string"},{"type":"null"}]},"instance_type":{"anyOf":[{"type":"string"},{"type":"null"}]},"region":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["instance_type","region","ami"],"type":"object"},{"type":"null"}]},"cpu_quota":{"anyOf":[{"type":"string"},{"type":"null"}]},"cpu_topology":{"items":{"additionalProperties":false,"properties":{"core_id":{"minimum":0,"type":"integer"},"cpu_id":{"minimum":0,"type":"integer"},"numa_node":{"minimum":0,"type":"integer"},"socket_id":{"minimum":0,"type":"integer"}},"required":["cpu_id","core_id","socket_id","numa_node"],"type":"object"},"type":"array"},"host_id":{"type":"string"},"kernel_release":{"type":"string"},"os":{"$ref":"#/$defs/os"},"provider":{"enum":["native","aws"]},"virtualization":{"additionalProperties":false,"properties":{"kind":{"enum":["wsl2","vm","bare_metal","unknown"]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]}},"required":["kind","status","reason"],"type":"object"}},"required":["provider","host_id","architecture","os","kernel_release","virtualization","aws","cpu_topology","available_cpu_ids","cpu_quota"],"type":"object"},"execution":{"additionalProperties":false,"properties":{"container_os":{"anyOf":[{"$ref":"#/$defs/os"},{"type":"null"}]},"docker_version":{"type":"string"},"dockerfile_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"image_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"load_generator":{"type":"string"},"mode":{"type":"string"},"profile":{"enum":["experimental","production"]},"timeout_seconds":{"const":3600}},"required":["profile","mode","docker_version","image_id","dockerfile_sha256","container_os","load_generator","timeout_seconds"],"type":"object"},"framework":{"additionalProperties":false,"properties":{"archive_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"backend":{"const":"cpu"},"name":{"type":"string"},"version":{"type":"string"}},"required":["name","version","backend","archive_sha256"],"type":"object"},"model":{"additionalProperties":false,"properties":{"format":{"type":"string"},"id":{"type":"string"},"manifest_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"quantization":{"type":"string"}},"required":["id","manifest_sha256","quantization","format"],"type":"object"},"platform":{"additionalProperties":false,"properties":{"cpu":{"additionalProperties":false,"properties":{"clock":{"$ref":"#/$defs/clock"},"name":{"type":"string"}},"required":["name","clock"],"type":"object"},"memory":{"additionalProperties":false,"properties":{"available_bytes_at_start":{"minimum":0,"type":"integer"},"bandwidth":{"$ref":"#/$defs/bandwidth"},"capacity_bytes":{"minimum":0,"type":"integer"}},"required":["capacity_bytes","available_bytes_at_start","bandwidth"],"type":"object"},"name":{"type":"string"},"vcpu_count":{"minimum":0,"type":"integer"}},"required":["name","vcpu_count","cpu","memory"],"type":"object"},"pricing":{"additionalProperties":false,"properties":{"compute_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"currency":{"anyOf":[{"type":"string"},{"type":"null"}]},"reason":{"anyOf":[{"type":"string"},{"type":"null"}]},"status":{"enum":["ok","not_implemented","unavailable","not_applicable","disabled","error"]},"storage":{"items":{"$ref":"#/$defs/storage"},"type":"array"},"storage_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]},"total_hourly_rate":{"anyOf":[{"pattern":"^\\d+(\\.\\d+)?$","type":"string"},{"type":"null"}]}},"required":["status","reason","currency","compute_hourly_rate","storage_hourly_rate","total_hourly_rate","storage"],"type":"object"},"profiling":{"additionalProperties":false,"properties":{"perf":{"anyOf":[{"$ref":"#/$defs/perf_config"},{"type":"null"}]},"performix":{"$ref":"#/$defs/measure"}},"required":["perf","performix"],"type":"object"},"run":{"additionalProperties":false,"properties":{"ended_at":{"anyOf":[{"format":"date-time","type":"string"},{"type":"null"}]},"errors":{"items":{"additionalProperties":false,"properties":{"code":{"enum":[2,10,20,30,31,32,40,50,130]},"condition_id":{"anyOf":[{"type":"string"},{"type":"null"}]},"message":{"type":"string"},"phase":{"type":"string"}},"required":["code","phase","message","condition_id"],"type":"object"},"type":"array"},"exit_code":{"anyOf":[{"enum":[0,2,10,20,30,31,32,40,50,130]},{"type":"null"}]},"id":{"type":"string"},"started_at":{"format":"date-time","type":"string"},"status":{"enum":["pending","running","success","partial","failed","unsupported","cancelled"]}},"required":["id","started_at","ended_at","status","exit_code","errors"],"type":"object"},"scaling":{"additionalProperties":false,"properties":{"plan":{"additionalProperties":false,"properties":{"available_cpu_ids":{"items":{"minimum":0,"type":"integer"},"type":"array"},"base_nproc":{"minimum":1,"type":"integer"},"baseline_condition_id":{"type":"string"},"cpu_selection":{"type":"string"},"requested_ratios":{"const":["1/4","1/2","3/4","4/4"]},"rounding":{"type":"string"},"sequence_seed":{"minimum":0,"type":"integer"}},"required":["base_nproc","available_cpu_ids","requested_ratios","baseline_condition_id","rounding","cpu_selection","sequence_seed"],"type":"object"},"results":{"items":{"$ref":"#/$defs/condition"},"type":"array"}},"required":["plan","results"],"type":"object"},"schema_version":{"const":"3.2.0"},"toolchain":{"additionalProperties":false,"properties":{"compiler":{"$ref":"#/$defs/measure"},"distribution":{"type":"string"},"python_version":{"type":"string"}},"required":["distribution","compiler","python_version"],"type":"object"},"workload":{"additionalProperties":false,"properties":{"prompt_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"},"runner_config":{"$ref":"#/$defs/runner"},"runner_id":{"type":"string"},"runner_sha256":{"pattern":"^[a-f0-9]{64}$","type":"string"}},"required":["runner_id","runner_sha256","runner_config","prompt_sha256"],"type":"object"}},"required":["schema_version","run","environment","platform","toolchain","framework","model","workload","execution","cache_policy","profiling","pricing","cost","scaling","artifacts"],"title":"CPU LLM benchmark summary 3.2.0","type":"object"}
````

</details>

<details>
<summary>requirements.lock</summary>

<!-- artifact path="requirements.lock" sha256="48ac5a8c75f36c9cfb79d734f5e2d68558b10d6da8a1bef3e8ce3bf7f069b781" canonical="text" -->

````text
attrs==26.1.0
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
referencing==0.37.0
rpds-py==2026.9.1
typing_extensions==4.16.0
zstandard==0.25.0
````

</details>

<details>
<summary>docker/Dockerfile</summary>

<!-- artifact path="docker/Dockerfile" sha256="b33669494e0f9610acaf45b1333ec9bbf9df310178449467a2005785d66ab9ec" canonical="text" -->

````text
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
COPY .cache/ollama/bin/ /usr/bin/
COPY .cache/ollama/lib/ /usr/lib/
ENV OLLAMA_HOST=0.0.0.0:11434 OLLAMA_MODELS=/models OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_NO_CLOUD=1
EXPOSE 11434
ENTRYPOINT ["/usr/bin/ollama", "serve"]
````

</details>

<details>
<summary>.dockerignore</summary>

<!-- artifact path=".dockerignore" sha256="fd6c95089c21248cc6522cd53b9ab1f2fe065ee75378fbcda0f59ce0eb8e69f4" canonical="text" -->

````text
**
!docker/
!docker/Dockerfile
!.cache/
!.cache/ollama/
!.cache/ollama/**
````

</details>

<details>
<summary>.gitignore</summary>

<!-- artifact path=".gitignore" sha256="61ae5ff5e95c9d7b047757e2131bee52b2bc0b868d75ecfc417dad8fb44741da" canonical="text" -->

````text
.venv/
.cache/
results/
__pycache__/
*.pyc
````

</details>

<details>
<summary>scripts/bundle_requirements.py</summary>

<!-- artifact path="scripts/bundle_requirements.py" sha256="49226ab4dafb2867da25f999284af72e739920c0322c306ebb9ae051825b0604" canonical="text" -->

````text
"""Embed maintained contracts and immutable inputs into the distributable requirements."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BEGIN='<!-- BEGIN GENERATED CONTRACT BUNDLE -->'
END='<!-- END GENERATED CONTRACT BUNDLE -->'

def files():
    return sorted([p.relative_to(ROOT).as_posix() for p in (ROOT/'specs').rglob('*') if p.is_file() and p.suffix in ['.md','.json']])+['requirements.lock','docker/Dockerfile','.dockerignore','.gitignore','scripts/bundle_requirements.py']
def render():
    chunks=[BEGIN,'','## 内包データ（自動生成・直接編集禁止）','']
    for name in files():
        source=(ROOT/name).read_text(encoding='utf-8')
        kind='json' if name.endswith('.json') else 'text'
        canonical=json.dumps(json.loads(source),sort_keys=True,separators=(',',':'),ensure_ascii=True) if kind=='json' else source
        payload=canonical+'\n' if kind=='json' else source
        if not payload.endswith('\n'):raise ValueError('Text artifact must end in LF: '+name)
        digest=hashlib.sha256(canonical.encode()).hexdigest()
        chunks += ['<details>',f'<summary>{name}</summary>','',f'<!-- artifact path="{name}" sha256="{digest}" canonical="{kind}" -->','',f'````{kind}',payload[:-1],'````','','</details>','']
    chunks.append(END)
    return '\n'.join(chunks)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    path=ROOT/'Requirments.md';source=path.read_text(encoding='utf-8')
    starts=list(re.finditer('^'+re.escape(BEGIN)+'$',source,re.M));ends=list(re.finditer('^'+re.escape(END)+'$',source,re.M))
    if len(starts)!=1 or len(ends)!=1:raise ValueError('Expected exactly one generated bundle region')
    a=starts[0].start();b=ends[0].end()
    expected=render();updated=source[:a]+expected+source[b:]
    if args.check:
        if updated!=source:print('Contract bundle is stale; run scripts/bundle_requirements.py');return 1
        print('Contract bundle is current');return 0
    path.write_text(updated,encoding='utf-8');print(f'Bundled {len(files())} artifacts');return 0
if __name__=='__main__':raise SystemExit(main())
````

</details>

<!-- END GENERATED CONTRACT BUNDLE -->
