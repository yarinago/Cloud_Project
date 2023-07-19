import os
import re as regex
from dotenv import load_dotenv
from flask import make_response, jsonify

load_dotenv()

IS_NAME_VALID_REGEX = r'[a-zA-Z]+'
IS_EMAIL_VALID_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
# The API request will work on this table with this key column
TABLE_NAME = os.getenv("TABLE_NAME")
KEY_COLUMNS_NAMES = os.getenv("KEY_COLUMNS_NAMES")
CONTENT_HEADER = {"content_type": "application/json; charset=utf-8"}

# Check if the params given to the api request are valid
def isParamsValid(record: dict):
    error_msgs = []
    COLUMNS_LIST = ['id', 'first_name', 'last_name', 'email', 'job_id']

    for key, value in record.items():
        if key == KEY_COLUMNS_NAMES and (value is None or int(value) < 1000000000 or int(value) > 9999999999):
            error_msgs.append(f"Query {KEY_COLUMNS_NAMES} value is incorrect: {value}")
        elif key == COLUMNS_LIST[1] and (value is None or not regex.fullmatch(IS_NAME_VALID_REGEX, value)):
            error_msgs.append(f"Query first_name value is incorrect: {value}")
        elif key == COLUMNS_LIST[2] and (value is None or not regex.fullmatch(IS_NAME_VALID_REGEX, value)):
            error_msgs.append(f"Query last_name value is incorrect: {value}")
        elif key == COLUMNS_LIST[3] and (value is None or not regex.fullmatch(IS_EMAIL_VALID_REGEX, value)):
            error_msgs.append(f"Query email value is incorrect: {value}")
        elif key == COLUMNS_LIST[4] and (value is None or int(value) < 1000000000 or int(value) > 9999999999):
            error_msgs.append(f"Query job_id value is incorrect: {value}")
        elif (not key in COLUMNS_LIST):
            raise KeyError("{key}={value} argument is not exist", 422)

    if error_msgs:
        return make_response(jsonify({"msg": "\n".join(error_msgs)}), 400, CONTENT_HEADER)
    else:
        return make_response(jsonify({"msg": "Valid"}), 200, CONTENT_HEADER)


# Split args from API request to multiple sets of [id, first_name, last_name, email, job_id] and return list of the sets
def argsToSetOfValues(args: dict):
    # Process each set of values
    record = {}
    records_list = []
    for key, value in args.items():
        # When the table is "candidate" the "id" columns is a most, therefor it is our separator between records_list
        if key == KEY_COLUMNS_NAMES and record:
            # Check Validity of given params
            response = isParamsValid(record)
            if (response.status_code != 200):
                raise ValueError(response.json["msg"]) 
            
            records_list.append(record)
            record.clear()

        if(key != "action"):
            record[key] = value
    
    response = isParamsValid(record)
    if (response.status_code != 200):
        raise ValueError(response.json["msg"]) 
    records_list.append(record) # For the last record OR in case we have only one record
    return records_list


# Take a list of records_list and create a new json variable that match the columns as key and values from record
# [{"key1": "value1", "key2": "value2", ...}, {"key1": "value11", "key2": "value22", ...}, ...]
def dataJsonWithColumns(candidates_raw: object, columns: list):
    data_json = []

    for record in candidates_raw:
        record_dict = {}
        for column, value in zip(columns, record):
            record_dict[column] = value
        data_json.append(record_dict)
    
    return data_json


def getResponseFromDB(connection: object, cur: object, query: list, success_msg: str, error_msg: str, request_type: str) -> tuple:
    is_query_successful = False
    candidates_raw = None
    candidates_json = []
    try:
        cur.execute(query)
        if(request_type in ("GET", "POST")):
            candidates_raw = cur.fetchall()
            is_query_successful = True if candidates_raw is not None else is_query_successful

        if(request_type == "DELETE"):
            is_query_successful = bool(cur.rowcount)

        if(is_query_successful):
            if request_type == "DELETE" or request_type == "POST": connection.commit() 
            if(candidates_raw):
                candidates_json = dataJsonWithColumns(candidates_raw, [desc[0] for desc in cur.description])
            else:
                success_msg = f"The request was successfully for this query but no data could be returned: \n {query}"
            return make_response(jsonify({"msg": success_msg, "data": candidates_json}), 200, CONTENT_HEADER)    
        else:
            return make_response(jsonify({"msg": f"{error_msg}. \n {query}."}), 204, CONTENT_HEADER)
            
    except Exception as exe:
        return make_response(jsonify({"msg": "An error occurred: {}. \n {}.".format(type(exe), str(exe))}), 404, CONTENT_HEADER)
        #TODO: LOG THE ERROR