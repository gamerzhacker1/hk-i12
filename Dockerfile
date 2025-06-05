FROM ubuntu:22.04

RUN apt update && apt install -y python3 python3-pip tmate curl
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
CMD ["python3", "bot.py"]
