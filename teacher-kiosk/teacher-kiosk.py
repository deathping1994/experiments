from __future__ import print_function
from urllib import urlencode, urlopen
import requests
from flask import Flask, send_from_directory, jsonify
from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename
from apiclient import discovery
import os
from sqlalchemy import and_
import sqlalchemy.exc
from oauth2client.client import SignedJwtAssertionCredentials
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import and_
import sqlalchemy.exc
UPLOAD_FOLDER = '/home/gaurav/uploads'
ALLOWED_EXTENSIONS = set(['txt','doc','docx','ppt','pptx','xls','xlsx', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:gaurav@localhost:5432/teacherkiosk'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db=SQLAlchemy(app)

class Timetable(db.Model):
    id=db.Column(db.Integer,autoincrement=True,primary_key=True)
    day=db.Column(db.String(25))
    time=db.Column(db.String(20))
    batch=db.Column(db.String(50))
    sub=db.Column(db.String(50))
    fac=db.Column(db.String(50))
    venue=db.Column(db.String(25))
    type=db.Column(db.String(20))

    def __init__(self,day,time,batch,sub,fac,venue,type):
        self.day=day
        self.time=time
        self.batch=batch
        self.sub=sub
        self.fac=fac
        self.venue=venue
        self.type=type

def sendsms(tags):
    return True

@app.route('/savetimetable')
def timetable_create():
    db.create_all()
    file= open("timetable.txt","r")
    for line in file:
        line=line.split("   ")
        line[1]=line[1].strip()
        if "PM" in line[1]:
            line[1]=line[1][:-2]
            line[1]=str(int(line[1])+12)
        else:
            line[1]=line[1][:-2]
        # print (line)
        cl=Timetable(line[0].strip(),line[1],line[2].strip(),line[3].strip(),line[4].strip(),line[5].strip(),line[6].strip())
        db.session.add(cl)
        db.session.commit()
    return jsonify(success="Time table successfully created")

@app.route('/timetable/<fac_code>')
def showtimetable(fac_code):
    try:
        fac_code=str(fac_code)
        sql="SELECT * FROM timetable WHERE fac='"+fac_code+"'"
        print (sql)
        res=db.engine.execute(sql)
        if res is not None:
            print(res.keys())
            js={}
            jslist=[]
            for r in res:
                print ("k")
                js['day']=r['day']
                js['time']=r.time
                js['batch']=r.batch
                js['sub']=r.sub
                js['venue']=r.venue
                js['type']=r.type
                print ("blk")
                jslist.append(js.copy())
            return jsonify(success=jslist),200
        else:
            return jsonify(error="Invalid Code"),500
    except Exception as e:
        print (str(e))
        return jsonify(error="Exception block"),500


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


client_email = 'account-1@teachers-kiosk.iam.gserviceaccount.com'
with open("client.p12") as f:
  private_key = f.read()

credentials = SignedJwtAssertionCredentials(client_email, private_key,
    'https://www.googleapis.com/auth/drive')
from httplib2 import Http
http_auth = credentials.authorize(Http())

service = discovery.build('drive', 'v2', http=http_auth)

@app.route('/folders')
def list_folder():
    param={}
    param['q'] = "'root' in parents"
    results = service.files().list(**param).execute()
    return jsonify(results=results)


@app.route('/notify')
def sendnotification():
    headers={}
    data={}
    par=request.get_json(force=True)
    try:
        if par['authtoken']=="gauraviscool":
            data['platform']=par[1]
            data['msg']=par['msg']
            data['tags']=par['tags']
            if 'payload' in par:
                data['payload']=par['payload']
                headers['x-pushbots-appid']="564e3f56177959ce468b4569"
                headers['x-pushbots-secret']="bafdd9608dab716baabad599cc6c477e"
                headers['Content-Type']="application/json"
                r=requests.post("https://api.pushbots.com/push/all",headers=headers)
                sendsms(data['tags'])
                if r.status_code==200:
                    return jsonify(success="Notification Pushed"),200
            else:
                return jsonify(error=r.content),r.status_code
        else:
            return jsonify(error="Not Authorised"),403
    except Exception as e:
        print(str(e))
        return jsonify(error="Something's fishy"),500


@app.route('/upload',methods=['GET','POST'])
def upload_file():
    if request.method == 'POST':
        # file = request.files['file']
        uploaded_files = request.files.getlist("file[]")
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                temp=app.config['UPLOAD_FOLDER']+"/"+filename
                results = service.files().insert(
                media_body=temp,
                convert=False,
                useContentAsIndexableText=False)\
                    .execute()
                # str(results)

                service.permissions().insert(fileId=results['id'], body={
                'value':'gshukla66@gmail.com',
                'type': 'user',
                'role': 'writer'
                }).execute()
                service.permissions().insert(fileId=results['id'], body={
                'value':'',
                'type': 'anyone',
                'role': 'reader'
                }).execute()
                os.remove(app.config['UPLOAD_FOLDER']+'/'+filename)
        return jsonify(res=results)
    return '''
    <!DOCTYPE html>
<html lang="en">
  <head>
    <link href="//netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap.min.css"
          rel="stylesheet">
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h3 class="text-muted">Upload Notes</h3>
      </div>
      <hr/>
      <div>

      <form action="" method="post" enctype="multipart/form-data">
        <input type="file" multiple="" name="file[]" class="span3" /><br />
        <input type="submit" value="Upload"  class="span2">
      </form>
      </div>
    </div>
  </body>
</html>
    '''

@app.route('/delete/<fileid>')
def delete(fileid):
    result=service.files().delete(fileId=fileid).execute()
    return jsonify(res=result)

@app.route('/sendsms')
def sms():
    params = urlencode(
            {'api_key':'e282f7cbe915f6399e627a9469c08562131c82e7','message': 'Hi', 'phone':'+918375847862'})
    response = urlopen("https://api.ringcaptcha.com/imu9yju8ozy4y5u4igob/sms", params)
    return response.read()

if __name__ == '__main__':
    app.run(debug=True,port=4500)
