#!/bin/bash

export PYTHONUNBUFFERED=1
cd /apps/svr/DevOps/
/apps/svr/python3/bin/python3  manage.py runserver 0.0.0.0:8000 > ./server.log 2>&1 &
echo "end"