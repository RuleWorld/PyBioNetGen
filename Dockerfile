FROM continuumio/anaconda3
LABEL Ali Sinan Saglam <als251@pitt.edu>
ENV PS1="\[\e[0;33m\]|> bionetgen <| \[\e[1;35m\]\W\[\e[0m\] \[\e[0m\]# "

LABEL org.opencontainers.image.source=https://github.com/RuleWorld/PyBioNetGen
LABEL org.opencontainers.image.description="PyBNG container"
LABEL org.opencontainers.image.licenses=MIT
RUN apt-get update && apt-get install -y \
  libncurses5-dev \
  libncursesw5-dev \
  libncurses5
WORKDIR /src
COPY . /src
RUN pip install --no-cache-dir -r requirements.txt 
RUN pip install -e .
WORKDIR /
ENTRYPOINT ["bionetgen"]
