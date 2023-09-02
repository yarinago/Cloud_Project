import re as regex
from flask import make_response, jsonify

IS_NAME_VALID_REGEX = r'[a-zA-Z]+'
IS_EMAIL_VALID_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
# The API request will work on this table with this key column
TABLE_NAME = "candidates"
KEY_COLUMNS_NAMES = "id"
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
    for key, value in args.items():
        if(key != "action"):
            record[key] = value
    
    response = isParamsValid(record)
    if (response.status_code != 200):
        raise ValueError(response.json["msg"]) 
    
    return record


# Take a list of records_list and create a new json variable that match the columns as key and values from record
# [{"key1": "value1", "key2": "value2", ...}, {"key1": "value11", "key2": "value22", ...}, ...]
def rawToJsonWithColumns(candidates_raw: object, columns: list):
    data_json = []

    for record in candidates_raw:
        record_dict = {}
        for column, value in zip(columns, record):
            record_dict[column] = value
        data_json.append(record_dict)
    
    return data_json