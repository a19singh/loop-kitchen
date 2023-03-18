#!/bin/bash

MYSQL=`which mysql`
Q1="CREATE DATABASE IF NOT EXISTS loop_project;"
SQL="${Q1}"

supervisord -c /etc/supervisor/supervisord.conf
python /code/loop/manage.py makemigrations &&  python /code/loop/manage.py migrate
