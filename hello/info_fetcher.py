import json
import redis
from hello import config

# handles communicating back and forth with redis
# handles interpreting JSON files

def getIPaddress(request):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_address:
        ip_address = ip_address.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    return ip_address

def toJSON(frequency, duration, slide_duration):
    x = {
        "frequency": frequency,
        "duration": duration,
        "slide-duration": slide_duration
        }
    return json.dumps(x)

def fromJSON(json_string):
    return json.loads(json_string)

def connectToRedis():
    r = redis.Redis(
        host=config.HOST, port=config.PORT,
        username=config.USERNAME, # use your Redis user. More info https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/
        password=config.PASSWORD # use your Redis password
        #ssl=True,
        #ssl_certfile="./redis_user.crt",
        #ssl_keyfile="./redis_user_private.key",
        #ssl_ca_certs="./redis_ca.pem",
        )
    return r

# get current user data
def getUserInfo(key):
    r = connectToRedis()
    if r.exists(key):
        return fromJSON(r.get(key))
    else:
        return({
            "frequency": [],
            "duration": [],
            "slide-duration": []
            })

# push new user data to redis, reset key expration time
def setUserInfo(key, frequency, duration, slide_duration, key_lifetime):
    r = connectToRedis()
    r.set(key,toJSON(frequency, duration, slide_duration))
    r.expire(key, key_lifetime)
    return

# delete user data associated with an ip address
def clearUserInfo(key):
    r = connectToRedis()
    r.delete(key)