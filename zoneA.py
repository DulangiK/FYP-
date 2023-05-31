from flask import Flask, request
import mysql.connector
import math
import requests
import posixpath
import os
import hashlib
import time
import datetime
#import thread
import threading
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="bat123",
    database="platdb"
)
mycursor = mydb.cursor()

zoneA_capacity=0

app = Flask(__name__)

@app.route('/')
def index():
    return 'Server Works!'

@app.route('/zoneAllocation', methods=['POST'])
def zoneAllocation():
    global zoneA_capacity
    if zoneA_capacity<3000 :
        print("connected")
        zoneA_capacity=zoneA_capacity+1
        print(zoneA_capacity)
        input = request.get_json()
        print(input)
        latitude=input['latitude'] 
        longitude=input['longitude']
        vmd_id=input['vmd_id']
        driver_license_id=input['driver_license_id']


        #docker(os)
    else :
        print("connection failed")



    
