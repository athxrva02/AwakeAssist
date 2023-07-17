import random
from random import randint
import math
from flask import Flask, render_template, url_for, redirect, Response

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import sqlite3
from sqlite3 import Error
import cv2
import numpy as np
import cv2
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model
import numpy as np
from pygame import mixer


db = SQLAlchemy()
app = Flask(__name__)
bcrypt = Bcrypt(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# db.init_app(app)
app.config['SECRET_KEY'] = 'thisisasecretkey'

app.config['MAIL_SERVER']='smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'dagaonkaratharva@gmail.com'
app.config['MAIL_PASSWORD'] = 'xpdsvfbntqtyjqaa'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(40), nullable = False, unique = True)

with app.app_context():
    db.create_all()

class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=60)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=60)], render_kw={"placeholder": "Password"})

    email = StringField(validators=[
                           InputRequired(), Length(min=4, max=60)], render_kw={"placeholder": "Email"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=60)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=60)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

class ResetForm(FlaskForm):
    email = StringField(validators = [InputRequired(), Length(min=4, max=60)], render_kw={"placeholder": "Email"})
   
    submit = SubmitField('Login')

class OTPForm(FlaskForm):

    otp = StringField(validators=[
                           InputRequired(), Length(min=4, max=60)], render_kw={"placeholder": "OTP"})
    submit = SubmitField('Login')

class ForgetForm(FlaskForm):
    email = StringField(validators=[
                           InputRequired(), Length(min=4, max=60)], render_kw={"placeholder": "email"})
    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=60)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Submit')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    form = ResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            str1 = str(randint(100000,1000000))
            msg = Message('Password Reset', sender = 'dagaonkaratharva@gmail.com', recipients = ['dagaonkaratharva@gmail.com'])
            msg.body = ("Your OTP is " + str1 )
            mail.send(msg)
            # otp(str1)
            return redirect(url_for('otp', variable = str1))
            if form.validate_on_submit():
                usx = form.otp.data
    return render_template('reset.html', form=form)

@app.route('/<variable>/otp/', methods = ['GET', 'POST'])
def otp(variable):
    form = OTPForm()
    if form.validate_on_submit():
        usx = form.otp.data
        if usx == variable:
            return redirect(url_for('forget'))
        else:
            return "Incorrect OTP"
    return render_template('otp.html', form = form)

@app.route('/forget', methods = ['POST', 'GET'])
def forget():
    form = ForgetForm()
    conn = None
    try:
        conn = sqlite3.connect('instance/database.db')
    except Error as e:
        print(e)
    if form.validate_on_submit():
        em = form.email.data
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        task = (hashed_password, em)
        query = 'UPDATE User SET password = ? where email = ?' 
        cur = conn.cursor()
        cur.execute(query, task)
        conn.commit()
        # if True:
        return redirect(url_for('login'))
    return render_template('forget.html', form = form)



@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/drowsy')
@login_required
def drowsy():
    return render_template('drowsy.html')
@app.route('/video_feed')
@login_required
def video_feed():
    return Response(genframes(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password, email = form.email.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)



face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
# model = load_model(r'C:\Users\athar\Drowsiness_Detect\Model\model.h5')
model = load_model(r'C:\Users\athar\Drowsiness_Detect\Model\model.h5') #Insert your own location

mixer.init()
sound= mixer.Sound(r'C:\Users\athar\Drowsiness_Detect\Driver-Drowsiness-Detection-using-Deep-Learning-main\Driver-Drowsiness-Detection-using-Deep-Learning-main\alarm.wav') #Insert your location
cap = cv2.VideoCapture(0)

def genframes():
    Score = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        height,width = frame.shape[0:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces= face_cascade.detectMultiScale(gray, scaleFactor= 1.2, minNeighbors=5)
        eyes= eye_cascade.detectMultiScale(gray, scaleFactor= 1.1, minNeighbors=5)
        
        cv2.rectangle(frame, (0,height-50),(200,height),(0,0,0),thickness=cv2.FILLED)
        
        for (x,y,w,h) in faces:
            cv2.rectangle(frame,pt1=(x,y),pt2=(x+w,y+h), color= (255,0,0), thickness=3 )
            
        for (ex,ey,ew,eh) in eyes:
            #cv2.rectangle(frame,pt1=(ex,ey),pt2=(ex+ew,ey+eh), color= (255,0,0), thickness=3 )
            #cv2.rectangle(frame,pt1=(ex,ey),pt2=(ex+ew,ey+eh), color= (255,0,0), thickness=3 )
            
            # preprocessing steps
            eye= frame[ey:ey+eh,ex:ex+ew]
            eye= cv2.resize(eye,(80,80))
            eye= eye/255
            eye= eye.reshape(80,80,3)
            eye= np.expand_dims(eye,axis=0)
            # preprocessing is done now model prediction
            prediction = model.predict(eye)
            
            print(prediction)
            #if eyes are closed
            if prediction[0][0]>0.50:
                cv2.putText(frame,'closed',(10,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                        thickness=1,lineType=cv2.LINE_AA)
                cv2.putText(frame,'Score'+str(Score),(100,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                        thickness=1,lineType=cv2.LINE_AA)
                Score=Score+1
                if(Score>15):
                    try:
                        sound.play()
                    except:
                        pass
                
            # if eyes are open
            elif prediction[0][1]>0.90:
                cv2.putText(frame,'open',(10,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                        thickness=1,lineType=cv2.LINE_AA)      
                cv2.putText(frame,'Score'+str(Score),(100,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                        thickness=1,lineType=cv2.LINE_AA)
                Score = Score-3
                if (Score<0):
                    Score=0
                    
            else:
                cv2.putText(frame,'closed',(10,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                        thickness=1,lineType=cv2.LINE_AA)
                cv2.putText(frame,'Score'+str(Score),(100,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                        thickness=1,lineType=cv2.LINE_AA)
                Score=Score+1
                if(Score>10):
                    try:
                        sound.play()
                    except:
                        pass
        tmp1, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' 
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')