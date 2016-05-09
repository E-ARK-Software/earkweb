import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

from django.contrib.auth.models import User


def main():
    if len(sys.argv) != 4:
        print "Arguments missing:"
        print "python util/createuser.py <username> <email> <password>"
    user = User.objects.create_user(username=sys.argv[1], email=sys.argv[2], password=sys.argv[3])

if __name__ == "__main__":
    main()
