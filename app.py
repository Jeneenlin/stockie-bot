from flask import Flask, request
from linebot import *
from linebot.models import *
from datetime import date, datetime
# ------------------------ CONNECT DATABASE --------------------------------------------------------
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import firestore
cred = credentials.Certificate("stockie-bot-firebase-adminsdk-exvio-3135ec8555.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'stockie-bot.appspot.com'})
db = firestore.client()
# --------------------------------------------------------------------------------------------------

app = Flask(__name__)

line_bot_api = LineBotApi('kE96JwdX/Qfz0zB9w/3FoxBw1oXvFNACjmOFSYe5iFGh46p/jTV5g4EML5a2dYmKxeFzswMHZg8d1LyVNCu0KesXP8GaBdLJetY0KqxrSou/6onAmwKlQmSyO2T4nUbFurM4sMkjnGZ1WT+leFkCQgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('6b0dccfb48298fba2818425b41263c9b')

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    # print('body'+body)
    req = request.get_json(silent=True, force=True)
    intent = req['queryResult']['intent']['displayName']
    text = req['originalDetectIntentRequest']['payload']['data']['message']['text']
    reply_token = req['originalDetectIntentRequest']['payload']['data']['replyToken']
    user_id = req['originalDetectIntentRequest']['payload']['data']['source']['userId']
    disname = line_bot_api.get_profile(user_id).display_name
    # print('user_id : ' + user_id)
    # print('name : ' + disname)
    # print('text : ' + text)
    # print('user_id : ' + user_id)
    # print('intent : ' + intent)
    # print('reply_token : ' + reply_token)

    reply(intent,text,reply_token,disname,user_id)
    return 'OK'

def reply(intent,text,reply_token,disname,user_id):
    if intent == 'vocab':
        docs = db.collection('Vocabulary').stream()
        ans = ""
        for doc in docs:
            ans = ans + f"{doc.id}" + "\n"
        ans = ans.rstrip()
        text_message = TextSendMessage(text=ans)
        line_bot_api.reply_message(reply_token,text_message)

    elif intent == 'Chart patterns':
        docs = db.collection('Chart_patterns').stream()
        ans = ""
        for doc in docs:
            ans = ans + f"{doc.id}" + "\n"
        ans = ans.rstrip()
        text_message = TextSendMessage(text=ans)
        line_bot_api.reply_message(reply_token,text_message)

    elif intent == 'predict GC':
        line_reply(reply_token,'PTTGC')

    elif intent == 'predict IRPC':
        line_reply(reply_token,'IRPC')

    elif intent == 'predict TOP':
        line_reply(reply_token,'TOP')

    elif intent == 'predict GPSC':
        line_reply(reply_token,'GPSC')

    elif intent == 'predict PTT':
        line_reply(reply_token,'PTT')    

    elif intent == 'predict PTTEP':
        line_reply(reply_token,'PTTEP')  

    elif intent == 'predict OR':
        line_reply(reply_token,'OR')              

def line_reply(reply_token,stock):
    r1,r2,r3,r4,r5 = retrieve_db(stock)
    text_message = TextSendMessage(text = "ผลทำนายราคาหุ้น {} สัปดาห์นี้\n{}\n{}\n{}\n{}\n{}".format(stock,r1,r2,r3,r4,r5))

    filename = "assets/{}_image.jpg".format(stock)
    blob = storage.bucket().blob(filename)
    image_url = blob.public_url
    image_message = ImageSendMessage(original_content_url = image_url, preview_image_url = image_url)

    reply_message = [text_message,image_message]
    line_bot_api.reply_message(reply_token,reply_message)

def retrieve_db(stock):
    week_num = date.today().isocalendar()[1]
    year = date.today().isocalendar()[0]
    doc_name = 'weekno.{} of {}'.format(week_num,year)
    doc_ref = db.document('{}_resultData/{}'.format(stock,doc_name))
    doc_dict = doc_ref.get().to_dict()
    doc_sort = sorted(doc_dict.items(),key=lambda date: datetime.strptime(date[0], '%d %b %Y'))
    ans = []
    for key, value in doc_sort:
        ans.append(f"{key} : {value}")
    return ans[0],ans[1],ans[2],ans[3],ans[4]

#     tickers = ['PTTGC.BK']
# for ticker in tickers:
#     ticker_yahoo = yf.Ticker(ticker)
#     data = ticker_yahoo.history()
#     last_quote = data['Close'].iloc[-1]
#     print(ticker, last_quote)

if __name__ == "__main__":
    app.run(debug=False)

