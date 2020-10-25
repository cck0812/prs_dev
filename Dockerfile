FROM python:3.7
LABEL maintainer Zak
ENV PYTHONUNBUFFERED 1
ADD requirements.txt /app/prs_dev/requirements.txt
WORKDIR /app/prs_dev
RUN pip install -r requirements.txt

