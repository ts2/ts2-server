from flask import Flask, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy



# temp hack to load etc
ALLOWED_IPS = [
    "127.0.0.1"
]

app = Flask(__name__)
db = SQLAlchemy(app)




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username



@app.route("/")
def index():
    return jsonify(info="Hello TS2!",
                remote_address=request.remote_addr,
                HTTP_X_FORWARDED_FOR=request.headers.get('HTTP_X_FORWARDED_FOR'),
                HTTP_X_CLIENT_IP=request.headers.get('HTTP_X_CLIENT_IP'),
    )


@app.route("/db/create")
def db_create():
    db.create_all()
    return jsonify(success=True)

## Run Local
if __name__ == "__main__":
    app.debug = True
    app.run()

