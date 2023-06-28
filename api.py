import tornado.ioloop
import tornado.web
import redis
import pymongo
import json
import uuid
import time
import certifi
from bson import ObjectId

# Redis cache configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDEIS_DB = 0

# MongoDB configuration
MONGO_HOST = 'mongodb+srv://qiwenjie026:qwjdx123@api.sd8t01s.mongodb.net/'
MONGO_PORT = 27017
MONGO_DB = 'API'
MONGO_COLLECTION = 'Info'

# Connect to Redis
redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT)

# Connect to MongoDB
mongo_client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT, tlsCAFile=certifi.where())
mongo_db = mongo_client[MONGO_DB]
mongo_coll = mongo_db[MONGO_COLLECTION]

# Cache expiration time (in seconds)
CACHE_EXPIRATION = 60 * 60 * 24 * 30  # 30 days

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Generate a random GUID
def generate_guid():
    return str(uuid.uuid4())

# Create a new GUID with the provided metadata.
def create_guid(guid=None, expire=None, user=None):
    if not guid:
        guid = generate_guid()

    if not expire:
        expire = int(time.time()) + CACHE_EXPIRATION

    document = {
        'guid': guid,
        'expire': int(expire),
        'user': user
    }
    mongo_coll.insert_one(document)

    redis_conn = redis.Redis(connection_pool=redis_pool)
    redis_conn.set(guid, json.dumps(document, cls=CustomJSONEncoder), ex=expire)

    return document

# Clean up expired GUIDs from the database and cache.
def clean_expired_guids():
    current_time = int(time.time())
    mongo_coll.delete_many({'expire': {'$lt': current_time}})
    redis_conn = redis.Redis(connection_pool=redis_pool)
    all_guids = mongo_coll.find({}, {'guid': 1})
    expired_guids = [guid['guid'] for guid in all_guids if int(guid['expire']) < current_time]
    if expired_guids:
        redis_conn.delete(*expired_guids)


def read_guid(guid):
    redis_conn = redis.Redis(connection_pool=redis_pool)
    cached_data = redis_conn.get(guid)

    if cached_data:
        return json.loads(cached_data)

    document = mongo_coll.find_one({'guid': guid})

    if document:
        redis_conn.set(guid, json.dumps(document, cls=CustomJSONEncoder), ex=document['expire'])
        return document

    return None

def update_guid(guid, expire, user):
    redis_conn = redis.Redis(connection_pool=redis_pool)
    cached_data = redis_conn.get(guid)

    if cached_data:
        document = json.loads(cached_data)

        # Update only the fields provided by the user
        if expire is not None:
            document['expire'] = int(expire)
        if user is not None:
            document['user'] = user

        # Exclude the _id field from the update operation
        document.pop('_id', None)

        mongo_coll.replace_one({'guid': guid}, document)
        redis_conn.set(guid, json.dumps(document, cls=CustomJSONEncoder), ex=document['expire'])

        return document

    return None

def delete_guid(guid):
    redis_conn = redis.Redis(connection_pool=redis_pool)
    cached_data = redis_conn.get(guid)

    if cached_data:
        document = json.loads(cached_data)
        redis_conn.delete(guid)
        mongo_coll.delete_one({'guid': guid})
        return document

    return None

class GUIDHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def get(self, guid):
        document = read_guid(guid)
        if document:
            self.write(json.dumps(document, cls=CustomJSONEncoder))
        else:
            self.set_status(404)
            self.write(json.dumps({'error': 'GUID not found'}))

    def post(self, guid):
        try:
            request_data = json.loads(self.request.body)
            user = request_data.get('user')
            expire = request_data.get('expire')

            if expire is not None:
                expire = int(expire)
            else:
                expire = int(time.time()) + CACHE_EXPIRATION

            if not guid:
                guid = generate_guid()

            document = create_guid(guid, expire, user)
            self.write(json.dumps(document, cls=CustomJSONEncoder))
        except ValueError:
            self.set_status(400)
            self.write(json.dumps({'error': 'Invalid JSON payload'}))

    def put(self, guid):
        try:
            request_data = json.loads(self.request.body)
            user = request_data.get('user')
            expire = request_data.get('expire')

            document = read_guid(guid)
            if document:
                # Update only the fields provided by the user
                if expire is not None:
                    document['expire'] = int(expire)
                if user is not None:
                    document['user'] = user

                # Update the document in the database and cache
                update_guid(guid, document['expire'], document['user'])

                self.write(json.dumps(document, cls=CustomJSONEncoder))
            else:
                self.set_status(404)
                self.write(json.dumps({'error': 'GUID not found'}))
        except ValueError:
            self.set_status(400)
            self.write(json.dumps({'error': 'Invalid JSON payload'}))


    def delete(self, guid):
        document = delete_guid(guid)
        if document:
            self.write("successfully deleted")
        else:
            self.set_status(404)
            self.write('GUID not found')

def make_app():
    return tornado.web.Application([
        (r"/guid/?(.*)", GUIDHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server started on 8888")
    tornado.ioloop.PeriodicCallback(clean_expired_guids, 60 * 60 * 1000).start()
    tornado.ioloop.IOLoop.current().start()
