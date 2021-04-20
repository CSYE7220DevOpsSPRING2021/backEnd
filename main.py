from flask import session,Flask, flash, request, jsonify, render_template, redirect, url_for, g, send_from_directory, abort
from flask_cors import CORS
from flask_api import status
from datetime import date, datetime, timedelta
from calendar import monthrange
from dateutil.parser import parse
import pytz
import os
import sys
import time
import uuid
import json
import random
import string
import pathlib
import io
from uuid import UUID
from bson.objectid import ObjectId
import re
from pymongo import MongoClient
from flask_jwt_extended import (create_access_token,current_user,jwt_required,JWTManager,create_refresh_token)
import bcrypt

# mongo configuration
## straight mongo access
## set up mongo
ip="localhost:27017"
if os.getenv("mongoDBip")!=None:
    ip=os.environ.get("mongoDBip",None)
print(ip)
mongo_client = MongoClient(ip)
db = mongo_client['Uber']
Uber_bus = db['Uber']
Uber_user = db['User']
Uber_booking = db['Booking']
# set up apps
app = Flask(__name__)
CORS(app)
jwt = JWTManager(app)
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=10)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(minutes=30)
salt = bcrypt.gensalt()

# jwt config
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]    
    return dict(identity)
# DAO
## user
def verifyUser(username,password):
    user=Uber_user.find_one({"userName":username})
    if user is None or bcrypt.checkpw(password.encode(),salt):
        return None
    return user
def getUser(username):
    user=Uber_user.find_one({"userName":username})
    if user is None:
        return None
    del user["password"]
    return user
def createUser(username,password):
    # # print(Uber_user.find_one({"userName":username}))
    if Uber_user.find_one({"userName":username}) is not None:
        # print(Uber_user.find_one({"userName":username}))
        return None
    try:   
        # print(username,password)     
        user=dict(userName=username,password=str(bcrypt.hashpw(password.encode(),salt)),_id=str(ObjectId()),userType="normal")        
        Uber_user.insert_one(user)
        return user
    except Exception as e:
        # print(e)
        return None
# To be completed, google api not work in China(GFW)
def getEstimateTime(bus):
    bus["EstimateTime"]="3h" 
    return bus
## service
### 
def insertBusToDB(bus):
    Uber_bus.insert_one(bus)
    return bus

def getBusLists(StartTime,EndTime,Depart,Arrive,Number):
    # return None
    # print(Number)
    return list(Uber_bus.find({"Depart":Depart,"Arrive":Arrive,"Departtime":{"$gte":StartTime,"$lte":EndTime},"Number":{"$gte":Number}}))
#### simple transaction!
def bookingProcess(busID,user,Number,contactinfo,status):
    mongosession=mongo_client.start_session()
    mongosession.start_transaction()
    try:
        if status=="confirmed":
            bus=Uber_bus.find_one({"_id":busID})
            if bus is None or int(bus["Number"])<Number:
                raise "No bus found"
            bus["Number"]=int(bus["Number"])-Number
            Uber_bus.update_one({"_id" : bus['_id']},
                {"$set": bus},
                upsert=True)
        else:
            bus=busID
            insertBusToDB(bus)       
        # # print(bus)            
        bd=dict(_id=str(ObjectId()),user_id=user["_id"],Number=Number,contactinfo=contactinfo,busID=bus["_id"],status=status)
        Uber_booking.insert_one(bd)
        mongosession.commit_transaction()
        return jsonify(""),201
    except Exception as e:
        # print(e)
        mongosession.abort_transaction()
        return jsonify("Bus didnt have enough seats"),400
    finally:
        mongosession.end_session()
def deletebookingprocess(bookingID):
    mongosession=mongo_client.start_session()
    mongosession.start_transaction()
    try:
        booking=Uber_booking.find_one({"_id":bookingID})
        # if booking["status"]!="confirmed":
        #     raise "process error"
        bus=Uber_bus.find_one({"_id":booking["busID"]})
        bus["Number"]+=int(booking["Number"])
        if bus["BusType"]=="shared":
            Uber_bus.update_one({"_id" : bus['_id']},
                {"$set": bus},
                upsert=True)
        else:
            Uber_bus.delete_one({"_id" : bus['_id']})
        Uber_booking.delete_one({"_id":bookingID})
        mongosession.commit_transaction()
        return jsonify("successfully delete"),200
    except Exception as e:
        # print(e)
        mongosession.abort_transaction()
        return jsonify("internal error"),500
    finally:
        mongosession.end_session()
def getBookingList(user):
    # print(user)
    booking=list(Uber_booking.find({"user_id":user["_id"]}))
    
    return jsonify(dict(confirmed=booking))
def confirmBookingProcess(bookingID):
    booking=Uber_booking.find_one({"_id":bookingID})
    booking["status"]="confirmed"
    Uber_booking.update_one({"_id" : bookingID},
                {"$set": booking},
                upsert=True)
# route
## docs
@app.route('/doc',methods=['GET'])
def doc():
    return """
        POST:<BR/>
        http://apiurl/user/signin<BR />
        http://apiurl/user/signup<BR />
        http://apiurl/user/refresh<BR />
        http://apiurl/user/bus/insertbus<BR />
        http://apiurl/user/bus/searchbus<BR />
        http://apiurl//booking/bookingexist<BR />
        GET:<BR/>
        http://apiurl/user/getuser<BR />
        http://apiurl/booking/getlist<BR />
    """
## user
### sign in/login
@app.route('/user/signin', methods=['POST'])
def login():
    try:
        request.json['username']
        request.json['password']
    except:
        return jsonify("error input"), 400 
    user=verifyUser(request.json['username'],request.json['password'])  
    if user is None:
        return jsonify("error input:password or username wrong"), 400   
    del user["password"]
    return jsonify(access_token=create_access_token(identity=user,fresh=timedelta(minutes=10)),refresh_token=create_refresh_token(identity=user)), 200
### sign up a user
@app.route('/user/signup', methods=['POST'])
def signup():
    try:
        request.json['username']
        request.json['password']
    except:
        return jsonify("error input"), 400 
    user=createUser(request.json['username'],request.json['password'])     
    if user is None:
        return jsonify("dulpicate user"), 400   
    del user["password"]
    return jsonify(access_token=create_access_token(identity=user,fresh=timedelta(minutes=10)),refresh_token=create_refresh_token(identity=user)), 200
### refresh token
@app.route("/user/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=datetime.timedelta(minutes=15))
    return jsonify(access_token=access_token)
### get user information
@app.route('/user/getUser', methods=['GET'])
@jwt_required(fresh=True)
def getUser():
    # user = get_jwt_identity()
    return jsonify(dict(current_user)), 200
## BUS
@app.route('/bus/insertone',methods=["POST"])
@jwt_required(fresh=True)
def insertBus():
    if(current_user["userType"] != "admin"):
        return jsonify("error access"),401
    json=request.json
    try:
        json["Departtime"]
        json["Number"]
        json["Depart"]
        json["Arrive"]
        json["BusType"]
    except:
        return jsonify("error input1"),400
    try:
        bus=dict(Departtime=datetime.strptime(json["Departtime"],"%Y/%m/%d %H:%M"),Number=int(json["Number"]),Depart=json["Depart"],Arrive=json["Arrive"],_id=str(ObjectId()),BusType=json["BusType"])
        for key in bus:
            if key=="Departtime" or key=="Number":
                continue
            if len(bus[key]) == 0:
                return jsonify("error input1"),400
        
        bus=getEstimateTime(bus)
        insertBusToDB(bus)
        return jsonify(bus),200
    except Exception as e:
        # # print(e)
        return jsonify("error input"),400
@app.route('/bus/searchbus',methods=["POST"])
def searchbus():    
    try:
        StartTime=datetime.strptime(request.json["StartTime"],"%Y/%m/%d %H:%M")
        try:
            EndTime=datetime.strptime(request.json["EndTime"],"%Y/%m/%d %H:%M")
            if StartTime.__ge__(EndTime):
                return jsonify("error"),400
        except Exception as e:
            # print(e)
            EndTime=StartTime+timedelta(days=1)
        Depart=request.json["Depart"]
        Arrive=request.json["Arrive"]
        try:
            Number=int(request.json["Number"])
        except:
            Number=0
    except Exception as e:
        # print(e)
        return jsonify("error"),400
    # return jsonify(data=dict(StartTime=StartTime,EndTime=EndTime,Depart=Depart,Arrive=Arrive))
    busList=getBusLists(StartTime,EndTime,Depart,Arrive,Number)
    return jsonify(data=busList)
@app.route('/booking/bookingexist',methods=["POST"])
@jwt_required(fresh=True)
def bookingExistBus():
    try:
        busID=request.json["busID"]
        user=dict(current_user)
        Number=request.json["Number"]
        contactinfo=request.json["contactinfo"]
        status="confirmed"
        if busID is None or Number is None or contactinfo is None or contactinfo["name"] is None or contactinfo["phone"] is None:
            return jsonify("error input"),400
        try:
            Number=int(Number)
        except:
            return jsonify("error input"),400
        return bookingProcess(busID,user,Number,contactinfo,status)
    except:
        return jsonify("error input"),400
@app.route('/booking/deletebooking',methods=["DELETE"])
@jwt_required(fresh=True)
def deleteBooking():
    try:
        bookingID=request.json["bookingID"]
        return deletebookingprocess(bookingID)
    except:
        return jsonify("error"),400
@app.route('/booking/getlist',methods=["GET"])
@jwt_required(fresh=True)
def getBookings():
    user=dict(current_user)
    return getBookingList(user)
@app.route('/booking/confirm',methods=["PUT"])
@jwt_required(fresh=True)
def confirmBooking():
    try:
        user=dict(current_user)
        if(user["userType"]!="admin"):
            return jsonify(),401
        bookingID=request.json["bookingID"]
        if bookingID is None:
            return jsonify("no id"),400
        confirmBookingProcess(bookingID)
        return jsonify(),204
    except Exception as e:
        print(e)
        return jsonify(),400
@app.route('/booking/createbooking',methods=["POST"])
@jwt_required(fresh=True)
def createBooking():
    try:
        user=dict(current_user)
        Number=request.json["Number"]
        contactinfo=request.json["contactinfo"]
        json=request.json
        try:
            bus=dict(Departtime=datetime.strptime(json["Departtime"],"%Y/%m/%d %H:%M"),Number=int(json["Number"]),Depart=json["Depart"],Arrive=json["Arrive"],_id=str(ObjectId()),BusType="private")
            for key in bus:
                if key=="Departtime" or key=="Number":
                    continue
                if len(bus[key]) == 0:
                    return jsonify("error input1"),400
            
            bus=getEstimateTime(bus)
        except:
            return jsonify("error input2"),400
        if Number is None or contactinfo is None or contactinfo["name"] is None or contactinfo["phone"] is None:
            return jsonify("error input3"),400
        try:
            Number=int(Number)
        except:
            return jsonify("error input4"),400
        return bookingProcess(bus,user,Number,contactinfo,"unconfirmed")
    except Exception as e:
        # print(e)
        return jsonify("error input5"),400


# interceptor
## simple interceptor
def check_value(json):
    for key in json:
        if type(json[key]) is dict:
            value=check_value(json[key])
            if value:
                return value
        elif re.match("[`~!@#$^&*()=|{}':;',\\[\\].<>《》/?~！@#￥……&*（）——|{}【】‘；：”“'。，、？ ]",json[key]):
            return True
@app.before_request
def interceptor():
    if type(request.json) is dict:
        value=check_value(request.json)
        if value==True:
            return jsonify({"status":400,"msg":"input error(Dangerous characters)"})
    # if re.match("[`~!@#$^&*()=|{}':;',\\[\\].<>《》/?~！@#￥……&*（）——|{}【】‘；：”“'。，、？ ]",request.json):
    #     return jsonify({"status":400,"msg":"input error"})
#########
# create a admin user
#########
@app.before_first_request
def before_first_request_func():
    if Uber_user.find_one({"userName":"admin"}) is None:
        Uber_user.insert_one(dict(userName="admin",password=str(bcrypt.hashpw("admin".encode(),salt)),_id=str(ObjectId()),userType="admin"))






if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    