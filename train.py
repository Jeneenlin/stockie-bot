from flask import Flask, render_template, request
from sklearn.preprocessing import MinMaxScaler
from datetime import date
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import numpy as np
import keras
import schedule
import time
import datetime
# ------------------------ CONNECT DATABASE --------------------------------------------------------
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import firestore
cred = credentials.Certificate("stockie-bot-firebase-adminsdk-exvio-3135ec8555.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'stockie-bot.appspot.com'})
db = firestore.client()
# --------------------------------------------------------------------------------------------------

app = Flask(__name__)

@app.route("/train")
def main():
    stock_list = ['PTTGC','IRPC','TOP','GPSC','PTT','OR','PTTEP']
    for i in range(len(stock_list)):
        print('stock_list ======== ',stock_list[i])
        train_model(stock_list[i])
    return 'OK'

def train_model(stock_n):
    if stock_n == 'PTTGC' or stock_n == 'IRPC' or stock_n == 'TOP':
        print('GC-IRPC-TOP-Price-predict.h5')
        periodhist = "7y"
        model = keras.models.load_model('model/GC-IRPC-TOP-Price-predict.h5')
    elif stock_n == 'GPSC':
        print('{}-Price-predict.h5'.format(stock_n))
        periodhist = "7y" 
        model = keras.models.load_model('model/{}-Price-predict.h5'.format(stock_n)) 
    elif stock_n == 'PTT':
        print('{}-Price-predict.h5'.format(stock_n)) 
        periodhist = "7y"
        model = keras.models.load_model('model/{}-Price-predict.h5'.format(stock_n)) 
    elif stock_n == 'OR':
        print('{}-Price-predict.h5'.format(stock_n)) 
        periodhist = "3y"
        model = keras.models.load_model('model/{}-Price-predict.h5'.format(stock_n)) 
    elif stock_n == 'PTTEP':
        print('{}-Price-predict.h5'.format(stock_n)) 
        periodhist = "10y"
        model = keras.models.load_model('model/{}-Price-predict.h5'.format(stock_n)) 

    stock = yf.Ticker("{}.bk".format(stock_n))

    hist = stock.history(period=periodhist)
    df = pd.DataFrame(hist)
    d = 35
    ahead = 5
    n = int(hist.shape[0]*0.8)
    training_set = df.iloc[:n, 1:2].values
    # test_set = df.iloc[n:, 1:2].values

    sc = MinMaxScaler(feature_range = (0, 1))
    training_set_scaled = sc.fit_transform(training_set)
    X_train = []
    y_train = []
    for i in range(d, n-ahead):
        X_train.append(training_set_scaled[i-d:i, 0])
        y_train.append(training_set_scaled[i+ahead, 0])
    X_train, y_train = np.array(X_train), np.array(y_train)
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

    df['Date'] = df.index
    df = df.reset_index(drop=True)
    ## Add a dummy row at the end. This will not be used to predict. 
    df.loc[len(df)]=df.loc[len(df)-1]

    # Getting the predicted stock price 
    dataset_train = df.iloc[:n, 1:2]
    dataset_test = df.iloc[n:, 1:2]
    dataset_total = pd.concat((dataset_train, dataset_test), axis = 0)
    inputs = dataset_total[len(dataset_total) - len(dataset_test) - d:].values
    inputs = inputs.reshape(-1,1)
    inputs = sc.transform(inputs)

    X_test = []
    for i in range(d, inputs.shape[0]):
        X_test.append(inputs[i-d:i, 0])
    X_test = np.array(X_test)
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

    predicted_stock_price = model.predict(X_test)
    predicted_stock_price = sc.inverse_transform(predicted_stock_price)

    plt.plot(df.loc[n:, 'Date'],dataset_test.values, color = 'red', label = 'Real Stock Price')
    plt.plot(df.loc[n:, 'Date'],predicted_stock_price, color = 'blue', label = 'Predicted  Stock Price')
    plt.title('{} Price Prediction'.format(stock_n))
    plt.xlabel('Time')
    plt.ylabel('{} Price'.format(stock_n))
    plt.legend()
    plt.xticks(rotation=90)
    plt.savefig('assets/{}_image.jpg'.format(stock_n))
    plt.clf()

    p1 = round(float(predicted_stock_price[-5]),3)
    p2 = round(float(predicted_stock_price[-4]),3)
    p3 = round(float(predicted_stock_price[-3]),3)
    p4 = round(float(predicted_stock_price[-2]),3)
    p5 = round(float(predicted_stock_price[-1]),3)

    print("Day 1 predicted price = ", float(predicted_stock_price[-5]))
    print("Day 2 predicted price = ", float(predicted_stock_price[-4]))
    print("Day 3 predicted price = ", float(predicted_stock_price[-3]))
    print("Day 4 predicted price = ", float(predicted_stock_price[-2]))
    print("Day 5 predicted price = ", float(predicted_stock_price[-1]))

    update_database(stock_n,p1,p2,p3,p4,p5)

def update_database(stock,p1,p2,p3,p4,p5):
# -------------------------- UPDATE PREDICT RESULT TO DATABASE------------------------
    d5predict = (date.today() + datetime.timedelta(days=5)).strftime("%d %b %Y")
    d4predict = (date.today() + datetime.timedelta(days=4)).strftime("%d %b %Y")
    d3predict = (date.today() + datetime.timedelta(days=3)).strftime("%d %b %Y")
    d2predict = (date.today() + datetime.timedelta(days=2)).strftime("%d %b %Y")
    d1predict = (date.today() + datetime.timedelta(days=1)).strftime("%d %b %Y")
    week_num = date.today().isocalendar()[1]
    year = date.today().isocalendar()[0]
    doc_name = 'weekno.{} of {}'.format(week_num,year)
    
    doc_ref = db.document('{}_resultData/{}'.format(stock,doc_name))
    doc_ref.set({
        str(d5predict):float(p5),
        str(d4predict):float(p4),
        str(d3predict):float(p3),
        str(d2predict):float(p2),
        str(d1predict):float(p1)
    })
# ------------------------ UPLOAD IMAGE FILE TO STORAGE --------------------------------------------
    filename = "assets/{}_image.jpg".format(stock)
    blob = storage.bucket().blob(filename)
    blob.upload_from_filename(filename)
    blob.make_public()
    print("I'm training model..............",time.ctime())  
# --------------------------------------------------------------------------------------------------

schedule.every(10).seconds.do(main)
# schedule.every().sunday.do(main)
if __name__ == "__main__":
    # app.run(debug=True)
    while True:
        schedule.run_pending()
        time.sleep(1)
        # time.sleep(60)