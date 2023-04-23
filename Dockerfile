FROM ubuntu:22.04

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
  apt update && \
  apt install -y vim git tmux cmake wget curl g++ software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
  apt install -y python3.11 python3.11-venv

RUN useradd --create-home --shell /bin/bash ubuntu

WORKDIR /home/ubuntu
COPY .bash_profile .
RUN echo 'source ~/.bash_profile' >> .bashrc

# build latest zstd from source for best performance
WORKDIR /tmp
RUN git clone https://github.com/facebook/zstd /tmp/zstd
WORKDIR /tmp/zstd
RUN make
RUN cp programs/zstd /usr/local/bin/

# stockfish binpack minimizer
WORKDIR /tmp
RUN git clone https://github.com/Sopel97/Stockfish /tmp/stockfish
WORKDIR /tmp/stockfish/src
RUN git fetch origin && git checkout -t origin/binpack_minimizer
RUN make -j profile-build ARCH=x86-64-bmi2
RUN cp stockfish /usr/local/bin/stockfish-bin-min
RUN mv /tmp/stockfish /tmp/stockfish-bin-min-src

# stockfish for multipv2 scores and csv data
WORKDIR /tmp
RUN git clone https://github.com/linrock/Stockfish /tmp/stockfish
WORKDIR /tmp/stockfish/src
RUN git fetch origin && git checkout -t origin/nnue-data-v7
RUN make -j profile-build ARCH=x86-64-bmi2
RUN cp stockfish /usr/local/bin/stockfish-output-positions-csv
RUN mv /tmp/stockfish /tmp/stockfish-positions-csv-src

RUN chown -R ubuntu:ubuntu /home/ubuntu
USER ubuntu
WORKDIR /home/ubuntu/
COPY *.py *.sh *.txt .
RUN cp minimize_binpack.sh /usr/local/bin/

# prepare python 3.11 env
RUN python3.11 -m venv venv
RUN venv/bin/pip3 install -r requirements.txt
RUN echo 'export PATH=/home/ubuntu/venv/bin:$PATH' >> ~/.bashrc

WORKDIR /home/ubuntu/
CMD sleep infinity
