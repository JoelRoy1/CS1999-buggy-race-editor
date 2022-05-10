from flask import Flask, render_template, request, jsonify
import os
import sqlite3 as sql
from flask_wtf import FlaskForm
from wtforms import  IntegerField, validators




DATABASE_FILE = "database.db"
DEFAULT_BUGGY_ID = "1"
BUGGY_RACE_SERVER_URL = "https://rhul.buggyrace.net"



con = sql.connect(DATABASE_FILE)
con.row_factory = sql.Row
cur = con.cursor()
cur.execute("SELECT * FROM buggies")
rows = cur.fetchall()

for row in rows:
    print(row[1])