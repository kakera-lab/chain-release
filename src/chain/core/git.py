import subprocess


class Git:
    """Gitに関する情報を取得するためのモジュール。"""

    @classmethod
    def hash(cls) -> str:
        """Gitの現在のコミットハッシュを取得。"""
        cmd = ("git", "rev-parse", "HEAD")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", check=True)  # noqa
        githash = result.stdout.strip()
        return githash

    @classmethod
    def branch(cls) -> str:
        """Gitの現在のブランチ名を取得。"""
        cmd = ("git", "rev-parse", "--abbrev-ref", "HEAD")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", check=True)  # noqa
        gitbranch = result.stdout.strip()
        return gitbranch

    @classmethod
    def diff(cls, debug: bool) -> bool:
        """未コミットの変更を確認。"""
        if debug:
            return True
        cmd = ("git", "diff")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", check=True)  # noqa
        diff = result.stdout.strip()
        if diff:
            raise RuntimeError
        return True


if __name__ == "__main__":
    pass
