# Python 開発テンプレート

```plaintext
 _            _                         _____          _    _
| |          | |                       |  __ \        | |  | |
| | __  __ _ | | __  ___  _ __   __ _  | |__) | _   _ | |_ | |__    ___   _ __
| |/ / / _` || |/ / / _ \| '__| / _` | |  ___/ | | | || __|| '_ \  / _ \ | '_ \
|   < | (_| ||   < |  __/| |   | (_| | | |     | |_| || |_ | | | || (_) || | | |
|_|\_\ \__,_||_|\_\ \___||_|    \__,_| |_|      \__, | \__||_| |_| \___/ |_| |_|
                                                 __/ |
                                                |___/
```

[![OS - macOS](https://img.shields.io/badge/OS-macOS-%23000000?logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![OS - Ubuntu](https://img.shields.io/badge/OS-Ubuntu-%23E95420?logo=ubuntu&logoColor=white)](https://jp.ubuntu.com)
[![Docker](https://img.shields.io/badge/Docker->=v27.5.1-%232496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Made with Python](https://img.shields.io/badge/Python->=3.12-%233776AB?logo=python&logoColor=white)](https://python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## 概要

Python 開発用のテンプレート

## 構成 / 依存

- **OS**: macOS, Ubuntu
- **仮想環境**: [Docker](https://www.docker.com/ja-jp/products/docker-desktop/)
- **エディター**: [VSCode](https://azure.microsoft.com/ja-jp/products/visual-studio-code)
- **コード管理**: [git](https://git-scm.com/docs), [pre-commit](https://pre-commit.com/)
- **Python 環境**: Python 3.12.10 (2025/05/30)
- **Python バージョン / パッケージ管理**: [uv](https://docs.astral.sh/uv/)
- **Python リンター / フォーマッター**: [ruff](https://docs.astral.sh/ruff/)
- **Python 型解析**: [mypy](https://mypy.readthedocs.io/en/stable/)
- **テスト系**: [pytest](https://docs.pytest.org/en/stable/), [tox](https://tox.wiki/en/4.24.1/)
- **ドキュメント作成**: [sphinx](https://www.sphinx-doc.org/ja/master/)

## 環境構築

### Git の初期設定

- [GitLab 公式ドキュメント](https://gitlab-docs.creationline.com/)
- [Git 公式ドキュメント](https://docs.github.com/ja/get-started/getting-started-with-git/set-up-git)
- GitLab のアカウントに SSH 鍵を[登録する](https://gitlab-docs.creationline.com/ee/user/ssh.html)(必須)
- `git`が入っていない場合は[インストールする](https://git-scm.com/downloads)
- 以下のコマンドで`git`の初期設定を行う

```sh
git config --global user.name "Your Name"
git config --global user.email "Your Email"
```

### 環境のセットアップ

- 対応: Ubuntu, macOS
- Apple Accelerate を利用可能
- 実装済み外部コマンドが利用可能

```sh
# uvをインストール
curl -LsSf https://astral.sh/uv/install.sh | sh
# Ubuntu
echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc
# macOS
echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
```

### 開発用 Docker コンテナ

- 対応: Ubuntu
- 以下のコマンドでコンテナを立ち上げ、コンテナ内で作業する
- 実装済み外部コマンドが利用不可
- 任意に変更：`PASS=<sudo用パスワード>`
- 使いたい機能によって`docker-compose.yaml`を編集
  - WebGUI なし； `target: final`
  - WebGUI あり； `target: vnc`
  - GPU を利用: `docker-compose.yaml`に指示記載

```sh
UNAME=$(whoami) UID=$(id -u) GID=$(id -g) PASS=password docker compose -p "$(whoami)" -f docker/docker-compose.yaml up -d
```

### VSCode のセットアップ

- [VSCode](https://azure.microsoft.com/ja-jp/products/visual-studio-code)
- 新規プロファイルを作成(オプション)
  - ⚙️ > プロファイル > プロファイルの作成
- 推奨拡張機能をインストール(必須)
  - RECOMMENDED に一覧で表示されているものをインストールする

### リポジトリの初期化

- GitLab で初期化する(推奨)
  - GitLab で[空のプロジェクトを作成](https://gitlab-docs.creationline.com/ee/user/project/)
  - GitLab から clone(IDE で開く: Visual Studio Code)、保存先を指定して VSCode で開く
- その他のリポジトリ初期化
  - ホストマシーンで初期化する
  - 既存のリポジトリをクローン

### プロジェクトの初期化

- プロジェクトディレクトリに移動
- テンプレートファイルのダウンロード
- プロジェクトの初期化
- (オプション)ターミナルプロファイル`pytmp`が利用可能
  - ターミナルを開いて + で`pytmp`を選択
  - デフォルトに設定すると他の拡張機能の機能に影響が出るため禁止
  - 実装済み外部コマンドが利用可能

```sh
# テンプレート(このリポジトリ)を配置
git archive --remote=ssh://git@gitlab.kakera-lab.synology.me:9022/kakera-lab/template.git release | tar -xvf -
git add .
git commit -m "template init"
git push origin main
# Pythonプロジェクトの有効化
uv init --app --package --python 3.12.10 --vcs none
git add .
git commit -m "project init"
git push origin main
```

### 依存関係インストール

- Python のパッケージ管理は`uv`を使って行う(`pip`の代わり)
- Python 本体は`uv`によってプロジェクトごとに独立した仮想環境が作られる

```sh
# 開発用の依存のインストール(必須)
uv add $(cat requirements/dev.txt) --group dev
# Sphinx (Docs) 用の依存のインストール(オプション)
uv add $(cat requirements/docs.txt) --group docs
# Ansible 用の依存のインストール(オプション)
uv add $(cat requirements/ansible.txt) --group ansible
# (メモ)プロジェクトの依存関係をインストール
uv sync
# (定期的)プロジェクトの依存関係を更新
uv lock --upgrade
```

## 開発

### 基本

- 開発は[GitHub Flow](https://docs.github.com/ja/get-started/using-github/github-flow)の原則に従い行う
- `src/`の中で開発する(厳守)

```sh
# (毎回必須)uv仮想環境を有効化
source .venv/bin/activate
# (初回必須)pre-commitの有効化
pre-commit install
# (定期的)
pre-commit autoupdate
```

## ツール

### 実装済み外部コマンド

- Docker コンテナで実装しているため機能に制限がある可能性がある
- [`terraform <コマンド>`](https://developer.hashicorp.com/terraform/cli/commands)
- [`dockle <コマンド>`](https://github.com/goodwithtech/dockle)
- [`trivy <コマンド>`](https://trivy.dev/latest/docs/)

### ドキュメントの更新

```sh
# プロジェクトルートで実行
python -m builder.docs
```

### Docker コンテナのビルド

```sh
# プロジェクトルートで実行
# プライベートコンテナレジストリにログイン
docker login registry.kakera-lab.synology.me
# ビルド + プッシュ
python -m builder.container
```

- 下記の記述例のように`pyproject.toml`に追加する
- `dockerfiles`の書き方は 3 種類
- Dockerfile の書き方によって使えるものが異なる
  - `<タグ>`にレジストリ指定は不要
  - `<タグ> = <dockerfile>`
  - `<タグ> = { FILE = <dockerfile> }`
  - `<タグ> = { FILE = <dockerfile>, IMAGE = <ベースのイメージ> }`
  - `<タグ> = { FILE = <dockerfile>, IMAGE = <ベースのイメージ>, TARGET=<ステージ>  }`

```pyproject.toml
[tool.docker]
push = true
cache = false
registry = <レジストリのホスト名>
platforms = ["linux/amd64", "linux/arm64"]

[tool.docker.dockerfiles]
"ubuntu:2204.base" = "docker/dockerfile"
"ubuntu:2204.base" = { FILE = "docker/dockerfile" }
"ubuntu:2204.base" = { FILE = "docker/dockerfile", IMAGE = "ubuntu:22.04" }
"ubuntu:2204.base" = { FILE = "docker/dockerfile", IMAGE = "<任意のレジストリ>/ubuntu:22.04" }
"ubuntu:2204.base" = { FILE = "docker/dockerfile", IMAGE = "<任意のレジストリ>/ubuntu:22.04", TARGET="base" }
```

### リリース zip 作成

- バージョン管理は [セマンティックバージョニング](https://semver.org/lang/ja/) に従って行われる
- バージョン番号の形式は `MAJOR.MINOR.PATCH`
  - **MAJOR**：後方互換性のない変更
  - **MINOR**：後方互換性のある新機能追加
  - **PATCH**：バグ修正

```sh
# 現在のバージョンで zip を作成
python -m builder.snapshot
# セマンティックバージョンを更新して zip を作成
python -m builder.snapshot [major|minor|patch]
# リリースブランチの更新
python -m builder.release
```

- 下記の記述例のように`pyproject.toml`に追加する
  - 記載がない場合はデフォルト設定が使用される
- `.gitignore` に記載されたパスは zip に含まれない
- `readme = true`とするとこで README.md を`README.<prj_name>.md`にリネームする。
- `ignore = []` には、追加で除外したいファイル・ディレクトリのパスをルート相対で指定する
  - パスの末尾に `/` があるとディレクトリとして扱われる

```toml
[tool.release]
readme = true
ignore = [
    "src/",
    "pyproject.toml",
    "uv.lock"
]
```

## リンク

- [GitHub](https://docs.github.com/en)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Shields.io](https://img.shields.io/)
- [Simple Icons](https://simpleicons.org/)
