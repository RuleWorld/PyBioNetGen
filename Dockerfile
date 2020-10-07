FROM continuumio/anaconda3
MAINTAINER Ali Sinan Saglam <als251@pitt.edu>
ENV PS1="\[\e[0;33m\]|> bionetgen <| \[\e[1;35m\]\W\[\e[0m\] \[\e[0m\]# "

WORKDIR /src
COPY . /src
RUN pip install --no-cache-dir -r requirements.txt 
RUN python setup.py install
WORKDIR /
ENTRYPOINT ["bionetgen"]
