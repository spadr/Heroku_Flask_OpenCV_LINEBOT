from flask import *
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextSendMessage, ImageMessage, FollowEvent)
import os
import cv2
import numpy as np

app = Flask(__name__)

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(SECRET)

ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
SECRET = os.environ['SECRET']

aruco = cv2.aruco
dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)


#マーカを検出
def arReader(img):
    corners, ids, rejectedImgPoints = aruco.detectMarkers(img, dictionary)
    if len(corners)==0:
        return [],[]
    nmids = np.array([i for i in np.array(np.array(ids).flatten())])
    nmcorners = np.array(corners)[np.argsort(nmids)][:,0]
    return nmcorners,nmids


@app.route("/")
def hello_world():
    return "app is running!"


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Requestbody: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return'OK'


@handler.add(FollowEvent)
def handle_follow(event):
    reply_messages = []
    reply_messages.append(TextSendMessage(text="フォーしてくれてありがとう！"))
    line_bot_api.reply_message(event.reply_token, reply_messages)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    reply_messages = []
    with open("static/"+event.message.id+".jpg", "wb") as f:
        f.write(message_content.content)
        test_url = "./static/"+event.message.id+".jpg"
        img = cv2.imread(test_url)
        corners, ids = arReader(img)
        if img.shape[0]<img.shape[1]:
            img =  np.rot90(img)
        corners, ids = arReader(img)
        if len(ids)!=2:
            reply_messages.append(TextSendMessage(text="ARマーカーが読み取れません！"))
            line_bot_api.reply_message(event.reply_token, reply_messages)
            return
        #画像処理(省略)
        reply_messages.append(TextSendMessage(text="ARマーカーが読み取れたよ！"))
        line_bot_api.reply_message(event.reply_token, reply_messages)

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)