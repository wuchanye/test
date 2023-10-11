from flask import Flask
app = Flask(__name__)

from flask import request, abort
from linebot import  LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

line_bot_api = LineBotApi('dhX8nvPCDm0VOdFugXpTvezKPKsw7coeISdVz28SQ7WMQ7cTj0M8IBtE/L+qaWj4iwUaKv+2S8zhsUda4sfGHMncEVlacKwO8zrP4PTzcTeOvHaXDpSAONV4M/aNfXAlFEkQmlDlPRFUih/jhZk3fAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('8488ba547e8aeb4a4255b31562637275')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=event.message.text))

if __name__ == '__main__':
    app.run()
