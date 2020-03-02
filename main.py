#import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from flask import Flask, session, render_template, request, url_for, redirect, flash
import requests
from matplotlib import rcParams
import io
from flask import Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import base64


RAPIDAPI_KEY  = "******" 
RAPIDAPI_HOST = "******"
inputdata = {}

def fetchStockData(symbol):
  response = requests.get("https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/get-charts?region=US&lang=en&symbol=" + symbol + "&interval=1d&range=3mo",
    headers={
      "X-RapidAPI-Host": RAPIDAPI_HOST,
      "X-RapidAPI-Key": RAPIDAPI_KEY,
      "Content-Type": "application/json"
    }
  )
  if(response.status_code == 200):
    return response
  else:
    return None

def parseTimestamp(inputdata):
    timestamplist = []

    timestamplist.extend(inputdata["chart"]["result"][0]["timestamp"])
    #timestamplist.extend(inputdata["chart"]["result"][0]["timestamp"])

    calendertime = []

    for ts in timestamplist:
        dt = datetime.fromtimestamp(ts)
        calendertime.append(dt.strftime("%m/%d/%Y"))

    return calendertime

def parseValues(inputdata):

  valueList_open = []
  valueList_close = []
  valueList_open.extend(inputdata["chart"]["result"][0]["indicators"]["quote"][0]["open"])
  valueList_close.extend(inputdata["chart"]["result"][0]["indicators"]["quote"][0]["close"])

  return valueList_open, valueList_close

def attachEvents(inputdata):

  eventlist = []

  for i in range(0,len(inputdata["chart"]["result"][0]["timestamp"])):
    eventlist.append("open")	

  for i in range(0,len(inputdata["chart"]["result"][0]["timestamp"])):
    eventlist.append("close")

  return eventlist

app = Flask(__name__)

@app.route('/')
def newroute():
    """parameter"""
    return "this was passed in here" 

@app.route('/plot_png/<symbol_string>')
def plot_png(symbol_string):
    matplotlib.use('Agg')
    retdata = fetchStockData(symbol_string)
    retdata = retdata.json()
    print(retdata)

    if (None != inputdata): 

            inputdata["Timestamp"] = parseTimestamp(retdata)

            inputdata["open_Values"], inputdata["close_Values"] = parseValues(retdata)

            #inputdata["Events"] = attachEvents(retdata)

            df = pd.DataFrame(inputdata)
            print(df)

    print("***************plotting***************")
    #df = request.args['df']
    img = io.StringIO()
    
    #plt.savefig(img, format='png')
    #plt.close()
    #img.seek(0)

    #plot_url = base64.b64encode(img.getvalue())
    xtick_labels = [df['Timestamp'][i] for i in range(len(df['Timestamp'])) if i%4==0]
    x_tick_values = [i for i in range(len(df['Timestamp'])) if i%4==0]
    fig = Figure(figsize=(8,6))
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(df['Timestamp'], df['open_Values'], label="Open", color='green')
    axis.plot(df['Timestamp'], df['close_Values'], label="Close", color='red')
    axis.legend()
    axis.set_title(f"Opening and closing Trend for {symbol_string}")
    axis.set_xticks(x_tick_values)
    axis.set_xticklabels(labels=xtick_labels, rotation=25)

    #figfile = io.BytesIO()
    #plt.savefig(figfile, format='png')
    #figfile.seek(0)  # rewind to beginning of file
    #figdata_png = base64.b64encode(figfile.getvalue())
    #return render_template('create.html', results=figdata_png)

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

    #return render_template('find.html', plot_url=plot_url)




@app.route('/create', methods=('GET', 'POST'))
def create():
    error = None
    symbol_string = None
    if request.method == 'POST':
        symbol_string = request.form['title']

        if not symbol_string:
            error = 'Title is required.'
        
        if error is not None:
            flash(error)

        if request.form['button'] == 'Plot Trend':     
            return redirect(url_for('plot_png', symbol_string=symbol_string))
        elif request.form['button'] == 'Details':
            return redirect(url_for('get_detail', symbol_string=symbol_string))

    return render_template('create.html')

@app.route('/get_detail/<symbol_string>', methods=('GET', 'POST'))
def get_detail(symbol_string):
    response = requests.get("https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/get-detail?region=US&lang=en&symbol="+symbol_string,
    headers={
      "X-RapidAPI-Host": RAPIDAPI_HOST,
      "X-RapidAPI-Key": RAPIDAPI_KEY,
      "Content-Type": "application/json"
    }
  )
    if(response.status_code == 200):
        res = response.json()
        answer = {}
        answer["symbol"] = symbol_string
        answer["sector"] = res["summaryProfile"]["sector"]
        answer["fte"] = res["summaryProfile"]["fullTimeEmployees"]
        answer["city"] = res["summaryProfile"]["city"]
        answer["phone"] = res["summaryProfile"]["phone"]
        answer["state"] = res["summaryProfile"]["state"]
        answer["country"] = res["summaryProfile"]["country"]
        answer['longBusinessSummary'] = res["summaryProfile"]["longBusinessSummary"]

        answer['quarterly1'] = [res['earnings']['earningsChart']['quarterly'][0],
                                res['earnings']['earningsChart']['quarterly'][1],
                                res['earnings']['earningsChart']['quarterly'][2],
                                res['earnings']['earningsChart']['quarterly'][3]]

        answer['quarterly'] =  res['earnings']['financialsChart']['quarterly']

        answer['yearly'] = res['earnings']['financialsChart']['yearly']
        print("***********************************************")
        print(answer['yearly'])
        return render_template('details.html', answer=answer)


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    #app.run(host='127.0.0.1', port=8000, debug=True)
    app.run(host='0.0.0.0', port=80, debug=True)
