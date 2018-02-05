FROM mdillon/postgis:9.6
#FROM mdillon/postgis:9.6-2.3

# make the "en_US.UTF-8" locale so postgres will be utf-8 enabled by default
RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
	&& localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# install wget
RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

## install cron
RUN apt-get update && apt-get -y install cron
# Add crontab file in the cron directory
ADD crontab /etc/cron.d/updater
# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/updater
# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# install python3
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    ca-certificates \
    gcc \
    git \
    libpq-dev \
    make \
    mercurial \
    pkg-config \
    python3 \
    python3-dev \
    python3-pip \
    ssh \
    && apt-get autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# copy helper scripts
COPY keepright/* /docker-entrypoint-initdb.d/keepright/
COPY whitelist_errors.txt /docker-entrypoint-initdb.d/

COPY osm_errors/* /docker-entrypoint-initdb.d/osm_errors/

COPY all_errors/* /docker-entrypoint-initdb.d/all_errors/

COPY kort/* /docker-entrypoint-initdb.d/kort/

COPY update/* /docker-entrypoint-initdb.d/update/

COPY mission_creator/* /docker-entrypoint-initdb.d/mission_creator/

COPY kort2osm/helper/* /docker-entrypoint-initdb.d/kort2osm/helper/
COPY kort2osm/* /docker-entrypoint-initdb.d/kort2osm/

# create overpass log file for user postgres
RUN touch /docker-entrypoint-initdb.d/mission_creator/overpass.log
RUN chown -R postgres:postgres /docker-entrypoint-initdb.d/mission_creator/overpass.log

RUN touch /docker-entrypoint-initdb.d/kort2osm/kort2osm.log
RUN touch /docker-entrypoint-initdb.d/kort2osm/kort2osm_error.log
RUN chown -R postgres:postgres /docker-entrypoint-initdb.d/kort2osm/kort2osm.log
RUN chown -R postgres:postgres /docker-entrypoint-initdb.d/kort2osm/kort2osm_error.log

# install python dependencies for mission creator
RUN pip3 install -r /docker-entrypoint-initdb.d/mission_creator/requirements.txt
RUN pip3 install -r /docker-entrypoint-initdb.d/kort2osm/requirements.txt


#### copy and run initialization scripts
COPY 00_init_db.sql /docker-entrypoint-initdb.d/
COPY 02_setup_postgis.sh /docker-entrypoint-initdb.d/
COPY 01_setup_keepright_db.sh /docker-entrypoint-initdb.d/
COPY 03_setup_osm_errors_db.sh /docker-entrypoint-initdb.d/
COPY 04_setup_all_errors_db.sh /docker-entrypoint-initdb.d/
COPY 05_setup_kort_db.sh /docker-entrypoint-initdb.d/
