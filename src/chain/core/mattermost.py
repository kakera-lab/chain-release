import os

from mattermostdriver import Driver

from .. import settings


class Mattermost:
    """Mattermost通知のモジュール。"""

    def __init__(self, active: bool = False) -> None:
        """初期化メソッド。

        Args:
            active (bool): Mattermost通知を有効にするかどうか。デフォルトはFalse。
        """
        self.active = active

    def send(self, message: str) -> None:
        """Mattermost通知を送るメソッド。

        Args:
            message (str): メッセージ
        """
        if not self.active:
            return

        # Mattermostドライバーの設定
        md = Driver(
            {
                "url": os.environ["MATTERMOST_URL"],
                "login_id": os.environ["MATTERMOST_BOT_ID"],
                "token": os.environ["MATTERMOST_BOT_TOKEN"],
                "scheme": "http",
                "port": int(os.environ["MATTERMOST_PORT"]),
                "verify": False,
            }
        )

        # Mattermostにログイン
        md.login()

        # ユーザーの取得
        sender = md.users.get_user_by_username(os.environ["MATTERMOST_BOT_ID"])
        receiver = md.users.get_user_by_username(os.environ["MATTERMOST_TO_ID"])

        # ダイレクトメッセージチャンネルの作成
        peers = [sender["id"], receiver["id"]]
        direct_channel = md.channels.create_direct_message_channel(peers)

        # メッセージの投稿
        md.posts.create_post(options={"channel_id": direct_channel["id"], "message": message})

        # Mattermostからログアウト
        md.logout()


if __name__ == "__main__":
    pass
