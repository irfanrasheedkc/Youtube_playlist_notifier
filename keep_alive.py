from flask import Flask , render_template
from threading import Thread
from flask_cors import CORS, cross_origin

app = Flask('',
           static_folder='static')

CORS(app)

@app.route('/')
def home():
    return render_template('app.html')

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()
