import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

from django.contrib.auth.models import User


def main():
    if len(sys.argv) != 5:
        print "Number of arguments incorrect"
        print "python util/createuser.py <username> <email> <password> <isstaff>"
    user = User.objects.create_user(username=sys.argv[1], email=sys.argv[2], password=sys.argv[3], is_staff=(sys.argv[4] == "true"))

if __name__ == "__main__":
    main()
