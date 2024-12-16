from flask import Flask,render_template,request,make_response,session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import login_manager,LoginManager,login_user


app= Flask(__name__)
bcry= Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///datastore.db"
app.config["SECRET_KEY"] = "end"
db=SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Detail(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(60),unique=True)
    email=db.Column(db.String,unique=True)
    password=db.Column(db.String(255),nullable=False)
    active = db.Column(db.Boolean())
with app.app_context():
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
        user=Detail.query.filter_by(email=request.form['email']).first()
        
        if user:
            msg='User is already registered'
            return render_template('index.html',msg=msg,username=user.username)
        user=Detail(username=request.form['username'],email=request.form['email'],password=bcry.generate_password_hash(request.form['password']).decode('utf-8'),active=1)
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
                except Exception as e:
                    msg='Wrong password!'
                    return render_template('login.html',msg=msg)
                    
            else:
                msg='User doesn\'t exits!'
            return render_template('login.html',msg=msg)
        else:
            return render_template('login.html',msg=msg)
@app.route("/logout/<int:id>", methods=['POST','GET'])
def logout(id):
    user = db.get_or_404(Detail, id)
    msg=''
    if request.method == "POST":
        db.session.delete(user)
        session[user.username] = None
        #session.pop('username', None)
        db.session.commit()
        msg='This user '+user.username+' deleted!'
        return render_template('index.html',msg=msg)

    return render_template("logout.html", msg=msg,username='none')
    
if __name__ == '__main__':
    app.run(debug=True) 