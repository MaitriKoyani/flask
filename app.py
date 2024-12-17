from flask import Flask,render_template,request,make_response,session,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import login_manager,LoginManager
from sqlalchemy import text
from datetime import date,time,datetime

app= Flask(__name__)
bcry= Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///Timeline.db"
app.config["SECRET_KEY"] = "end"
db=SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Detail(db.Model):
    __tablename__ = 'detail'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String(255), nullable=False)

    # Relationship with logs
    logs = db.relationship('Log', backref='user', lazy=True)

class Log(db.Model):
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    timein = db.Column(db.Time, nullable=False)
    timeout = db.Column(db.Time, nullable=False)
    task = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    hours = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('detail.id'), nullable=False, index=True)

    # Unique constraint for one log per date per user
    __table_args__ = (db.UniqueConstraint('date', 'user_id', name='unique_date_user'),)


with app.app_context():
    # db.session.execute(text('DROP TABLE IF EXISTS datastore;'))
    # db.session.commit()
    # print("Table deleted successfully.")

    db.create_all()

@login_manager.user_loader
def loader_user(user_id):
    return Detail.query.get(user_id)

@app.route('/')
def index():
    count = int(request.cookies.get('visitors count', 0))
    count = count+1
    output = 'You visited this page for '+str(count) + ' times'
    resp = make_response(render_template('index.html',msg='', resp=output)) 
    resp.set_cookie('visitors count', str(count))
    return resp


@app.route('/register',methods=['POST','GET'])
def register():
    msg=''
    if request.method == 'POST':
        user=Detail.query.filter_by(username=request.form['username']).first()
        email=Detail.query.filter_by(email=request.form['email']).first()
        if user and email:
            if user.username==email.username:
                if user.password==request.form['password']:
                    msg=' is already registered , please login!'
                    return render_template('welcome.html',msg=msg,username=user.username)
                else:
                    msg='Password is wrong but user exists so please login!'
                    return render_template('register.html',msg=msg)
            else:
                msg='Please change your username and email both are exists!'
                return render_template('register.html',msg=msg)
        elif user:
            if user.email!=request.form['email']:
                msg='Username already exists , please change your username!'
                return render_template('register.html',msg=msg)
        elif email:
            if email.username!=request.form['username']:
                msg='Email already exists , please change your Email!'
                return render_template('register.html',msg=msg)
        else:
            user=Detail(username=request.form['username'],email=request.form['email'],password=bcry.generate_password_hash(request.form['password']).decode('utf-8'))
            db.session.add(user)
            db.session.commit()
            
            msg=' registration successful'
            
            return render_template('welcome.html',username=user.username,msg=msg)
    else:
        return render_template('register.html',msg=msg)

@app.route('/login',methods=['POST','GET'])
def login():
    msg=''
    if 'username' in session:
        msg='you are already logged in'
        return render_template('welcome.html',username=session['username'],msg=msg)
    else:
        if request.method == 'POST':
            user=Detail.query.filter_by(username=request.form['username']).first()
            if user:
                try:
                    if bcry.check_password_hash (user.password, request.form['password']):
                
                        msg=' login successful'
                        session['username']=user.username
                        
                        return render_template('welcome.html',username=user.username,msg=msg)
                    else:
                        msg='Wrong password!'
                        return render_template('login.html',msg=msg)
                except Exception as e:
                    msg='Wrong password!'
                    return render_template('login.html',msg=msg)
                    
            else:
                msg='User doesn\'t exits!'
            return render_template('login.html',msg=msg)
        else:
            return render_template('login.html',msg=msg)
@app.route("/logout")
def logout():
    msg=''
    if 'username' in session:
        session.pop('username', None)
        msg='This user was logout!'
        return render_template('index.html',msg=msg)
    else:
        msg='User isn\'t logged in!'
        return render_template('index.html',msg=msg)
    

@app.route('/addlog', methods=['POST','GET'])
def addlog():
    msg=''
    if 'username' in session:
        if request.method == 'POST':
            log=Log.query.filter_by(date=request.form['date']).first()
            if log:
                msg='The log of this date is added , Please change the date!'
                return render_template('addlog.html', msg=msg)
            else:
                user=Detail.query.filter_by(username=session['username']).first()
                
                log=Log(date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),timein=datetime.strptime(request.form['timein'],'%H:%M').time(),timeout=datetime.strptime(request.form['timeout'],'%H:%M').time(),task=request.form['task'],description=request.form['description'],hours=float(request.form['hours']),user_id=user.id)
                db.session.add(log)
                db.session.commit()
                msg='Log added successfully'
                return redirect(url_for('viewlog'))
        log=''
        return render_template('addlog.html',username=session['username'],l=log)
    else:
        return redirect(url_for('login'))

    
@app.route('/viewlog',methods=['GET'])
def viewlog():
    if 'username' in session:
        user=Detail.query.filter_by(username=session['username']).first()
        us=user.id
        log=Log.query.filter_by(user_id=us).all()
        
        return render_template('viewlog.html',log=log,username=user.username,coun=len(log))
    else:
        return redirect(url_for('login'))
@app.route('/updatelog/<int:id>',methods=['GET','POST'])
def updatelog(id):
    log=Log.query.filter_by(id=id).first()
    user=Detail.query.filter_by(id=log.user_id).first()
    if request.method == 'POST':
        log.date=datetime.strptime(request.form['date'],'%Y-%m-%d').date()
        try:
            log.timein=datetime.strptime(request.form['timein'],'%H:%M:%S').time()
        except ValueError:
            log.timein=datetime.strptime(request.form['timein'],'%H:%M').time()
        try:
            log.timeout=datetime.strptime(request.form['timeout'],'%H:%M:%S').time()
        except ValueError:
            log.timeout=datetime.strptime(request.form['timeout'],'%H:%M').time()

        log.task=request.form['task']
        log.description=request.form['description']
        log.hours=float(request.form['hours'])
        log.user_id=log.user_id
        db.session.commit()
        msg='Log added successfully'
        return redirect(url_for('viewlog'))
    return render_template('addlog.html',l=log,username=user.username)

@app.route('/deletelog/<int:id>',methods=['GET'])
def deletelog(id):
    log=Log.query.filter_by(id=id).first()
    db.session.delete(log)
    db.session.commit()
    print('log deleted successfully')
    return redirect(url_for('viewlog'))

if __name__ == '__main__':
    app.run(debug=True) 
