# docker
`docker build -f ./dockerfile -t xxx .`
`docker run -d -p 5000:5000 -e mongoDBip="remote mongo" majun1997/uber:test`
# structure:
1. User{
    _id,
    userName,
    password,
    userType
}
2. Bus{
    BusType,
    _id,
    Departtime,
    Number,
    Depart,
    Arrive,
    EstimateTime
}
3. Booking{
    _id,
    user_id
    Number
    contactinfo{
        name,
        phone
    }
    busID,
    status
}
# How to set token in postman:
* Header->Key->add "Authorization"->value->add "Bearer token_str"
# API
## POST API:
* http://apiurl/user/signin
* * input: json{username,password}
* * output: json{access_token,refresh_token}
* http://apiurl/user/signup
* * input: json{username,password}
* * output: json{access_token,refresh_token}
* http://apiurl/user/refresh
* * token required
* * output: access_token
* http://apiurl/user/bus/insertone
* * token required(admin access)
* * input json{Departtime,Number,Depart,Arrive,BusType}
* * output json{Bus}
* http://apiurl/user/bus/searchbus
* * input json{StartTime,EndTime,Depart,Arrive,Number}
* * output json{BusList}
* * description: find the bus that between StartTime and EndTime (or StartTime + 1 day) and seats(Number) greater or equal to the Number
* http://apiurl//booking/bookingexist
* * token required
* * input json{busID,Number,contactinfo}
* * output None
* http://apiurl/booking/createbooking
* * token required
* * input json {Number,contactinfo,Departtime,Depart,Arrive}
## GET API:
* http://apiurl/user/getuser
* * input (header) access_token (postman->header->authorization->Bearer token)
* * output json{user}
* http://apiurl/booking/getlist
* * token required
* * output json{bookingList}
## PUT API
* http://apiurl/booking/confirm
* * input json{bookingID}
* * description: make unconfirmed booking to confirmed booking
## DELETE API
* http://apiurl/booking/deletebooking
* * token required
* * input json{bookingID}
# Test
* How to run test
    `python -m unittest test`