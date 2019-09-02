# Agave clients service for generating OAuth2 client applications for the WSO2 API Manager platform.
# Image: jstubbs/agave_clients

FROM jstubbs/template_compiler
MAINTAINER Joe Stubbs

# Manually set up the apache environment variables
ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
ENV APACHE_LOCK_DIR /var/lock/apache2
ENV APACHE_PID_FILE /var/run/apache2.pid

RUN apt-get update && \
		apt-get install -y python \
											 python-dev \
											 python-pip \
											 git \
											 apache2 \
											 apache2-mpm-prefork \
											 apache2-utils \
											 libexpat1 \
											 ssl-cert \
											 libapache2-mod-wsgi \
											 lynx \
											 libldap2-dev \
											 libsasl2-dev \
											 python-mysqldb && \
		mkdir /code
ADD requirements.txt /code/
RUN pip install -r /code/requirements.txt

ADD agave_clients /code/agave_clients/agave_clients
ADD manage.py /code/agave_clients/

RUN touch /code/agave_clients/agave_clients/running_in_docker && \
		chmod o+rw -R /code/agave_clients/

ADD deployment/wsgi.load /etc/apache2/mods-available/
ADD deployment/apache2.conf /etc/apache2/sites-enabled/000-default.conf

EXPOSE 80

CMD /usr/sbin/apache2ctl -D FOREGROUND
