import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, make_response, render_template, jsonify
import helper

load_dotenv()

app = Flask(__name__)

SERVER = os.getenv("SERVER") 
DB_URL = os.getenv("DATABASE_URL") # TODO: SWITCH TO SERVER-USERNAME-PASSWORD USE
DB_USERNAME = os.getenv("USERNAME")
RECORDS_LIMIT = os.getenv("RECORDS_LIMIT")
# The API request will work on this table with this key column
TABLE_NAME = os.getenv("TABLE_NAME")
KEY_COLUMNS_NAMES = os.getenv("KEY_COLUMNS_NAMES")
# DB_PASSWORD = GET FROM GITHUB
dbConnectionOptions = "-c statement_timeout={}".format(os.getenv("DB_TIMEOUT"))
DB_NOT_WORKING_MSG = f"Connection failed with SERVER = {SERVER}, USERNAME = {DB_USERNAME}, password is stored in secret."
connection = object


@app.route("/")
def homePage():
    # TODO: MAKE SOMETHING ELSE WITH THIS
    return render_template("home.html")


@app.route("/health", methods=["GET"])
def apiHandelHealth():
    return make_response(jsonify({"msg": "Healthy"}), 200)


@app.route("/ready", methods=["GET"])
def apiHandelReady():
    try:
        # TODO: SWITCH TO SERVER-USERNAME-PASSWORD USE
        # connection = psycopg2.connect(database=SERVER, user=DB_USERNAME, password=DB_PASSWORD, options=dbConnectionOptions)
        connection = psycopg2.connect(DB_URL, options = dbConnectionOptions) 
        if (connection.status):
            return make_response(jsonify({"msg": "DB connection work"}), 200)  
        else: 
            return make_response(jsonify({"msg": f"DB connection does not work: \n {DB_NOT_WORKING_MSG}"}), 404)
    except (psycopg2.Error) as error:             
            make_response(jsonify({"msg": f"{DB_NOT_WORKING_MSG} \n {error}"}), 400)
            #TODO: LOG THE ERROR
    finally:
        connection.close()


# Return all the records that match the args parameters
def createQueryByRequestType(args: dict, request_type: str, action: str = None):
    query = ""

    # Process each set of values
    results = helper.argsToSetOfValues(args)
    
    #TODO: THIS METHOD SEEMS VERY WASTEFULLY BECAUSE WE CREATE NEW STRING EACH TIME
    if(request_type == "GET" or request_type == "DELETE"):

        query = f"SELECT * FROM {TABLE_NAME} WHERE " if request_type == "GET" else f"DELETE FROM {TABLE_NAME} WHERE "
        # SELECT * FROM TABLE_NAME WHERE (key1=value1 and key2=value2 and ...) or (key11=value11 and key22=value22 and ...) or ...
        conditions = []
        for record in results:
            condition = " AND ".join(["{}='{}'".format(key, value) for key, value in record.items()])
            conditions.append(f"({condition})")

        query += " OR ".join(conditions)        
        return query
    
    if(request_type == "POST"):
        values = []
        # INSERT INTO TABLE_NAME(id, first_name, last_name, email, job_id) VALUES (%s, %s, %s, %s, %s)
        # values = [('value1', 'value2', None, None), ('value3', None, 'value4', None), ('value5', 'value6', 'value7', 'value8')]
        if action == "create":
            values = []
            columns = []
            for record in results:
                for key, value in record.items():
                    columns.append(key)
                    values.append(f"\'{value}\'")
            
            query = "INSERT INTO {} ({}) VALUES ({})".format(TABLE_NAME, ", ".join(columns), ", ".join(values))

        if(action == "update"):
            conditions = []
            for record in results:
                key_value_pairs = ", ".join(["{}='{}'".format(key, value) for key, value in record.items()])
            
            query = "UPDATE {} SET {} WHERE {}='{}'".format(TABLE_NAME, key_value_pairs, KEY_COLUMNS_NAMES, record.get(KEY_COLUMNS_NAMES))
        
        return query


@app.route("/candidate", methods=["GET", "POST", "DELETE"])
def apiHandelCandidate():
    GET_ALL_CANDIDATES = f"SELECT * FROM {TABLE_NAME} "
    # TODO: CHANGE THE 100 TO A VARIABLE FROM USERS WITH DEFAULT OF 100
    
    messages = {
        "get": {
            "success": "Successful in fetching all candidates",
            "error": "Candidates data for GET request not found"
        },
        "create": {
            "success": "Successful in creating all new candidates",
            "error": "Candidates data for POST (create) request not found"
        },
        "update": {
            "success": "Successful in updating all candidates",
            "error": "Candidates data for POST (update) request not found"
        },
        "delete": {
            "success": "Successful in deleting all candidates",
            "error": "Candidates data for DELETE request not found"
        }
    }
    query = ""
    success = ""
    error = ""

    try:
        # Store the url query params
        args = request.args.to_dict() 
        
        # Check connectivity to DB
        getReady = apiHandelReady()
        if(getReady.status_code != 200):
            return getReady
        
        # TODO: SWITCH TO SERVER-USERNAME-PASSWORD USE
        # connection = psycopg2.connect(database=SERVER, user=DB_USERNAME, password=DB_PASSWORD, options=dbConnectionOptions)
        connection = psycopg2.connect(DB_URL, options = dbConnectionOptions) 
        cur = connection.cursor()
        
        if(request.method == "GET"):  
            success = messages.get("get", {}).get("success")         
            error =  messages.get("get", {}).get("error")

            if(args == {}): # Get all candidates               
                return helper.getResponseFromDB(connection, cur, GET_ALL_CANDIDATES + RECORDS_LIMIT, success, error, request.method)
            else: # Get one/many candidates
                query = createQueryByRequestType(args, request.method)
                return helper.getResponseFromDB(connection, cur, f"{query} {RECORDS_LIMIT}", success, error, request.method)
                
        if(request.method == "POST"):
            action = args.pop("action") # action=update or action=create
            
            if(action == "create"):
                success = messages.get("create", {}).get("success")
                error = messages.get("create", {}).get("error")  
            elif(action == "update"):
                success = messages.get("update", {}).get("success")
                error = messages.get("update", {}).get("error")
            else:
                return make_response(jsonify({"msg": f"'action' key is not correct. The only valid options are 'create' and 'insert'."}), 404) 
            
            query = createQueryByRequestType(args, request.method, action)
            return helper.getResponseFromDB(connection, cur, f"{query} RETURNING *", success, error, request.method)

        if(request.method == "DELETE"):
            success = messages.get("delete", {}).get("success")
            error = messages.get("delete", {}).get("error")
            query = createQueryByRequestType(args, request.method)
            return helper.getResponseFromDB(connection, cur, query, success, error, request.method)

    except Exception as exe:
        return make_response(jsonify({"msg": "And error occurred: {}. \n {}.".format(type(exe), str(exe))}), 404)
        #TODO: LOG THE ERROR
    finally:
        connection.close()



# RUN THE FLASK APP:
#   python -m flask run
#   python -m --host=0.0.0.0 --port=80 flask run 
# OVERRIDE THE REQUIREMENT FILE:
#   pip freeze > requirement.txt
# QUERY FOR THE REQUEST: 
# # ?id=INT&first_name=VARCHAR&last_name=VARCHAR&email=VARCHAR&job_id=INT
