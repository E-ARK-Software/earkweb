FROM ubuntu:18.04
LABEL maintainer="AIT, http://www.ait.ac.at"

ARG USER

RUN apt-get update --fix-missing

# Set locale
RUN apt-get install -y locales && locale-gen de_AT.UTF-8

# copy python requirements
COPY ./requirements.txt /tmp

# python3
RUN apt-get update --fix-missing
RUN apt-get install -y python3 python3-dev 
RUN apt-get install -y python3-virtualenv 
RUN apt-get install -y build-essential libmysqlclient-dev -y
RUN apt-get upgrade python3 -y
RUN apt install python3-pip -y
RUN apt-get install git telnet nano -y
RUN apt-get install libicu-dev -y

RUN apt-get install wget -y
RUN apt-get install unzip -y
# Ghostscript
RUN wget --no-verbose -P /tmp https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs951/ghostscript-9.51-linux-x86_64.tgz && \
    cd /tmp && tar -xzf ghostscript-9.51-linux-x86_64.tgz && \
    cp /tmp/ghostscript-9.51-linux-x86_64/gs-951-linux-x86_64 /usr/local/bin/ghostscript && \
    chmod +x /usr/local/bin/ghostscript

RUN apt-get install imagemagick -y 
# Fido
#RUN wget -P /tmp https://github.com/openpreserve/fido/archive/1.3.2-81.tar.gz && \
#    cd /tmp && tar -xzf 1.3.2-81.tar.gz && \
#    cd fido-1.3.2-81 && \
#    python3 setup.py install

#RUN wget --no-verbose -P /tmp https://github.com/E-ARK-Software/eatb/archive/master.zip && \
#    cd /tmp && unzip ./master.zip && \
#    cd eatb-master && \
#    python3 setup.py install && \
#    rm /tmp/master.zip && rm -rf /tmp/eatb-master

RUN wget -P /tmp https://github.com/E-ARK-Software/eatb/archive/v0.1.5.tar.gz && \
    cd /tmp && tar -xzf v0.1.5.tar.gz && \
    cd eatb-0.1.5 && \
    python3 setup.py install && \
    rm /tmp/v0.1.5.tar.gz && rm -rf /tmp/eatb-0.1.5

RUN apt-get remove wget -y

# install python requirements
#RUN /usr/bin/pip3 install -r /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt

# packages
RUN apt-get install vim curl redis-server -y

#RUN mkdir -p /var/data/storage/pairtree_version0_1
#COPY ./docker/sample/repo /var/data/repo

ADD . /earkweb

# make sure the docker settings are used in the container
COPY ./settings/settings.cfg.docker /earkweb/settings/settings.cfg

# i18n
RUN apt-get install gettext -y
RUN cd /earkweb && django-admin makemessages -l en
RUN cd /earkweb && django-admin makemessages -l de
RUN cd /earkweb && django-admin compilemessages

# add non-priviledged user
RUN adduser --disabled-password --gecos "" ${USER}

COPY scripts/wait-for-it.sh wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# entry point
RUN chmod +x /earkweb/docker/run_earkweb.sh
RUN chmod +x /earkweb/docker/run_celery.sh
RUN chmod +x /earkweb/docker/run_flower.sh
#ENTRYPOINT ["/earkweb/run_all.sh"]

USER ${USER}:${USER}

# EXPOSE 8000 5555
