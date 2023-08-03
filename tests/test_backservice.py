import os
import unittest
from flaskApp import backservice
from flaskApp.backservice import app


#region DB CONNECTION VARIABLES
BASE_URL = os.getenv("BASE_URL")
DB_HOST = os.getenv("DB_HOST") 
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
#endregion
#region CREATE/UPDATE ARGUMENTS VARIABLES
ARGUMENTS_CREATE = "id=1111111111&first_name=yar&last_name=in&email=yarin@gmail.com&job_id=7894561235"
EXPECTED_DATA_CREATE = {'id': 1111111111, 'first_name': 'yar', 'last_name': 'in', 'email': 'yarin@gmail.com', 'job_id': 7894561235}
ARGUMENTS_UPDATE = "id=1111111111&first_name=test&last_name=ing&email=testing@gmail.com&job_id=7894561235"
EXPECTED_DATA_UPDATE = {'id': 1111111111, 'first_name': 'test', 'last_name': 'ing', 'email': 'testing@gmail.com', 'job_id': 7894561235}
#endregion

class TestBackServices(unittest.TestCase):

    # Create a test client to send requests to the app
    def setUp(self):
        self.app = app.test_client()
        self.original_db_password = backservice.DB_PASSWORD
        self.original_db_username = backservice.DB_USERNAME
        self.original_db_host = backservice.DB_HOST

    def tearDown(self):
        # Restore the original values of the environment variables
        backservice.DB_PASSWORD = self.original_db_password
        backservice.DB_USERNAME = self.original_db_username
        backservice.DB_HOST = self.original_db_host
    
    def test_server_is_up(self): 
        response = self.app.get(f"{BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Healthy", response.json['msg'])

    def test_server_incorrect_path(self):
        response = self.app.get(f"{BASE_URL}/invalid")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Route not found", response.json['msg'])

    def test_db_connection_working(self): 
        response = self.app.get(f"{BASE_URL}/ready")
        self.assertEqual(response.status_code, 200)
        self.assertIn("DB connection work", response.json['msg'])

    def test_db_pass_incorrect(self): 
        try:
            # Change the value of DB_PASSWORD for testing
            setattr(self, "original_db_password", "incorrect")
            response = self.app.get(f"{BASE_URL}/ready")
            self.assertEqual(response.status_code, 400)
            self.assertIn("One or more of the connection params is incorrect.", response.json['msg'])
        finally:
            setattr(self, "original_db_password", DB_PASSWORD)

    def test_db_username_incorrect(self):
        try:
            setattr(self, "original_db_username", "incorrect")
            response = self.app.get(f"{BASE_URL}/ready")    
            self.assertEqual(response.status_code, 400)
            self.assertIn("One or more of the connection params is incorrect.", response.json['msg'])
        finally:
            setattr(self, "original_db_username", DB_USERNAME)

    def test_db_not_exist(self):
        try:
            setattr(self, "original_db_host", "incorrect")
            response = self.app.get(f"{BASE_URL}/ready")
            self.assertEqual(response.status_code, 400)
            self.assertIn("One or more of the connection params is incorrect.", response.json['msg'])
        finally:
            setattr(self, "original_db_host", DB_HOST)

    def test_get_all_valid(self):
        try:
            response = self.app.post(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.failIf(response.status_code != 200, "Could not insert value to DB in order to start the test")


            response = self.app.get(f"{BASE_URL}/candidate")
            self.assertEqual(response.status_code, 200)
            self.assertIn(EXPECTED_DATA_CREATE, response.json['data'])
        finally:       
            response = self.app.delete(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.failIf(response.status_code != 200, "Could not delete record from DB in order to do clean up of test")

    def test_get_one_valid(self):
        try:
            response = self.app.post(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.failIf(response.status_code != 200, "Could not insert value to DB in order to start the test")

            response = self.app.get(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)
            self.assertIn(EXPECTED_DATA_CREATE, response.json['data'])
        finally:
            response = self.app.delete(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.failIf(response.status_code != 200, "Could not delete record from DB in order to do clean up of test")

    def test_post_create_new_valid(self):
        try:
            response = self.app.post(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)

            response = self.app.get(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)
            self.assertIn(EXPECTED_DATA_CREATE, response.json['data'])
        finally:
            response = self.app.delete(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.failIf(response.status_code != 200, "Could not delete record from DB in order to do clean up of test")

    def test_post_create_already_exist(self):
        try:
            response = self.app.post(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)                
            response = self.app.get(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)
            self.assertIn(EXPECTED_DATA_CREATE, response.json['data'])

            response = self.app.post(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 404)
            self.assertIn('duplicate key value violates', response.json['msg'])
        finally:
            response = self.app.delete(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.failIf(response.status_code != 200, "Could not delete record from DB in order to do clean up of test")
        
    def test_put_update_valid(self):
        try:
            response = self.app.post(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)        
            response = self.app.get(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)
            self.assertIn(EXPECTED_DATA_CREATE, response.json['data'])

            response = self.app.put(f"{BASE_URL}/candidate?{ARGUMENTS_UPDATE}")
            response = self.app.get(f"{BASE_URL}/candidate?{ARGUMENTS_UPDATE}")
            self.assertEqual(response.status_code, 200)
            self.assertIn(EXPECTED_DATA_UPDATE, response.json['data'])
        finally:
            response = self.app.delete(f"{BASE_URL}/candidate?{ARGUMENTS_UPDATE}")
            self.failIf(response.status_code != 200, "Could not delete record from DB in order to do clean up of test")
        
    def test_delete_valid(self):
        try:
            response = self.app.post(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)                
            response = self.app.get(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)
            self.assertIn(EXPECTED_DATA_CREATE, response.json['data'])
        finally:
            response = self.app.delete(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
            self.assertEqual(response.status_code, 200)
            self.assertIn("no data could be returned", response.json['msg'])

        response = self.app.get(f"{BASE_URL}/candidate?{ARGUMENTS_CREATE}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no data could be returned", response.json['msg'])

    def test_get_req_params_not_valid(self):  
        response = self.app.get(f"{BASE_URL}/candidate?key=1111111111")
        self.assertEqual(response.status_code, 404)
        self.assertIn("argument is not exist", response.json['msg'])

    def test_post_req_params_not_valid(self):
        response = self.app.post(f"{BASE_URL}/candidate?key=1111111111")
        self.assertEqual(response.status_code, 404)
        self.assertIn("argument is not exist", response.json['msg'])

if __name__ == '__main__':
    unittest.main()
