FROM python:3.12

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install python dependencies
RUN apt-get update
RUN apt-get install -y cron
RUN pip install --upgrade pip
# add cron job
RUN echo "* * * * * /usr/local/bin/python /app/manage.py update_task_status" > /etc/cron.d/update_task_status
RUN chmod 0644 /etc/cron.d/update_task_status
RUN crontab /etc/cron.d/update_task_status
RUN touch /var/log/cron.log
# set work directory
WORKDIR /app
COPY . .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD cron && tail -f /var/log/cron.log

