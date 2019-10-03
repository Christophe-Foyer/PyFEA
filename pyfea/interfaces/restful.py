# -*- coding: utf-8 -*-

from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from flask import jsonify

from waitress import serve
import socket
from contextlib import closing
import threading

#import pandas as pd

app = Flask(__name__)
api = Api(app)

engine = None
port = None

class Server_Data(Resource):
    def get(self):
        
        result = {
                'database': str(engine.url), 
#                'endpoints': api.app.url_map._rules_by_endpoint
                'endpoints': {key:[val.rule for val in value] for key, value 
                              in api.app.url_map._rules_by_endpoint.items()}
                  }
        
        return jsonify(result)

#%% Simulation
#Why is this sotred here? Because otherwise the other file starts getting messy
#if we need a lot more of these we'll move them to their own subfolder

class Assembly_Data(Resource):
    def get(self):
        conn = engine.connect() # connect to database
        query = conn.execute("select * from assembly_data")
        result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
        return jsonify(result)
    
#        query = conn.execute("select * from employees") # This line performs query and returns json result
#        return {'employees': [i[0] for i in query.cursor.fetchall()]} # Fetches first column that is Employee ID

class Part_Data(Resource):
    def get(self):
        conn = engine.connect()
        query = conn.execute("select * from part_data")
        result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
        return jsonify(result)
    
#        query = conn.execute("select trackid, name, composer, unitprice from tracks;")
#        result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
#        return jsonify(result)

class Sim_Data(Resource):
    def get(self):
        conn = engine.connect()
        query = conn.execute("select * from sim_data")
        result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
        return jsonify(result)
    
#        query = conn.execute("select * from employees where EmployeeId =%d "  %int(employee_id))
#        result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
#        return jsonify(result)

#%% Tools        

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

#%% Run
def run(engine_in, **kwargs):
    #This is funky but eh
    global engine
    engine = engine_in
    
    global port
    port = find_free_port()
    
    api.add_resource(Server_Data, '/')
    
    def runserve(app, port):
        serve(app, port=port)
    t = threading.Thread(target=runserve, 
                         args=(app,port))
    t.start()
    
    return 'localhost:' + str(port), t