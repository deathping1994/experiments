from __future__ import print_function
from urllib import urlencode, urlopen
from flask import Flask, send_from_directory, jsonify
from flask import Flask, request, redirect, url_for
from googleapiclient.http import BatchHttpRequest
from werkzeug import secure_filename
from apiclient import discovery
import httplib2
import os
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.client import SignedJwtAssertionCredentials

UPLOAD_FOLDER = '/home/gaurav/uploads'
ALLOWED_EXTENSIONS = set(['txt','doc','docx','ppt','pptx','xls','xlsx', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
    app.run(debug=True)
