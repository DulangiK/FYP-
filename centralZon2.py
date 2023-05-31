from flask import Flask, request
import mysql.connector
import math
import requests
import posixpath
import os
import hashlib
import time
import datetime
from datetime import timedelta
import math
from math import cos, pi,sin,acos 
import threading
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler
import central
import json

import psycopg2
try: 
 conn = psycopg2.connect(database="platdb", user="postgres", password="bat123", host="localhost")
 print("connected")
except:
 print ("I am unable to connect to the database")
mycursor =conn.cursor()

a=0

app = Flask(__name__)
node_ip = "127.0.0.1:6003"
port = 6003


@app.route('/')
def index():
    return 'Server Works!'

@app.route('/centralZon', methods=['POST'])
def centralZon():
    input = request.get_json()
    print(input)
    latitude=input['latitude'] 
    longitude=input['longitude']
    vmdID=input['vmdID']

    answer = mycursor.execute("SELECT curr_timestamp, expiry_time FROM vmd_timestamp where vmd_id=%s",(vmdID,))
    answer = mycursor.fetchall()
    for row in answer :
        curr_timestamp=row[0]
        expiry_time=row[1]
   
    current_timestamped = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') 
    
    global a
    if exp_time>current_timestamped and exp_hour<=22:
            a=1
    if exp_time<current_timestamped and exp_hour>22:
            a=1
    else:
        a=0
    #=6371*ACOS(COS(RADIANS(90-D14))*COS(RADIANS(90-D15))+SIN(RADIANS(90-D14))*SIN(RADIANS(90-D15))*COS(RADIANS(E14-E15)))/1.609
    if a==1:
        print("connection established")
        mycursor.execute("INSERT into CentralScript(latitude, longitude, vmdID, current_timestamped) values(%s, %s,%s,%s)", (latitude, longitude, vmdID, current_timestamped))
        conn.commit()
        zoneA_lat = 7.513617    #Westen Zone
        zoneA_longtitude = 80.137133

        zoneB_lat = 6.507628    #Southern Zone
        zoneB_longitude = 80.829782

        zoneC_lat = 7.402797    #Central Zone
        zoneC_longitude = 81.418508

        zoneD_lat = 9.021270    #Northern Zone
        zoneD_longitude = 80.587440

        #Longitude ref value calculation
        Ref_zoneA_lat = (90-zoneA_lat)*(pi/180)
        Ref_zoneB_lat = (90-zoneB_lat)*(pi/180)
        Ref_zoneC_lat = (90-zoneC_lat)*(pi/180)
        Ref_zoneD_lat = (90-zoneD_lat)*(pi/180)

        #latitude ref value calculation 
        Ref_latitude = (90-latitude)*(pi/180)

        #lalilude bitween zone and input calcualtion
        Ref_zoneA_longtitude_input = (zoneA_longtitude - longitude)*(pi/180)
        Ref_zoneB_latitude = (zoneB_longitude - longitude)*(pi/180)
        Ref_zoneC_latitude = (zoneC_longitude - longitude)*(pi/180)
        Ref_zoneD_latitude = (zoneD_longitude - longitude)*(pi/180)

        #distace calculation 
        RefA_X = cos(Ref_zoneA_lat)*cos(Ref_latitude)
        RefA_Y = sin(Ref_zoneA_lat)*sin(Ref_latitude)*cos(Ref_zoneA_longtitude_input)
        distanceA = 6371*acos(RefA_X + RefA_Y)

        RefB_X = cos(Ref_zoneB_lat)*cos(Ref_latitude)
        RefB_Y = sin(Ref_zoneB_lat)*sin(Ref_latitude)*cos(Ref_zoneB_latitude)
        distanceB = 6371*acos(RefB_X + RefB_Y)

        RefC_X = cos(Ref_zoneC_lat)*cos(Ref_latitude)
        RefC_Y = sin(Ref_zoneC_lat)*sin(Ref_latitude)*cos(Ref_zoneC_latitude)
        distanceC = 6371*acos(RefC_X + RefC_Y)

        RefD_X = cos(Ref_zoneD_lat)*cos(Ref_latitude)
        RefD_Y = sin(Ref_zoneD_lat)*sin(Ref_latitude)*cos(Ref_zoneD_latitude)
        distanceD = 6371*acos(RefD_X + RefD_Y)

        if distanceA < 100:
       # zone="West_zone"
       # port=5001
            data = {"zone":"West_zone" ,  
                "port":"5001"}
        elif distanceB < 100:
        #zone="South_zone"
        #port=5005
            data = {"zone":"South_zone" ,  
                "port":"5005"}
        elif distanceC < 100:
        #zone="East_zone"
        #port=5009
            data = {"zone":"East_zone" ,  
                "port":"5009"}
        elif distanceD < 130:
        #zone="North_zone"
        #port=5013
            data = {"zone":"North_zone" ,  
                "port":"5013"}
        else:
            data={"zone":"none"}

        jsdata = json.dumps(data)
        return jsdata
    else:
        print("connection time has expired")
    #return {"zone":zone,"port":port }

#def vmdScript(latitude, longitude, vmd_id):
    #timestamped = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    
    #mycursor.execute("INSERT into CentralScript(latitude, longitude, vmdID, current_timestamped) values(%s, %s,%s,%s)", (latitude, longitude, vmdID, current_timestamped))
    #val = (latitude, longitude, vmd_id, timestamped)
    #mycursor.execute(sql, val)
    #mydb.commit()
@app.route("/getCoordinator", methods=['GET'])
def getCoordinator():
    mycursor.execute("SELECT node_ip, timestamp from coordinator");
    coordinator_raw = mycursor.fetchall()
    return {
        "coordinator_ip": coordinator_raw[0][0]
    }
@app.route("/updateCoordinator", methods=['GET'])
def coordinateMasterNode():
    mycursor.execute("SELECT node_ip, timestamp from coordinator");
    coordinator_raw = mycursor.fetchall()
    conn.commit()
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    if (len(coordinator_raw)>0):
        if coordinator_raw[0][0] == node_ip:
            mycursor.execute("UPDATE coordinator set timestamp=%s where node_ip=%s", (timestamp, node_ip,))
            conn.commit()
        else:
            coordinator_nodeip = coordinator_raw[0][0]
            coordinator_timestamp = coordinator_raw[0][1]
            now = datetime.datetime.now()
            difference = now - coordinator_timestamp
            if difference.total_seconds()>5:
                print("Coordinator expired. Electing current node as the Coordinator")
                mycursor.execute("DELETE from coordinator")
                mycursor.execute("INSERT into coordinator(node_ip, timestamp) values(%s, %s)", (node_ip, timestamp,))
                conn.commit()

    else:
        print("SELECT current node as the Coordinator")
        mycursor.execute("INSERT into coordinator(node_ip, timestamp) values(%s, %s)", (node_ip, timestamp,))
        conn.commit()
    return {}

def runCoordinatorTask():
    coordinateMasterNode()
    sleep(0.5)


scheduler = BackgroundScheduler()
scheduler.add_job(func=coordinateMasterNode, trigger="interval", seconds=1)
scheduler.start()





    
