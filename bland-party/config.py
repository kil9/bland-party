import os

import logging

import redis

from flask import Flask

from linebot import LineBotApi, WebhookHandler

from dotenv import load_dotenv
load_dotenv()

LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
REDIS_URL = os.environ.get("REDIS_URL")

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
r = redis.from_url(REDIS_URL)

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
