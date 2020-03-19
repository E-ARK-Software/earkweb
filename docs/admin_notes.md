# Admin notes

## API authentication

### Create API token for users

Open a Django shell using command `python manage.py shell` and execute the following commands (adapt primary key of the user: `pk`):

    from django.contrib.auth.models import User
    u = User.objects.get(pk=1)
    from rest_framework.authtoken.models import Token
    token = Token.objects.create(user=u)
    print token.key
    8d14d3383b181bf592f825df813874630f8de607

Documentation: http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication

### Create API Keys

User independent API keys can be managed via the "djangorestframework-api-key" administration:

    http://localhost:8000/earkweb/adminrest_framework_api_key/apikey/

## Generate a pool of identifiers 

The system can use a pool of pre-generated identifiers which can be added or generated using the REST API function /earkweb/api/identifiers

It is also possible to generate identifiers in python as follows:

    from earkweb.models import InternalIdentifier
    import os
    for i in range(0, 100):
        InternalIdentifier.objects.create(identifier=os.urandom(20).encode('hex'), org_nsid=org_nsid)

If the identifier assignment step during ingest fails this can be because of no identifiers being available for a given 
organisation namespace.

## Index repository

Script for indexing the repository:

    python util/index-aip-storage.py
