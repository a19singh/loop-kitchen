FROM ubuntu:20.04
ARG PYTHON_VERSION=3.8
ENV LANGUAGE=en_US.UTF-8
ENV LANG=en_US.UTF-8

RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential git locales locales-all \
	mysql-client libmysqlclient-dev vim wget \
	g++ cmake ca-certificates


RUN apt-get update && apt-get install -y python3.8 python3.8-distutils python3.8-dev libldap2-dev libsasl2-dev tox lcov valgrind libpq-dev
RUN wget https://bootstrap.pypa.io/get-pip.py && python3.8 get-pip.py && rm get-pip.py
RUN python3.8 -m pip install --upgrade pip setuptools wheel
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.8 10

ADD ./requirements.txt /root/requirements.txt
ADD ./supervisord.conf /etc/supervisor/supervisord.conf
ADD ./loop /code/loop

RUN python -m pip install -r /root/requirements.txt

RUN mkdir -p /var/log/supervisor

WORKDIR /code/loop
