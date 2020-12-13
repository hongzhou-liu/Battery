import pandas as pd
from pandas import DataFrame
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as po
import json
import re
import sys
from flask import *
import os
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)

@app.route('/')
def landing():
   return redirect(url_for('upload_file'))

@app.route('/upload')
def upload_file():
   return render_template('testapp.html')

@app.route('/uploader',methods=['POST'])
def uploader():
	os.makedirs(os.path.join(app.instance_path, 'htmlfi'), exist_ok=True)
	device=request.form['device']
	date1=request.form['date1']
	date2=request.form['date2']
	return redirect(url_for('analyze',  device=device, date1=date1, date2=date2))

@app.route('/analyze/<device>/<date1>/<date2>')
def analyze(device,date1,date2):
	filename=device
	# url = "https://parkhub.loggly.com/apiv2/events?q=json.devicename:*_POWDRKILLINGTON_* and json.rawlogmessage:\"iOS Battery's current percentage:*\"&from=2020-11-21T03:00:00.000-06:00&until=2020-11-21T23:00:00.000-06:00&size=1000"
	url = "https://parkhub.loggly.com/apiv2/events?q=json.devicename:*_"+device+"_* and json.rawlogmessage:\"iOS Battery's current percentage:*\"&from="+date1+".000-06:00&until="+date2+".000-06:00&size=1000"
	payload = {}
	headers = {
	  'Authorization': 'Bearer c64c8ddc-a078-458f-acae-055531ac1c01'
	}

	response = requests.request("GET", url, data=payload, headers=headers)
	list1= response.text.encode('utf8')
	list2=pd.read_json(list1)

	## Normalize to split the Json to DataFrame
	from pandas.io.json import json_normalize 
	df=pd.io.json.json_normalize(list2.events)

	df['tTime'] = df['event.json.timestamp'].apply(str)

	r = re.compile(r'.\d\d\dZ$')

	df['tTime'] = df['tTime'].str.replace(r,'',regex=True)

	df['tTime'] = pd.to_datetime(df['tTime'])

	    #Create a new variable and store the transactionTime as Central_Time
	Central_Time=df['tTime'].dt.tz_localize('utc').dt.tz_convert('US/Central')

	df['Central_Time']=Central_Time

	df['Device_name']=df['event.json.devicename']

	df['Battery']=df['event.derived.iOSBatteryCurrentPercent']

	df['os']=df['event.json.osversion']

	fig = px.scatter(df,x='Central_Time', y='Device_name',color='Battery',template="plotly", color_continuous_scale='rdylgn',hover_data=["Battery","os"])
	    #fig = px.scatter(df,x='Central_Time', y='Cashier',color='Device_Name',template="plotly", hover_data=["Device_Name"], hover_name = "confirmationCode")
	fig.update_xaxes(title_font=dict(size=18, family='Courier', color='Darkblue'),showline=True, linewidth=2, linecolor='black', mirror=True)
	fig.update_yaxes(title_font=dict(size=18, family='Courier', color='Darkblue'),showline=True, linewidth=2, linecolor='black', mirror=True)
	fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
	fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

	fig.update_layout(
	    autosize=True,
	    width=2225,
	    height=800,
	    margin=go.layout.Margin(
	        l=70,
	        r=30,
	        b=90,
	        t=70,
	        pad=4
	                            ),
	        paper_bgcolor="lightsteelblue",
	                    )
	fig.update_layout(title_text=device)
	output_filename=filename+'_output.html'
	fig.write_html('instance/htmlfi/'+output_filename,auto_open=True)
	return redirect(url_for('done',file=output_filename))
    #po.plot(fig, filename=filename + '_output.html')

@app.route('/done/<file>')
def done(file):
    return send_file('instance/htmlfi/' + file, as_attachment=True)


if __name__ == '__main__':
	app.run(host = '0.0.0.0')