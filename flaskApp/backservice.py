import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, make_response, render_template, jsonify
from flaskApp import utils

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
# The API request will work on this table with this primary key column
TABLE_NAME = "candidates"
# The private key column name of the TABLE_NAME
KEY_COLUMNS_NAMES = "id"
# endregion
DB_NOT_WORKING_MSG = f"Connection failed with HOST={DB_HOST}, PORT={DB_PORT}, NAME={DB_NAME}, USERNAME={DB_USERNAME}, password is stored in 'DB_PASSWORD' secret."
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


@app.route("/candidate", methods=["GET"])
def apiHandelGetCandidate():
    query = ""
    candidates_raw = None
    candidates_json = []
    success = "Successful in fetching all candidates"
    error = "Candidates data for GET request not found"
    GET_ALL_CANDIDATES = f"SELECT * FROM {TABLE_NAME} "
    GET_ONE_CANDIDATE = f"SELECT * FROM {TABLE_NAME} WHERE "

    try:
        connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD, options = dbConnectionOptions)
        cur = connection.cursor()

        args = request.args.to_dict() # Store the url query params
        # Get all candidates
        if(args == {}):  
            query = GET_ALL_CANDIDATES               
        # Get one candidates
        else: 
            record = utils.argsToSetOfValues(args) # Process each set of values            
            # SELECT * FROM {TABLE_NAME} WHERE key1=value1 and key2=value2 and ...
            query = GET_ONE_CANDIDATE + " AND ".join(["{}='{}'".format(key, value) for key, value in record.items()]) 
        
        cur.execute(query)
        candidates_raw = cur.fetchall()
        if(candidates_raw):
            candidates_json = utils.rawToJsonWithColumns(candidates_raw, [desc[0] for desc in cur.description])
        else:
            success = f"The request was successfully for this query but no data could be returned: \n {query}"
        return make_response(jsonify({"msg": success, "data": candidates_json}), 200, CONTENT_HEADER)    
    
    except psycopg2.errors.UndefinedTable as exe:
        return make_response(jsonify({"msg": "Table {} not exist. \n {}.".format(TABLE_NAME, str(exe))}), 404, CONTENT_HEADER)
    except Exception as exe:
        return make_response(jsonify({"msg": "An error occurred: {}. \n {}: {}.".format(error, type(exe), str(exe))}), 404, CONTENT_HEADER)
        #TODO: LOG THE ERROR
    finally:
        connection.close()            


@app.route("/candidate", methods=["POST"])
def apiHandelPostCandidate():
    query = ""
    success = "Successful in creating all new candidates"
    error = "Candidates data for POST (creating) request not found"
    values = []
    columns = []
    candidates_raw = None
    candidates_json = []

    try:
        connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD, options = dbConnectionOptions)
        cur = connection.cursor()

        # Store the url query params
        args = request.args.to_dict()                
        # Process each set of values
        record = utils.argsToSetOfValues(args)
        

        # INSERT INTO {TABLE_NAME} (id, first_name, last_name, email, job_id) VALUES (%s, %s, %s, %s, %s)
        for key, value in record.items():
            columns.append(key)
            values.append(f"\'{value}\'")
        query = "INSERT INTO {} ({}) VALUES ({})".format(TABLE_NAME, ", ".join(columns), ", ".join(values))
        
        cur.execute(query + "RETURNING *")
        candidates_raw = cur.fetchall()
        connection.commit()
        if(candidates_raw):
            candidates_json = utils.rawToJsonWithColumns(candidates_raw, [desc[0] for desc in cur.description])
        else:
            success = f"The request was successfully for this query but no data could be returned: \n {query}"
        return make_response(jsonify({"msg": success, "data": candidates_json}), 200, CONTENT_HEADER)
    
    except psycopg2.errors.UndefinedTable as exe:
        return make_response(jsonify({"msg": "Table {} not exist. \n {}.".format(TABLE_NAME, str(exe))}), 404, CONTENT_HEADER)
    except Exception as exe:
        return make_response(jsonify({"msg": "An error occurred: {}. \n {}: {}.".format(error, type(exe), str(exe))}), 404, CONTENT_HEADER)
        #TODO: LOG THE ERROR
    finally:
        connection.close()


@app.route("/candidate", methods=["PUT"])
def apiHandelPutCandidate():
    query = ""
    success = "Successful in updating all new candidates"
    error = "Candidates data for PUT (updating) request not found"
    candidates_raw = None
    candidates_json = []

    try:
        connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD, options = dbConnectionOptions)
        cur = connection.cursor()

        # Store the url query params
        args = request.args.to_dict()
        # Process each set of values
        record = utils.argsToSetOfValues(args)        

        # UPDATE {TABLE_NAME} SET first_name=%s, email=%s, ... WHERE id=%s
        key_value_pairs = ", ".join(["{}='{}'".format(key, value) for key, value in record.items()])            
        query = f"UPDATE {TABLE_NAME} SET {key_value_pairs} WHERE {KEY_COLUMNS_NAMES}='{record.get(KEY_COLUMNS_NAMES)}'"

        cur.execute(query + "RETURNING *")
        candidates_raw = cur.fetchall()
        connection.commit()
        if(candidates_raw):
            candidates_json = utils.rawToJsonWithColumns(candidates_raw, [desc[0] for desc in cur.description])
        else:
            success = f"The request was successfully for this query but no data could be returned: \n {query}"
        return make_response(jsonify({"msg": success, "data": candidates_json}), 200, CONTENT_HEADER)
    
    except psycopg2.errors.UndefinedTable as exe:
        return make_response(jsonify({"msg": "Table {} not exist. \n {}.".format(TABLE_NAME, str(exe))}), 404, CONTENT_HEADER)
    except Exception as exe:
        return make_response(jsonify({"msg": "An error occurred: {}. \n {}: {}.".format(error, type(exe), str(exe))}), 404, CONTENT_HEADER)
        #TODO: LOG THE ERROR
    finally:
        connection.close()

@app.route("/candidate", methods=["DELETE"])
def apiHandelDeleteCandidate():
    query = ""
    candidates_raw = None
    candidates_json = []
    success = "Successful in deleting all candidates"
    error = "Candidates data for DELETE request not found"
    DELETE_ONE_CANDIDATE = f"DELETE FROM {TABLE_NAME} WHERE "

    try:
        connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD, options = dbConnectionOptions)
        cur = connection.cursor()

        # Store the url query params
        args = request.args.to_dict()
        # Process each set of values
        record = utils.argsToSetOfValues(args)                
        # DELETE FROM {TABLE_NAME} WHERE key1=value1 and key2=value2 and ...
        query = DELETE_ONE_CANDIDATE + " AND ".join(["{}='{}'".format(key, value) for key, value in record.items()])
    
        cur.execute(query)
        connection.commit()
        if(candidates_raw):
            candidates_json = utils.rawToJsonWithColumns(candidates_raw, [desc[0] for desc in cur.description])
        else:
            success = f"The request was successfully for this query but no data could be returned: \n {query}"
        return make_response(jsonify({"msg": success, "data": candidates_json}), 200, CONTENT_HEADER)

    except psycopg2.errors.UndefinedTable as exe:
        return make_response(jsonify({"msg": "Table {} not exist. \n {}.".format(TABLE_NAME, str(exe))}), 404, CONTENT_HEADER)
    except Exception as exe:
        return make_response(jsonify({"msg": "An error occurred: {}. \n {}: {}.".format(error, type(exe), str(exe))}), 404, CONTENT_HEADER)
        #TODO: LOG THE ERROR
    finally:
        connection.close()