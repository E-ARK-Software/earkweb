FROM ubuntu:18.04
LABEL maintainer="AIT, http://www.ait.ac.at"

RUN apt-get update --fix-missing

# Set locale
RUN apt-get install -y locales && locale-gen de_AT.UTF-8
ENV LANG='de_AT.UTF-8' \
    LANGUAGE='de_AT.UTF-8' \
    LC_ALL='de_AT.UTF-8'

# copy python requirements
COPY ./requirements.txt /tmp

# python3
RUN apt-get install python3 python3-dev python3-virtualenv build-essential libmysqlclient-dev -y
RUN apt-get upgrade python3 -y
RUN apt install python3-pip -y
RUN apt-get install git -y

RUN apt-get install wget -y

# Ghostscript
RUN wget -P /tmp https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs951/ghostscript-9.51-linux-x86_64.tgz && \
    cd /tmp && tar -xzf ghostscript-9.51-linux-x86_64.tgz && \
    cp /tmp/ghostscript-9.51-linux-x86_64/gs-951-linux-x86_64 /usr/local/bin/ghostscript && \
    chmod +x /usr/local/bin/ghostscript

# Fido
#RUN wget -P /tmp https://github.com/openpreserve/fido/archive/1.3.2-81.tar.gz && \
#    cd /tmp && tar -xzf 1.3.2-81.tar.gz && \
#    cd fido-1.3.2-81 && \
#    python3 setup.py install

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

RUN mkdir -p /data/storage/pairtree_version0_1
COPY ./docker/sample/repo /data/repo

ADD . /earkweb

# make sure the docker settings are used in the container
COPY ./settings/settings.cfg.docker /earkweb/settings/settings.cfg

# entry point
RUN chmod +x /earkweb/run_all.sh
ENTRYPOINT ["/earkweb/run_all.sh"]

EXPOSE 8000 5555
