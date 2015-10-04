# -*- coding: utf-8 -*-
# author: pedromorgan@gmail.com

import os
import json

from fabric.api import env, local, run, lcd, cd, sudo

def run():
    os.environ['OPENSHIFT_POSTGRESQL_DB_URL'] = "postgresql://ts2:ts2@localhost/ts2"
    with lcd("wsgi"):
        local("python ts2.py")
