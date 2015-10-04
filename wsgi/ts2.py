
import os

from flask import Flask, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy



# temp hack to load etc
ALLOWED_IPS = [
    "127.0.0.1",
    "84.45.225.28"
]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['OPENSHIFT_POSTGRESQL_DB_URL']

db = SQLAlchemy(app)


# ===========================================
# Models
# ===========================================

class Sim(db.Model):
    __tablename__ = 'sims'
    sim_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    description = db.Column(db.Text())
    version = db.Column(db.Integer)


    def __repr__(self):
        return '<Sim %r>' % self.title


class SimData(db.Model):
    __tablename__ = 'sim_data'
    sim_data_id = db.Column(db.Integer, primary_key=True)
    sim_id = db.Column(db.Integer)
    data = db.Column(db.Text)
    hash = db.Column(db.String(120))
    version = db.Column(db.Integer)


    def __repr__(self):
        return '<Sim %r>' % self.title


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username




def auth_su(req):
    ip = req.headers.get('x-forwarded-for')
    if ip == None:
        return True # hack cos local

    if ip in ALLOWED_IPS:
        return True
    return False



# ===========================================
# Handlers
# ===========================================


@app.route("/")
def index():
    return jsonify(info="Hello TS2!",
                remote_addr=request.headers.get('x-forwarded-for')
    )


@app.route("/db/create")
def db_create():
    if not auth_su(request):
        return jsonify(error="No Auth")
    db.create_all()
    return jsonify(success=True)

@app.route("/db/tables")
def db_tables():
    sql = "SELECT table_name FROM  INFORMATION_SCHEMA.tables "
    sql += "WHERE  table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema');"
    result = db.session.execute(sql)
    tables = []
    for row in result:
        tables.append(row[0])
    return jsonify(success=True, tables=tables)




# =======================================================
## Run Local
if __name__ == "__main__":
    app.debug = True
    app.run()

