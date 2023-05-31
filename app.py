from flask import Flask, request
import mysql.connector
import math
import requests
import posixpath
import os
import hashlib
import time
import datetime

# flask run --port=5002
#
#


mydb = mysql.connector.connect(
	host="localhost",
	user="root",
	passwd="bat123",
	database="platform"
)
mycursor = mydb.cursor()
app = Flask(__name__)

node_ip = "127.0.0.1:5002"

@app.route('/')
def index():
	return 'Server Works!'

@app.route('/zone', methods=['POST'])
def zone():

	input = request.get_json()
	print(input)
	latitude=input['latitude']
	longitude=input['longitude']
	speed=input['speed']
	acceleration=input['acceleration']
	direction=input['direction']
	vehicle_id=input['vehicle_id']
	service_id=input['service_id']

	print(latitude,longitude,speed,acceleration,direction,vehicle_id)
	answer = mycursor.execute("SELECT service_name, ip_address FROM service_and_ip where service_id=%s",(service_id,))
	answer = mycursor.fetchall()
	
	myobj = {'latitude': latitude,'longitude': longitude,'speed': speed,'acceleration': acceleration,'direction': direction,'vehicle_id': vehicle_id}
	print(answer)
	x = requests.post('http://'+answer[0][1]+'/'+answer[0][0] ,json=myobj)

	return x.json()

cpu_weight = 0.4
memory_weight = 0.6
@app.route('/getCapacity', methods=['POST'])
def findNodeCapacity():
	capacity = psutil.cpu_percent(interval=1)*cpu_weight + psutil.virtual_memory().percent*memory_weight
	return {
		"capacity": capacity
	}


@app.route('/getZone', methods=['POST'])
def getZone():
	input = request.get_json()
	vehicle_id = input['vehicle_id']
	mycursor.execute("SELECT zone_id, zone_ip from vehicle_zone_mapping where vehicle_id=%s", (vehicle_id))
	zone_data = mycursor.fetchall()
	return {
		"zone_id": zone_data[0][0],
		"zone_ip": zone_data[0][1]
	}

@app.route('/updateZone', methods=['POST'])
def central():
	input = request.get_json()
	current_latitude = input['latitude']
	current_longitude = input['longitude']
	vehicle_id = input['vehicle_id']

	mycursor.execute("SELECT service, computing_capacity from priority_service")
	priority_service = mycursor.fetchall()
	zone_list = []

	for service in priority_service:
		capacity = service[1]
		assigned_zone = findClosedRoute(current_latitude, current_longitude, capacity)
		mycursor.execute("SELECT ip from zone_ip_table where zone_id=%s", (assigned_zone,))
		zone_ip = mycursor.fetchall()[0][0]
		print(zone_ip)
		mycursor.execute("SELECT zone_id from vehicle_zone_mapping where vehicle_id=%s", (vehicle_id,))
		previous_vehicle_zone = mycursor.fetchall()
		if len(previous_vehicle_zone) == 0:
			mycursor.execute("INSERT INTO vehicle_zone_mapping(vehicle_id, zone_id, zone_ip) VALUES(%s, %s, %s)", (vehicle_id, assigned_zone, zone_ip))
			mydb.commit()
		else:
			mycursor.execute("UPDATE vehicle_zone_mapping SET zone_id=%s, zone_ip=%s where vehicle_id=%s", (assigned_zone, zone_ip, vehicle_id))
			mydb.commit()
		zone_list.append({
			"service": service[0],
			"zone_ip": zone_ip
			})
	return {
		"zone_list": zone_list
	}

def findClosedRoute(current_latitude, current_longitude, max_capacity):
	print("Find zone with max capacity " + str(max_capacity))
	mycursor.execute("SELECT zone_latitude, zone_longitude, zone_id FROM zones where capacity_usage>%s" ,(max_capacity,))
	zone_segment = mycursor.fetchall()
	print(zone_segment)
	min_distance = float("inf")
	min_zone_id = 0
	for segment in zone_segment:
		segment_longitude = segment[0]
		segment_latitude = segment[1]
		distance = math.sqrt((segment_latitude - current_latitude)**2 + (segment_longitude - current_longitude)**2)
		if distance < min_distance:
			min_distance = distance
			min_zone_id = segment[2]
	print("Closest zone found at " + str(min_zone_id))
	return min_zone_id

def takeSecond(elem):
    return elem[1]

@app.route('/authUser', methods=['POST'])
def authenticateUser():
	input = request.get_json()
	username = input['username']
	password = input['password']
	
	mycursor.execute("select password, salt from user where username = %s", (username,))
	user_result = mycursor.fetchall()
	print(user_result)

	salt = os.urandom(32)
	input_password = getSaltedHashPassword("abcd", salt)
	mycursor.execute("INSERT INTO user(username, password, salt) value(%s, %s, %s)", (username,input_password,salt,))
	mycursor.commit()

	return {}

@app.route("/createUser", methods=['POST'])
def createUser():
	input = request.get_json()
	username = input['username']
	password = input['password']
	salt = os.urandom(32)
	slatedPassword = getSaltedHashPassword(password, salt)
	print(slatedPassword)
	#mycursor.execute("INSERT INTO user(username, password, salt) value(%s, %s, %s)", (username,slatedPassword,salt,))
	#mycursor.commit()
	return {"status": "success"}

def getSaltedHashPassword(password, salt):
	
	return str(hash(password+salt))

@app.route("/getCoordinator", methods=['GET'])
def getCoordinator():
	mycursor.execute("select node_ip, timestamp from coordinator");
	coordinator_raw = mycursor.fetchall()
	return {
		"coordinator_ip": coordinator_raw[0][0]
	}

@app.route("/coordinate", methods=['GET'])
def coordinateMasterNode():
	mycursor.execute("select node_ip, timestamp from coordinator");
	coordinator_raw = mycursor.fetchall()
	ts = time.time()
	timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
	print(coordinator_raw)
	if (len(coordinator_raw)>0):
		print(coordinator_raw[0][1])
		coordinator_nodeip = coordinator_raw[0][0]
		coordinator_timestamp = coordinator_raw[0][1]
		now = datetime.datetime.now()
		difference = now - coordinator_timestamp
		print(difference.total_seconds())
		if difference.total_seconds()>5:
			print("Coordinator expired. Electing current node as the Coordinator")
			mycursor.execute("insert into coordinator(node_ip, timestamp) values(%s, %s)", (node_ip, timestamp,))
			mydb.commit()

	else:
		mycursor.execute("insert into coordinator(node_ip, timestamp) values(%s, %s)", (node_ip, timestamp,))
		mydb.commit()
	
	return {}
