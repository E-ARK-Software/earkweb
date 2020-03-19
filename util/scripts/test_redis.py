import redis
import json
r = redis.StrictRedis(decode_responses=True)

data = {"process_id": "f30c391e-10e6-42b0-9007-16941f8eea0c", "identifier": "eark:a78432b5ab3621c2e540f21d1d07a1fe282fad3c",
        "version": "00001", "storage_dir": "/var/data/earkweb/storage/pairtree_root/dm/a+/a7/84/32/b5/ab/36/21/c2/e5/40/f2/1d/1d/07/a1/fe/28/2f/ad/3c/data/00001/eark+a78432b5ab3621c2e540f21d1d07a1fe282fad3c"}

r.rpush('queue', json.dumps(data))

# val = r.blpop('queue')
# print(val)
