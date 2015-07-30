import random, string, uuid

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def getUniqueID():
   prefix = ""
   sf = uuid.uuid1()
   return "%s%d" % (prefix, sf)