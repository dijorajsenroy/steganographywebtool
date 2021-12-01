import os
from flask import Flask,request, send_file
from flask import render_template,url_for
from werkzeug.utils import secure_filename
from Backend import SteganographyComputation as steg 
cwd = os.getcwd()
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'assets'

@app.route("/")
def index():
    return render_template("homepage.html")

@app.route("/hide",methods=['POST','GET'])
def hide():
    if request.method == 'POST':
        formInfo=request.form
        # obtaining data
        cover_image = request.files['cover']
        password = formInfo['psw']
        secret_msg = formInfo['sec_msg']
        filename = secure_filename(cover_image.filename)
        # saving image
        d = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cover_image.save(d)
        # write secret message to file
        f = open('assets/msgtohide.txt', 'w')
        f.write(secret_msg)
        f.close()
        # Calling encryption module
        obj = steg(d, password)
        obj.LSB_hide('assets/msgtohide.txt', 'assets/enc_output.png') 
        return render_template("homepage.html",result=True)
    return render_template("homepage.html")

@app.route("/download")
def download():
    return render_template("display.html", user_image = 'assets/test.png')


@app.route("/reveal",methods=['POST','GET'])
def reveal():
    if request.method == 'POST':
        formInfo=request.form
        steg_image = request.files['steg_img']
        password = formInfo['psw_rev']
        filename = secure_filename(steg_image.filename)
        d = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        steg_image.save(d)
        # Calling decryption module
        obj = steg(d, password)
        obj.LSB_recover('assets/rec_msg.txt')
        f = open('assets/rec_msg.txt', 'r')
        result_reveal = str(f.read())
        # show results
        return render_template("homepage.html",result_reveal=result_reveal)
    return render_template("homepage.html")


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))

# set FLASK_ENV=development
# set FLASK_APP=app.py
