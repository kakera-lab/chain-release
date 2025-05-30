import os
from email.mime.text import MIMEText
from email.utils import formatdate
from smtplib import SMTP

from .. import settings


class Email:
    """メール通知を送信するモジュール。"""

    def __init__(self, active: bool = False) -> None:
        """初期化メソッド。

        Args:
            active (bool): メール送信機能を有効にするかどうか。デフォルトはFalse。
        """
        self.active = active

    def send(self, subject: str, message: str) -> None:
        """メール通知を送信するメソッド。

        Args:
            subject (str): 件名
            message (str): メッセージ
        """
        if not self.active:
            return

        # メールメッセージの作成
        msg = self.create_message(os.environ["MAIL_FROM"], os.environ["MAIL_TO"], subject, message)

        # SMTPサーバーの設定とメール送信
        with SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(os.environ["MAIL_FROM"], os.environ["MAIL_PASS"])
            smtp.send_message(msg)

    def create_message(self, sender: str, receiver: str, subject: str, message: str) -> MIMEText:
        """送信メッセージを作るメソッド。

        Args:
            sender (str): 送り手
            receiver (str): 受け手
            subject (str): 件名
            message (str): メッセージ

        Returns:
            MIMEText: メールメッセージオブジェクト。
        """
        msg = MIMEText(message, "plain", "utf-8")
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = subject
        msg["Date"] = formatdate()
        return msg


if __name__ == "__main__":
    pass
