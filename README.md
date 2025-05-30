# Chain: 実験管理ライブラリ

```
 _            _                          _____  _             _
| |          | |                        / ____|| |           (_)
| | __  __ _ | | __  ___  _ __   __ _  | |     | |__    __ _  _  _ __
| |/ / / _` || |/ / / _ \| '__| / _` | | |     | '_ \  / _` || || '_ \
|   < | (_| ||   < |  __/| |   | (_| | | |____ | | | || (_| || || | | |
|_|\_\ \__,_||_|\_\ \___||_|    \__,_|  \_____||_| |_| \__,_||_||_| |_|
```

## 概要

実験の安全性とコード管理を強化し、チームの情報共有を効率化

## 依存

- [必須: Docker](https://www.docker.com/ja-jp/)
- [MLFlow](https://mlflow.org/)
- [Optuna](https://optuna.org/)
- [DVC](https://dvc.org/)
- [MinIO](https://min.io/)
- [MariaDB](https://mariadb.org/)
- [Hydra](https://hydra.cc/)
- [gRPC](https://grpc.io/)
- [Hera](https://hera.readthedocs.io/en/stable/)

## Chain の概念

Chain では、研究を以下の階層構造で定義します。

### 1. Project

- **Task** の集合体
- 研究全体の単位

### 2. Workflow

- **Project** に実際のパラメータを与えたもの
- 実行可能な構成を定義

### 3. Task

- 前処理・学習・検証など、ある程度まとまった処理単位
- `Hydra` の Config やシミュレーション処理は **Task** 単位で実装

### 4. Experiment

- **Task** に対して具体的なパラメータを設定したもの
- パラメータ探索や比較の単位

### 5. Run

- **Experiment** を実行した際の個々の実行結果
- 実際に動いたシミュレーションや学習ログの記録単位
- 1 回の実行で親 Run が生成、その中で複数の子 Run が出る場合は入れ子構造で管理

## セットアップ

### 準備

- [kakera Python テンプレート](https://gitlab.kakera-lab.synology.me/kakera-lab/template)
- プロジェクト Dir の初期化
- 開発環境構築
- Docker を起動

## インストール

- クローンして pip インストール

## DVC の初期化(データの管理もする場合)

```sh
dvc init
git add .
git commit -m "dvc init"
```

## .env ファイルの作成

- kakera Python テンプレートを利用している前提
- MinIO に NFS ストレージは非推奨
- 例（ローカル実行ならコピペで動作可能）

```env
# src/.envとして配置（厳守）
CHAIN_URI=http://localhost:8180
FILE_PATH=./volumes
SECRET_KEY=dev-secret-key

STORE_URI=mysql+pymysql://root:mariadbadmin@mariadb:3306/chain
MARIADB_ROOT_PASSWORD=mariadbadmin
MARIADB_USER=mariadb
MARIADB_PASSWORD=mariadb
MARIADB_DATABASE=chain

S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

## Chain CLI

### Chain Server 操作（ローカル実行時）

- 起動: `chain up server [-e local|docker|k8s]`

  - `local`: MariaDB（phpMyAdmin 付き）+ MinIO を含む全サービスを Docker 展開
  - `docker`（デフォルト）: `chain server` のみ Docker 展開。DB や MinIO は外部
  - `k8s`: Kubernetes に `chain server` 展開。外部インスタンス必要

- 停止: `chain down server`

### プロジェクト操作

- 追加: `chain add prj`
- 削除: `chain remove prj`
- 初期化: `chain init prj`
- 設定: `chain set prj`
- 接続 ID・URL 取得: `chain get [prj|mlflow|optuna|chaser|dvc]`
- Client 設定: `chain modify [prj|mlflow|optuna|chaser|dvc] <接続ID・URL>`
- DVC Remote 設定: `dvc remote add <Project名> <DVC URL>`

### WebUI 操作

- WebUI コンテナはプロジェクトごとに独立
- 起動: `chain up [prj|mlflow|optuna|chaser]`
- 停止: `chain down [prj|mlflow|optuna|chaser]`
- `prj`選択で`mlflow|optuna|chaser`全展開

## ファイル保存仕様

- 全ファイルはリモートへ Push。ローカル保存は原則なし。
- 一時ファイルは `.volumes/` に保存。実験後、自動でリモートに Push。
- `Config` により `.volumes/` の削除設定が可能（デフォルト: OFF）

## Hydra の機能拡張

- Hydra 管理ファイルを MLflow に自動アップロード
- MLflow 上で Experiment・親 Run 自動生成
- 出力結果は MLflow に保存
- Multi-Run 無効化（管理簡略化のため）
- その他は通常の Hydra と同様

```python
from omegaconf import DictConfig
import chain

@chain.hydra.main(version_base=None, config_path="./configs", config_name="sample")
def main(configs: DictConfig, run: ActiveRun):
    <実験の処理>

if __name__ == "__main__":
    main()
```

```yaml
exp: <実験名>

<実験Config>

defaults:
  - custom
  - _self_

hydra:
  searchpath:
    - pkg://chain.configs
```

## Optuna との連携

- artifacts の TCP 経由 S3 保存
- gRPC server 経由の storage 連携
- 使用例：

```python
import optuna
from chain.optuna.storages import APIGrpcStorageProxy
from chain.optuna.artifacts import APIBoto3ArtifactStore

storage = APIGrpcStorageProxy("< Optuna URL >")
artifact_store = APIBoto3ArtifactStore("< Optuna URL >")

def objective(trial: optuna.Trial) -> float:
    ...
    upload_artifact(
        artifact_store=artifact_store,
        file_path=file_path,
        study_or_trial=trial,
    )
```

## DVC との連携

- Chain Server API 経由で S3 読み書き

## 通知機能（実装中）

- 任意設定で実験完了通知などを送信可能

## k8s への Helm デプロイ（実装中）

- MariaDB・MinIO を別途用意
- Helm 導入済み k8s クラスタ（microK8s 可）
- LoadBalancer (例: MetalLB) 導入

## Argo Workflow 利用（実装中）

- [Argo workflows](https://argoproj.github.io/workflows/)
