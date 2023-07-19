import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, make_response, render_template, jsonify
from flaskr import helper

load_dotenv()


# region DB CONNECTION VARIABLES
DB_HOST = os.getenv("DB_HOST") 
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
dbConnectionOptions = "-c statement_timeout={}".format(os.getenv("DB_TIMEOUT"))
connection = object
# endregion
# region SQL QUERIES PARAMS
RECORDS_LIMIT = os.getenv("RECORDS_LIMIT")
# The API request will work on this table with this primary key column
TABLE_NAME = os.getenv("TABLE_NAME")
# The private key column name of the TABLE_NAME
KEY_COLUMNS_NAMES = os.getenv("KEY_COLUMNS_NAMES")
# endregion
DB_NOT_WORKING_MSG = f"Connection failed with HOST={DB_HOST}, PORT={DB_PORT}, NAME={DB_NAME}, USERNAME={DB_USERNAME}, password is stored in secret."
CONTENT_HEADER = {"content_type": "application/json; charset=utf-8"}

app = Flask(__name__)


@app.errorhandler(404) 
def invalid_route(e): 
    return make_response(jsonify({'msg' : 'Route not found'}), 404, CONTENT_HEADER)

@app.errorhandler(503)
def server_unavailable(e):
    return make_response(jsonify({'error': 'Server is unavailable'}), 503, CONTENT_HEADER)


@app.route("/")
def homePage():
    # TODO: MAKE SOMETHING ELSE WITH THIS
    return render_template("home.html")


@app.route("/health", methods=["GET"])
def apiHandelHealth():
    return make_response(jsonify({"msg": "Healthy"}), 200, CONTENT_HEADER)


@app.route("/ready", methods=["GET"])
def apiHandelReady():
    connection = None
    try:
        connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD, options = dbConnectionOptions) 
        if (connection.status):
            return make_response(jsonify({"msg": "DB connection work"}), 200, CONTENT_HEADER)  
        else: 
            return make_response(jsonify({"msg": f"DB connection does not work: \n {DB_NOT_WORKING_MSG}"}), 404, CONTENT_HEADER)
    except (psycopg2.OperationalError) as error:
        return make_response(jsonify({"msg": f"{DB_NOT_WORKING_MSG} \n One or more of the connection params is incorrect. \n {error}"}), 400, CONTENT_HEADER)
    except (psycopg2.Error) as error:             
        return make_response(jsonify({"msg": f"{DB_NOT_WORKING_MSG} \n {error}"}), 400, CONTENT_HEADER)
        #TODO: LOG THE ERROR
    finally:
        if(connection is not None):
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
        
        connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD, options = dbConnectionOptions)
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
                return make_response(jsonify({"msg": f"'action' key is not correct. The only valid options are 'create' and 'insert'."}), 404, CONTENT_HEADER) 
            
            query = createQueryByRequestType(args, request.method, action)
            return helper.getResponseFromDB(connection, cur, f"{query} RETURNING *", success, error, request.method)

        if(request.method == "DELETE"):
            success = messages.get("delete", {}).get("success")
            error = messages.get("delete", {}).get("error")
            query = createQueryByRequestType(args, request.method)
            return helper.getResponseFromDB(connection, cur, query, success, error, request.method)

    except psycopg2.errors.UndefinedTable as exe:
        return make_response(jsonify({"msg": "Table {} not exist. \n {}.".format(TABLE_NAME, str(exe))}), 404, CONTENT_HEADER)
    except Exception as exe:
        return make_response(jsonify({"msg": "An error occurred: {}. \n {}.".format(type(exe), str(exe))}), 404, CONTENT_HEADER)
        #TODO: LOG THE ERROR
    finally:
        connection.close()