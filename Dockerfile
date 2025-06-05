FROM ubuntu:22.04

RUN apt update && apt install -y python3 python3-pip tmate wget

# Install playit agent
RUN wget https://github.com/playit-cloud/playit-agent/releases/latest/download/playit-linux-amd64 && \
    chmod +x playit-linux-amd64

# Set working directory
WORKDIR /app

# Copy bot files
COPY . /app

# Install Python dependencies
RUN pip3 install -r requirements.txt

CMD ["python3", "bot.py"]
