#!/usr/bin/env python
from os import environ

from app import app, db

db.create_all()
app.run(host='127.0.0.1', port=8000)
