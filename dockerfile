FROM python:3.8-slim-buster

ADD requirement.txt .
RUN python -m pip install -r requirement.txt
# RUN export FLASK_APP="flaskr/backservice.py"