from ubuntu:14.04.5

maintainer E-ARK project, http://www.eark-project.com

RUN echo "deb http://archive.ubuntu.com/ubuntu/ trusty multiverse" >> /etc/apt/sources.list
RUN apt-get update

# install python
RUN apt-get install python  --force-yes -y
RUN apt-get install python-setuptools --force-yes -y
RUN apt-get install build-essential --force-yes -y
RUN apt-get install python-virtualenv --force-yes -y
RUN apt-get install python-dev --force-yes -y

RUN easy_install pip

RUN apt-get install -y summain jhove pdftohtml

RUN apt-get install -y graphicsmagick imagemagick
RUN apt-get install -y libgraphicsmagick++1-dev libboost-python-dev

RUN apt-get install -y tar git curl vim wget dialog net-tools build-essential

RUN wget https://github.com/openpreserve/fido/archive/1.3.2-81.tar.gz
RUN tar -xzvf 1.3.2-81.tar.gz
RUN cd fido-1.3.2-81 && python setup.py install

#RUN cd fido-1.3.2-81/fido && echo 'yes' | python update_signatures.py

RUN wget http://downloads.ghostscript.com/public/old-gs-releases/ghostscript-9.18.tar.gz
RUN tar -xzf ghostscript-9.18.tar.gz
RUN cd ghostscript-9.18 && ./configure && make && make install

RUN apt-get install -y libgeos-dev libmysqlclient-dev libxml2-dev libxslt1-dev

ADD docker/wait-for-it/wait-for-it.sh /wait-for-it.sh

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN pip install redis

RUN mkdir -p /var/data/earkweb

RUN mkdir -p /var/log/earkweb

