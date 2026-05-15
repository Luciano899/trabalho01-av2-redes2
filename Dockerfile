FROM ubuntu:22.04

RUN apt update && apt install -y python3 iproute2 iputils-ping net-tools tcpdump

WORKDIR /app

COPY . .

CMD ["bash"]