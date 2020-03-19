FROM mysql:5.7.15

LABEL maintainer="DILCIS, dilcis.org"

ENV MYSQL_DATABASE=earkdb \
    MYSQL_ROOT_PASSWORD=eark \
        MYSQL_USER=eark \
        MYSQL_PASSWORD=eark

ADD earkdb.sql /docker-entrypoint-initdb.d

EXPOSE 3306