FROM nikolaik/python-nodejs

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install nano vim
RUN apt-get -y install git
RUN apt-get -y install python3-pydot python-pydot python-pydot-ng graphviz
RUN apt-get -y install python3-tk
RUN apt-get -y install zip unzip

RUN pip install --no-cache-dir -U pm4py Flask flask-cors requests python-keycloak
RUN pip install --no-cache-dir -U pyinstaller PyQT5 setuptools
COPY . /
#RUN git submodule init
#RUN git submodule update
#RUN cd /webapp2 && git checkout master && git pull
RUN mkdir -p /webapp2
RUN rm -rRf /webapp2
RUN git clone https://github.com/pm-tk/source.git
RUN mv /source /webapp2
RUN cd /webapp2 && npm install
RUN cd /webapp2 && npm install --save-dev --unsafe-perm node-sass
RUN cd /webapp2 && npm install -g @angular/cli
RUN cd /webapp2 && npm install -g @angular/material
RUN cd /webapp2 && ng build --prod
RUN python setup.py install

ENTRYPOINT ["python", "main.py"]

EXPOSE 5000