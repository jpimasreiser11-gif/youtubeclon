import redis
import json
r = redis.Redis(host='localhost', port=6379, db=0)

active = r.lrange('bull:video-processing:active', 0, -1)
wait = r.lrange('bull:video-processing:wait', 0, -1)
print(f"Active Queue items: {active}")
print(f"Wait Queue items: {wait}")

# Get all keys to see what BullMQ has
keys = r.keys('bull:video-processing:*')
print(f"All BullMQ keys: {keys}")
for k in keys:
    if r.type(k) == b'hash':
        print(f"Hash {k}: {r.hgetall(k)}")
