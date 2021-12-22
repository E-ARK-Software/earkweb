import os, sys
import MySQLdb
from config.configuration import mysql_host, mysql_user, mysql_port, mysql_password, mysql_db


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()



def main():
    db = MySQLdb.connect(host=mysql_host,  # your host, usually localhost
                         port=mysql_port,
                         user=mysql_user,  # your username
                         passwd=mysql_password,  # your password
                         db=mysql_db)  # name of the data base
    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = db.cursor()

    # Use all the SQL you like
    cur.execute("SELECT count(*) FROM informationpackage")

    # print all the first cell of all the rows
    for row in cur.fetchall():
        print(row)

    db.close()


if __name__ == "__main__":
    main()
