# 再生成入力の構成と編集手順

`../Requirments.md` と本ディレクトリ一式を同じ版で配布する。要件書は全体方針と受入条件、本ディレクトリは独立した契約と固定データの正本である。生成AIは既存の実行コードや過去の会話を補助入力にせず、この一式から実装する。

## 読む順序と責務

| ファイル | 責務 |
| --- | --- |
| [summary-format.md](summary-format.md) / [summary.schema.json](summary.schema.json) | 結果の意味・階層と機械検証。結果形式の変更はここから始める |
| [runner-contract.md](runner-contract.md) / [runner.schema.json](runner.schema.json) | モデルやテスト項目に依存しない Runner 契約 |
| [runner.template.json](runner.template.json) | 未束縛の雛形。直接実行しない |
| [measurement-protocol.md](measurement-protocol.md) | 測定区間・スケーリング・キャッシュ・集計・品質判定 |
| [ollama-adapter.md](ollama-adapter.md) | Ollama 固有の能力確認と証跡 |
| [model-catalog.md](model-catalog.md) / runners/*.json | 対象の一覧・追加手順とモデルごとの固定設定 |
| compat/*.json | 旧形式の検証専用。現行形式の生成には使わない |
| bootstrap/ | 再生成時にそのまま配置する固定入力 |
| inputs.manifest.json / [check_inputs.py](check_inputs.py) | 入力一式のハッシュと整合性確認 |

JSON のフィールド定義は Schema、意味・計算式は対応する Markdown、実際のモデル・測定パラメータは Runner instance を唯一の正本とする。矛盾は実装前に仕様側で解消する。モデル一覧は案内であり、Runner の値を上書きしない。

## 生成先への配置

| 入力 | 生成先（生成ルートからの相対パス） |
| --- | --- |
| summary.schema.json | schemas/summary.schema.json |
| runner.schema.json | schemas/runner.schema.json |
| compat/*.json | schemas/ 以下に同じファイル名で配置 |
| runners/*.json | runners/ 以下に同じファイル名で配置 |
| bootstrap/docker/Dockerfile | docker/Dockerfile |
| bootstrap/requirements.lock | requirements.lock |
| bootstrap/.dockerignore | .dockerignore |
| bootstrap/.gitignore | .gitignore |

JSON は内容を維持し、テキストは UTF-8/LF のバイト列を維持する。生成元の specs/ と生成先の runners/ 等を二重に手編集しない。生成先に既存ファイルがあれば差分確認し、上書きでユーザー設定を失わない。要件書・specs/ も保存し、生成コード・README・ログ・結果は入力一式に混入させない。

## 入力の検査と更新

リポジトリルートで実行する（Python 標準ライブラリのみ）。

```bash
python3 specs/check_inputs.py
```

検査対象は Requirments.md と specs/ の全ファイル（manifest 自体と Python の __pycache__ を除く）。JSON は `json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)` の UTF-8 バイト列、その他はそのままのバイト列の SHA-256 とする。manifest は `{"format_version": 1, "files": {"相対パス": "sha256"}}`。追加・欠落・内容差を検出し、成功0、不適合1で終了する。外部へのシンボリックリンクは入力にできない。ハッシュは配布一式の整合性確認であり、配布者の署名ではない。

仕様を変更したときだけ、差分を確認したうえで以下を実行する。

```bash
python3 specs/check_inputs.py --update
python3 specs/check_inputs.py
```

さらに全 Schema を Draft 2020-12 として検証し、Template と全 instance の Schema 適合、runner-contract の意味検証、測定・結果・表示の受入試験を生成した検証器で実施する。ハッシュ検査はこれらを代替しない。測定方式・結果形式を変更する場合は契約の版と互換性も更新する。ファイル配置だけの変更では Summary/Runner の版やモデル digest を変えない。

受入時には Requirments.md と specs/ だけを空の作業場所へコピーして検査・再生成する。旧埋込形式と旧 bundle_requirements.py は廃止し、新しい生成物から呼び出さない。
