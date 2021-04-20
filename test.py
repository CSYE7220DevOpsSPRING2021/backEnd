import unittest
from main import app,Uber_bus,Uber_booking,Uber_user
import json
class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls): 
        Uber_bus.delete_many({})
        Uber_booking.delete_many({})
        Uber_user.delete_many({})
    # test init    
    def setUp(self):
        app.testing=True
        self.client=app.test_client()       
           
    # end test
    def tearDown(self):
        pass             
    # testing    
    def test_1_interceptor(self):
        response = self.client.post("/user/signup",json={"user":"<"})
        resp_dict = json.loads(response.data)
        self.assertIn("status", resp_dict)
        code = resp_dict.get("status")
        self.assertEqual(code,400)
    def test_2_signUp(self):
        # no data
        response = self.client.post("/user/signup",json={})
        self.assertIn("400",response.status)
        # # create one
        response = self.client.post("/user/signup",json={"username":"majun","password":"123456"})
        resp_dict = json.loads(response.data)
        self.assertIn("200",response.status)
        self.assertIn("access_token",resp_dict)
        self.assertIn("refresh_token",resp_dict)
        # duplicate
        response = self.client.post("/user/signup",json={"username":"majun","password":"123456"})
        self.assertIn("400",response.status)
    def test_3_signIn_user(self):
        # test user
        response = self.client.post("/user/signin",json={"username":"majun","password":"123456"})        
        resp_dict = json.loads(response.data)
        self.assertIn("200",response.status)
        self.assertIn("access_token",resp_dict)
        self.assertIn("refresh_token",resp_dict)
        # test admin
        response = self.client.post("/user/signin",json={"username":"admin","password":"admin"})
        resp_dict = json.loads(response.data)
        self.assertIn("200",response.status)
        self.assertIn("access_token",resp_dict)
        self.assertIn("refresh_token",resp_dict)
        
        # client=APIClient()
        # client.credentials(HTTP_AUTHORIZATION='Bearer '+resp_dict["access_token"])
        response = self.client.get("/user/getUser",headers={'Authorization':"Bearer "+resp_dict["access_token"]})
        resp_dict = json.loads(response.data)
        self.assertIn("200",response.status)
        self.assertIn("userName",resp_dict)
    def test_4_insertBus(self):
        # no auth
        demobus=dict(
            Departtime="2021/01/01 00:00",
            Number="100",
            Depart="Boston",
            Arrive="New York",
            BusType="shared"
        )
        response =self.client.post("/bus/insertone",json=demobus)
        self.assertIn("401",response.status)
        # get auth token
        response = self.client.post("/user/signin",json={"username":"admin","password":"admin"})
        resp_dict = json.loads(response.data)
        self.assertIn("200",response.status)
        self.assertIn("access_token",resp_dict)
        # insert with auth
        response =self.client.post("/bus/insertone",json=demobus,headers={'Authorization':"Bearer "+resp_dict["access_token"]})
        self.assertIn("200",response.status)
    def test_5_search_booking(self):
        # demo query
        demobus=dict(
            StartTime="2020/12/31 01:00",
            EndTime="2021/01/01 02:00",
            Number="102",
            Depart="Boston",
            Arrive="New York",
        )
        response = self.client.post("/user/signin",json={"username":"majun","password":"123456"})
        resp_dict = json.loads(response.data)
        self.assertIn("200",response.status)
        self.assertIn("access_token",resp_dict)
        header={'Authorization':"Bearer "+resp_dict["access_token"]}
        response = self.client.post("/bus/searchbus",json=demobus,headers=header)
        self.assertIn("200",response.status)
        self.assertEqual(0,len(json.loads(response.data)["data"]))
        demobus["Number"]="20"
        response = self.client.post("/bus/searchbus",json=demobus,headers=header)
        self.assertIn("200",response.status)
        data=json.loads(response.data)["data"]
        self.assertEqual(1,len(data))
        self.assertIn("_id",data[0])        
        # booking
        bus=dict(
            busID=data[0]["_id"],
            Number="20",
            contactinfo={"name":"1","phone":"1"}
        )
        response = self.client.post("/booking/bookingexist",json=bus,headers=header)
        self.assertIn("201",response.status)
        response = self.client.post("/bus/searchbus",json=demobus)
        self.assertIn("200",response.status)
        data=json.loads(response.data)["data"]
        self.assertEqual(1,len(data))
        self.assertIn("Number",data[0])  
        self.assertEqual(80,data[0]["Number"])
        # get booking
        response = self.client.get("/booking/getlist",headers=header)
        data=json.loads(response.data)
        self.assertIn("confirmed",data)
        self.assertEqual(1,len(data["confirmed"]))
        self.assertIn("_id",data["confirmed"][0])
        # delete booking
        bookingID=data["confirmed"][0]["_id"]
        response = self.client.delete("/booking/deletebooking",json={"bookingID":bookingID},headers=header)
        self.assertIn("200",response.status)
        response = self.client.post("/bus/searchbus",json=demobus)
        self.assertIn("200",response.status)
        data=json.loads(response.data)["data"]
        self.assertEqual(1,len(data))
        self.assertIn("Number",data[0])  
        self.assertEqual(100,data[0]["Number"])
    def test_6_create_confirm_delete(self):
        response = self.client.post("/user/signin",json={"username":"majun","password":"123456"})
        resp_dict = json.loads(response.data)
        self.assertIn("200",response.status)
        self.assertIn("access_token",resp_dict)
        header={'Authorization':"Bearer "+resp_dict["access_token"]}
        bus=dict(
            Departtime="2021/01/01 00:00",
            Number="100",
            Depart="Boston",
            Arrive="New York",
            contactinfo={
                "name":"1",
                "phone":"1"
            }
        )
        response = self.client.post("/booking/createbooking",headers=header,json=bus)
        # print(response.data)
        self.assertIn("201",response.status)
        # get booking
        response = self.client.get("/booking/getlist",headers=header)
        data=json.loads(response.data)
        self.assertIn("confirmed",data)
        self.assertEqual(1,len(data["confirmed"]))
        self.assertIn("_id",data["confirmed"][0])
        bookingID=data["confirmed"][0]["_id"]
        # confirm by admin
        ## admin sign in
        response = self.client.post("/user/signin",json={"username":"admin","password":"admin"})
        resp_dict = json.loads(response.data)
        self.assertIn("200",response.status)
        self.assertIn("access_token",resp_dict)
        header_admin={'Authorization':"Bearer "+resp_dict["access_token"]}
        # confirm
        response=self.client.put("/booking/confirm",json={"bookingID":bookingID},headers=header_admin)
        self.assertIn("204",response.status)
        # confirm by user
        response = self.client.get("/booking/getlist",headers=header)
        data=json.loads(response.data)
        self.assertIn("confirmed",data)
        self.assertEqual(1,len(data["confirmed"]))
        self.assertIn("_id",data["confirmed"][0])
if __name__=='main':    
    unittest.main()