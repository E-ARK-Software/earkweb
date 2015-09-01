import random, string, uuid

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def getUniqueID():
   return uuid.uuid4().__str__()