from flask import Flask, json,request,redirect,render_template,url_for,jsonify
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import datetime
import os
import secrets
from monero_wallet import json_wallet_cmd

db_uri = os.environ["DATABASE_URL"]

app = Flask(__name__,template_folder='templates')

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(25),nullable = False,unique = True)
    password = db.Column(db.String(25),nullable = False)
    email = db.Column(db.String(100),nullable = False,unique = True)
    orders = db.relationship('Offer',backref ='customer')
    date_created = db.Column(db.DateTime,nullable = False, default = datetime.datetime.utcnow)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    customer_id = db.Column(db.Integer)
    time = db.Column(db.DateTime,default = datetime.datetime.utcnow())
    is_admin = db.Column(db.Boolean,default = True, nullable = False)
    session_id = db.Column(db.String, nullable = False)

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    customer_id = db.Column(db.Integer,db.ForeignKey('customer.id'),nullable = False)
    want = db.Column(db.String(3),nullable = False)
    have = db.Column(db.String(3),nullable = False)
    rate = db.Column(db.Integer,nullable = False)
    time = db.Column(db.DateTime,nullable = False,default = datetime.datetime.utcnow)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'GET':
            return render_template("signup.html")
        elif request.method == 'POST':   
            print(request.form)
            username_input = request.form["username"]
            password_input = request.form["password"]
            email_input = request.form["email"]
            new_query = Customer(username = username_input,
                         password = password_input,
                         email = email_input
                        )
            db.session.add(new_query)
            db.session.commit()
            return redirect(url_for('login'))
    except:
        return jsonify({"error" : "username or email already in use."})
#ImmutableMultiDict([('username', 'amrith'), ('password', 'amrith'), ('email', 'amrith')])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    elif request.method == 'POST':   
        print(request.form)
        username_input = request.form["username"]
        password_input = request.form["password"]
        try:
            new_query = Customer.query.filter_by(username = username_input).first()
            print(new_query)
            if new_query.password == password_input:
                if new_query.username == "a":
                    is_admin = True
                else:
                    is_admin = False
                new_session = secrets.token_urlsafe(16)
                new_session_query = Session(customer_id = new_query.id,
                                time = datetime.datetime.utcnow(),
                                is_admin = is_admin,
                                session_id = new_session
                    )            
                db.session.add(new_session_query)
                db.session.commit()
                return redirect(url_for('admin_dashboard_xmr',session = new_session))
            else:
                return jsonify({"error":"incorrect password"})
            
        except:
            return jsonify({"error":"bad password or username"})
            
        #return 'login'

#ImmutableMultiDict([('username', 'amrith'), ('password', 'amrith')])

@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'GET':
        return render_template("update.html")
    elif request.method == 'POST':   
        print(request.form)
        username_input = request.form["username"]
        password_input = request.form["password"]
        new_password_input = request.form["new_password"]
        try:
            new_query = Customer.query.filter_by(username = username_input).first()
            if new_query.password == password_input:
                new_query.password = new_password_input
                db.session.commit()
                return jsonify({"message" : "password changed :)"})
            else:
                return jsonify({"error":"incorrect password"})
            
        except:
            return jsonify({"error":"bad password or username"})

#ImmutableMultiDict([('username', 'amrith'), ('password', 'amrith'), ('new_password', 'amrith2')])

@app.route('/wipe', methods=['GET', 'POST'])
def wipe():
    if request.method == 'GET':
        return render_template("wipe.html")
    elif request.method == 'POST':   
        print(request.form)
        username_input = request.form["username"]
        password_input = request.form["password"]
        email_input = request.form["email"]
        try:
            new_query = Customer.query.filter_by(username = username_input).first()
            if new_query.password == password_input and new_query.email == email_input:
                db.session.delete(new_query)
                db.session.commit()
                return jsonify({"message" : "account wiped :("})
            else:
                return jsonify({"error":"incorrect password or email"})
            
        except:
            return jsonify({"error":"bad password or username"})
        print(request.form)
        return 'wipe'

#ImmutableMultiDict([('username', 'amrith'), ('password', 'amrith'), ('email', 'amrith')])

@app.route('/admin/monero/<session>')
def admin_dashboard_xmr(session):
    session =  Session.query.filter_by(session_id = session).first()
    session_created = session.time
    time_now = datetime.datetime.utcnow()
    difference = time_now - session_created
    if difference.seconds >= 600:
        return "session expired"
    else:
        if session.is_admin == True:
            return jsonify(json_wallet_cmd())
        else:
            return "hello regular!"


if __name__ == "__main__":
    app.run(debug=True)