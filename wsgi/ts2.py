
import os
import requests
import zipfile
import StringIO
import json
import hashlib
import datetime

from flask import Flask, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

LOCAL = bool(os.environ.get('__TS2_DEV__'))


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
    filename = db.Column(db.String(120))
    title = db.Column(db.String(120))
    description = db.Column(db.Text())
    curr_version = db.Column(db.String(10))

    def __repr__(self):
        return '<Sim %r>' % self.title


class SimData(db.Model):
    __tablename__ = 'sim_data'
    sim_data_id = db.Column(db.Integer, primary_key=True)
    sim_id = db.Column(db.Integer)
    data = db.Column(db.Text)
    hash = db.Column(db.String(120))
    data_version = db.Column(db.String(10))
    dated = db.Column(db.DateTime())
    source = db.Column(db.String(50))

    def __repr__(self):
        return '<SimData %r>' % self.data_version



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
    return jsonify(info="Hello TS2",
                remote_addr=request.headers.get('x-forwarded-for')
    )

@app.route("/ajax/sims")
def ajax_sims():

    sql = """
    SELECT
        sim_data.sim_data_id, sim_data.sim_id,
        sims.filename, sims.title, sims.description,
        sim_data.dated, sim_data.hash
    FROM sim_data
    inner join sims on sim_data.sim_id = sims.sim_id
    where dated = (select max(dated) from sim_data where sim_data.sim_id = sims.sim_id)
    order by sim_data.dated desc

    """
    result = db.session.execute(sql)
    sims = []
    for row in result:
        sims.append( dict(filename=row[2], title=row[3], description=row[4],
                          dated=row[5], hash=row[6]) )

    return jsonify( sims=sims  )



@app.route("/ajax/pull_git_zip")
def pull_git_zip():
    if not auth_su(request):
        return jsonify(error="No Auth")

    ## Fetch remote zip
    url = 'http://localhost/~ts2/ts2-data-master.zip' if LOCAL else 'https://github.com/ts2/ts2-data/archive/master.zip'
    r = requests.get(url)
    zippy = zipfile.ZipFile(StringIO.StringIO(r.content))

    imported = 0
    updated = 0
    files_list = []
    for filepath in zippy.namelist():
        if filepath.endswith(".ts2") or filepath.endswith(".json"):
            filename = os.path.basename(filepath)
            files_list.append(filename)
            data = json.loads( zippy.read(filepath) )
            opts =  data['options']

            sim_blob = json.dumps(data, sort_keys=True, indent=4)
            sha = hashlib.sha1()
            sha.update(sim_blob)
            hash = sha.hexdigest()

            sim = db.session.query(Sim).filter_by(filename=filename).first()
            if sim == None:
                sim = Sim()
                sim.filename = filename
                db.session.add(sim)


            sim.title = opts['title']
            sim.description = opts['description']
            db.session.commit()

            simdata = db.session.query(SimData).filter_by(sim_id=sim.sim_id, hash=hash).order_by(SimData.data_version.desc()).first()
            if simdata == None:
                simdata = SimData()
                simdata.sim_id = sim.sim_id
                db.session.add(simdata)
                imported += 1
            else:
                updated += 1
            simdata.data = sim_blob

            simdata.hash = hash
            simdata.data_version = opts['version']
            simdata.dated = datetime.datetime.utcnow()
            simdata.source = "ts2-data-master.zip"
            db.session.commit()




    return jsonify(success=True, files_list = sorted(files_list), updated=updated,  imported=imported)


# ==============================================
# Database Stuff
@app.route("/ajax/db/create_tables")
def db_create_tables():
    if not auth_su(request):
        return jsonify(error="No Auth")
    db.drop_all()
    db.create_all()

    sql = """
    CREATE OR REPLACE VIEW v_sims AS
    SELECT
        simdata.sim_data_id, simdata.sims.sim_id,
        sims.filename, sims.title, sims.description,
        simsdata.dated
    FROM simdata
    inner join sims on simdata.sim_id = sims.sim_id
    where dated = (select max(dated) from simsdata where simdata.sim_id = sims.sim_id)
    """

    return jsonify(success=True)

@app.route("/ajax/db/create_views")
def db_create_views():


    sql = """
    CREATE OR REPLACE VIEW v_sims AS
    SELECT
        sim_data.sim_data_id, sim_data.sim_id,
        sims.filename, sims.title, sims.description,
        sim_data.dated
    FROM sim_data
    inner join sims on sim_data.sim_id = sims.sim_id
    where dated = (select max(dated) from sim_data where sim_data.sim_id = sims.sim_id);
    """
    db.session.execute(sql)

    return jsonify(success=True)


@app.route("/ajax/db/tables")
def db_tables():

    sql_cols = text("select column_name, ordinal_position, data_type, is_nullable from INFORMATION_SCHEMA.COLUMNS where table_name = :table")


    sql = "SELECT table_name FROM  INFORMATION_SCHEMA.tables "
    sql += "WHERE  table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema');"
    result = db.session.execute(sql)
    tables = []
    for row in result:
        cols = []
        result_cols = db.session.execute(sql_cols, dict(table=row[0]))
        for crow in result_cols:
            cols.append( dict(name=crow[0], type=crow[2], nullable=crow[3] == "YES"))
        tables.append( dict(table=row[0], cols=cols) )
    return jsonify(success=True, tables=tables)




# =======================================================
## Run Local
if __name__ == "__main__":

    ### Run this with fabric in root dir as it sets environment. `fab run`

    app.debug = True
    app.run(port=5555)

