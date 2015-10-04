# -*- coding: utf-8 -*-
# author: pedromorgan@gmail.com

import os
import json

from fabric.api import env, local, run, lcd, cd, sudo

def run():
    """Run local dev server"""
    os.environ['__TS2_DEV__'] = "1"
    os.environ['OPENSHIFT_POSTGRESQL_DB_URL'] = "postgresql://ts2:ts2@localhost/ts2"
    with lcd("wsgi"):
        local("python ts2.py")

def deploy():
    """Deploy to openshift"""
    local("git push os master")
