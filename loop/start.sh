#!/bin/bash

MYSQL=`which mysql`
Q1="CREATE DATABASE IF NOT EXISTS loop_project;"
SQL="${Q1}"

media_path="/code/loop/media"

if [ ! -d $media_path ]; then
   mkdir $media_path
fi

supervisord -c /etc/supervisor/supervisord.conf
python /code/loop/manage.py makemigrations &&  python /code/loop/manage.py migrate
