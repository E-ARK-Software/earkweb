import random, string

import simpleflake.simpleflake

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def getUniqueID():
   prefix = "URN:EARK:"
   sf = simpleflake.simpleflake()
   return "%s%d" % (prefix, sf)