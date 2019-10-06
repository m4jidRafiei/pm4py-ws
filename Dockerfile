FROM nikolaik/python-nodejs

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install nano vim git python3-pydot python-pydot python-pydot-ng graphviz python3-tk zip unzip curl ftp fail2ban python3-openssl

RUN pip install --no-cache-dir -U pm4py==1.2.0 Flask flask-cors setuptools pm4pydistr==0.1.10
RUN pip install --no-cache-dir -U pm4pycvxopt
#RUN pip install --no-cache-dir -U pm4pybpmn
COPY . /
#RUN cd /files && python download_big_logs.py
RUN echo "enable_session = True" >> /pm4pywsconfiguration/configuration.py
RUN echo "static_folder = '/webapp2/dist'" >> /pm4pywsconfiguration/configuration.py
RUN echo "ssl_context_directory = '/ssl_cert_gen'" >> /pm4pywsconfiguration/configuration.py
#RUN echo "log_manager_default_variant = 'multinode_file_based'" >> /pm4pywsconfiguration/configuration.py
#RUN pip install --no-cache-dir -U pyOpenSSL
#RUN cd /ssl_cert_gen && python create.py

RUN mkdir -p /webapp2
RUN rm -rRf /webapp2
RUN cd / && git clone https://github.com/pm-tk/source.git
RUN cd / && mv /source /webapp2
#RUN cd /webapp2 && npm install && npm install --save-dev --unsafe-perm node-sass && npm install -g @angular/core @angular/cli @angular/material
#RUN cd /webapp2 && ng build --prod

RUN cd /webapp2 && wget http://www.alessandroberti.it/dist.tar && tar xvf dist.tar

RUN cd / && python setup.py install

ENTRYPOINT ["python", "main.py"]

EXPOSE 5000
