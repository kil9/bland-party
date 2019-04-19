import os

from linebot import LineBotApi, WebhookHandler

from flask import Flask

from dotenv import load_dotenv
load_dotenv()

LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)
