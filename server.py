from flask import Flask, render_template, request, send_file
from datetime import datetime, timedelta
import os, requests, lxml.html
import json, urllib
from email import generator
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import make_msgid
import mimetypes

## json 'details' field can accept formatted HTML it is rendered using jinja2 escaping '|safe'
#cacti image urls are loaded twice. Will not appear on checklist unless logged in. POST request encodes images into base64 email attachment after auth.

app = Flask(__name__)

@app.route("/")
def home_page():
	#today = datetime.today()
	#=today.strftime("")
	return render_template("home.html", date=datetime.now().date().strftime("%m/%d/%y"))

@app.route('/noon', methods=['POST', 'GET'])
def noon():
	current=datetime.now()
	date=current.date().strftime("%m/%d/%y")
	startcacti = current + timedelta(hours=-4)
	title="12:00 PM"

	with open('noon.json') as f:
		data=json.load(f)

	if request.method == "GET":
		return render_template('noon.html', title=title, date=date, time=datetime.now().time(), data=data, start=startcacti.strftime("+%s"))

	elif request.method == "POST":
		#end = current.time()
		cids=[]
		urls=[]
		images={}
		with open('noon.json') as f:
			data=json.load(f)
			#data=json.load(f)[15]['detail']
			for i in data:
				if "acti" in i['title']:
					cacti=i['detail']
			#print(type(cacti))
			urls=cacti.split('"')[1::2]
			#for i in urls:
				#urls[i]=url[i].concat(+"graph_start={0}").format(startcacti.strftime("+%s")
			#append cactistarttime to urls &graph_start={0}.format(startcacti.strftime("+%s"))

		for i in range(len(urls)):
			cids.append(make_msgid())

		images=list(zip(urls,cids))

		result = request.form
		html_output=render_template('result.html', result=result, endtime=datetime.now().time(), title=title, date=date, images=images, start=startcacti.strftime("+%s"))
		
		msg = MIMEMultipart()
		msg['Subject'] = '{0} Checklist {1}'.format(title, date)
		msg['From'] = ""
		msg['To'] = "checklist@example.com"
		msg['X-Unsent']="1" #makes eml open in compose mode

		headers = {}
		for key in headers:
			value = headers[key]
			if value and not isinstance(value, basestring):
				value = str(value)
			msg[key] = value

		part = MIMEText(html_output, 'html')
		msg.attach(part)

		with requests.Session() as s:
			loginurl="http://bumonitor.example.com/cacti/index.php"
			login = s.get(loginurl)
			login_html = lxml.html.fromstring(login.text)
			hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
			form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}
			form["login_username"] = "user"
			form["login_password"] = "password"
			#print (form)
			#print(loginurl)
			response = s.post(loginurl, data=form)
			#print(response.status_code)
			#if reponse.ok == False:
				#print("cacti login failed")

			for url,cid in images:
				response=s.get(url)
				#print(response.url)
				msgimg=(MIMEImage(response.content, _subtype="png"))
				msgimg.add_header('Content-ID', '{0}'.format(cid))
				msg.attach(msgimg)


		with open("html_output.html", "w") as fh:
			gen = generator.Generator(fh)
			gen.flatten(msg)
		return send_file("html_output.html", mimetype="application/octet-stream", as_attachment=True, attachment_filename="checklist.eml")
		#return render_template('result.html', result=result, endtime=datetime.now().time(), title="12PM", date=current.date(), start=start.strftime("+%s"))

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080, debug=True)
