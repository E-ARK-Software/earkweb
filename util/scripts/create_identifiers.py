#!/usr/bin/env python
import json
import os

import requests
import time
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()

from earkweb.models import InternalIdentifier
from config.configuration import node_namespace_id, verify_certificate

def main():
    if len(sys.argv) < 2:
        print("Parameters missing (1: access_token, 2: cycles, 3: batch_size, 4: pause)")
        return 1
    if len(sys.argv) != 5:
        print("Wrong parameter count (1: access_token, 2: cycles, 3: batch_size, 4: pause)")
        return 1
    access_token = sys.argv[1]
    if len(access_token) != 39:
        print("Wrong access token")
        return 1
    cycles = int(sys.argv[2])
    if cycles > 500:
        print("Cycles out of range (max 500)")
        return 1
    batch_size = int(sys.argv[3])
    if batch_size > 100:
        print("Batch size out of range (max 100)")
        return 1
    pause = int(sys.argv[4])
    if pause > 600:
        print("Pause out of range (max 600s/10min)")
        return 1
    request_url = "https://smart-contract-ui-centralnode-dev.aotp003.appagile.io/api/get_asset_addresses?amount=%d" % batch_size
    print("Blockchain get addresses request URL: %s" % request_url)
    for x in range(0, cycles):
        print("creating batch of identifiers: %d" % (x + 1))
        response = requests.get(request_url, headers={"Authorization": "Bearer %s" % access_token}, verify=verify_certificate)
        if response.status_code == 200:
            addresses = json.loads(response.text)
            for address in addresses['addresses']:
                print("creating address: %s" % address)
                int_id = InternalIdentifier.objects.create(identifier=address, org_nsid=node_namespace_id)
                int_id.save()
        time.sleep(pause)  # pause 3 minutes

if __name__ == "__main__":
    main()


