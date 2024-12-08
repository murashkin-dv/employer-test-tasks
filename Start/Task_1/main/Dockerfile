FROM python:3.8

# set project directory
ENV APP=/usr/src/app

WORKDIR $APP
ADD . $APP

# install dependencies
RUN pip install --upgrade pip
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt $APP/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# запуск скрипта в режиме Consume
ENTRYPOINT ["python3", "main.py", "--mode", "consume", "--kafka", "broker:9092"]
