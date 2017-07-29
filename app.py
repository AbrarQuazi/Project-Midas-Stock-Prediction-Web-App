from flask import Flask, render_template, request
import requests
import csv
import numpy as np 
import tweepy
import codecs 
from textblob import TextBlob
from sklearn.svm import SVR 
from contextlib import closing 


consumer_key = 'ZLTBGcwU3VdysfYpY3xYxqbib'
consumer_secret = 'mRtqyLsFazPlJxJYaFNcczV2Qehy9ec90x1ZWA5FprBBCBCa3P'

access_token = '975044329-m5XebkUSR5QitdyX88UKRsDnMoQ899eAYAIkL2cb'
access_token_secret = 'lfRSnE1PK8DuabUdp2blYasMZPdtkiZ2RP5WJ3y1Lmyr8'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token,access_token_secret)

api = tweepy.API(auth)

dates = []
prices = []
currentDate = 0
currentStock = 0

def predict_prices(dates,prices,x):
	dates = np.reshape(dates,(len(dates), 1))
	svr_rbf = SVR(kernel='rbf', C=1e3, gamma= .1 )
	svr_rbf.fit(dates, prices)

	return svr_rbf.predict(x)[0]


app = Flask(__name__)

@app.route('/')
def home():
	return render_template ('home.html')

@app.route('/search', methods= ['GET', 'POST'])
def search():
	if request.method == 'POST':
		company = request.form['company']
		numTweets = 500
		public_tweets = api.search(company + ' stock', count=numTweets )
		positiveSentiment = 0
		negativeSentiment = 0
		#Gatering CSV File 
		url = 'http://www.google.com/finance/historical?q=NASDAQ%3A'+company+'&output=csv%27&output=csv'
		with closing(requests.get(url, stream=True)) as r:
			if r.status_code == 400:
				return render_template('error.html')
			reader = csv.reader(codecs.iterdecode(r.iter_lines(), 'utf-8'))
			reader.__next__()
			num = 0;
			for row in reader:
				dates.append(int(row[0].split('-')[0]))
				prices.append(float(row[1]))
				if num == 0:
					currentDate = int(row[0].split('-')[0])
					currentStock = float(row[1])
				num += 1	
				if num == 20:
					break

		price = predict_prices(dates, prices, currentDate + .3)
		
		for tweet in public_tweets:
			tweetSentiment = TextBlob(tweet.text)
			if tweetSentiment.polarity < 0:
				negativeSentiment += 1
			if tweetSentiment.polarity > 0:
				positiveSentiment += 1

		if float(positiveSentiment) > float(.70 *(positiveSentiment + negativeSentiment)):
			del public_tweets[:]
			del dates[:]
			del prices[:]
			currentDate = 0
			return render_template('results.html', company= company, price=price, currentStock= currentStock, sentiment= 'positive')
		else:
			del public_tweets[:]
			del dates[:]
			del prices[:]
			currentDate = 0
			return render_template('results.html', company= company, price=price, currentStock= currentStock, sentiment= 'negative')

	return render_template('home.html')
if __name__ == "__main__":
	app.run(debug=True)