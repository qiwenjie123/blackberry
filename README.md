The necessary dependencies installation:
Tornado: pip install tornado
Redis: pip install redis
pymongo: pip install pymongo

Run the api:
start redis: brew services start redis
start the Tornado web server on localhost and port 8888.: python api.py

Test:
1. pyhton test.py

2. test on postman: 

post:
http://localhost:8888/guid
Content-Type: application/json
body json format
{
  "expire": "1427736345",
  "user": "new user"
}

get: 
http://localhost:8888/guid/{guid} 

put: 
http://localhost:8888/guid/{guid} 
body json format
{
  "user": "user1"
}

delete: http://localhost:8888/guid/{guid} 