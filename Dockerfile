FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        mariadb-client \
        mariadb-server \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir \
        Flask==2.3.3 \
        Flask-JWT-Extended==4.6.0 \
        Flask-Migrate==4.0.7 \
        Flask-SQLAlchemy==3.1.1 \
        Pillow==10.4.0 \
        PyMySQL==1.1.1 \
        Werkzeug==2.3.7

COPY . /app

RUN chmod +x /app/myServer/docker_start_all.sh \
    && mkdir -p /run/mysqld /var/lib/mysql \
    && chown -R mysql:mysql /run/mysqld /var/lib/mysql

VOLUME ["/var/lib/mysql"]

EXPOSE 3306 5000 5001 5002 5005

CMD ["/bin/bash", "/app/myServer/docker_start_all.sh"]
