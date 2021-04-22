# FROM python:3.9-slim-buster as base-img
FROM 997541697059.dkr.ecr.us-west-2.amazonaws.com/python:3.9-slim-buster   as base-img
WORKDIR /app
ADD . .
RUN apt-get update
RUN pip3 install -r requirements.txt
# FROM localimg
ARG test_mongo
ENV mongoDBip=$test_mongo
RUN python -m unittest test
EXPOSE 5000
ARG mongoDBip
ENV mongoDBip=$mongoDBip
CMD gunicorn --threads=3 --bind 0.0.0.0:5000 wsgi:app
