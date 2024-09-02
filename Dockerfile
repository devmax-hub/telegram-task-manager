FROM python:3.12

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install python dependencies
RUN apt-get update
RUN pip install --upgrade pip
# set work directory
WORKDIR /app
COPY . .
COPY requirements.txt .
RUN pip install -r requirements.txt

