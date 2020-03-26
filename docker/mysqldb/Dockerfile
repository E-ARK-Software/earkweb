FROM mysql:5.7.15

LABEL maintainer="AIT, http://www.ait.ac.at"

ENV MYSQL_DATABASE=repodb \
    MYSQL_ROOT_PASSWORD=repo \
        MYSQL_USER=repo \
        MYSQL_PASSWORD=repo

ADD db.sql /docker-entrypoint-initdb.d

EXPOSE 3306