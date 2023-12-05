FROM ubuntu:23.10

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
  apt update && \
  apt install -y vim git sudo tmux cmake wget curl g++ \
                 software-properties-common zstd python3-pip

# RUN useradd --create-home --shell /bin/bash ubuntu
RUN usermod -aG sudo ubuntu
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

WORKDIR /home/ubuntu
COPY .bash_profile .
RUN echo 'source ~/.bash_profile' >> .bashrc

# build latest zstd from source for best performance
# WORKDIR /tmp
# RUN git clone https://github.com/facebook/zstd /tmp/zstd
# WORKDIR /tmp/zstd
# RUN make
# RUN cp programs/zstd /usr/local/bin/

# stockfish for multipv2 scores and csv data
WORKDIR /tmp
RUN git clone https://github.com/linrock/Stockfish /tmp/stockfish
WORKDIR /tmp/stockfish/src
RUN git fetch origin && git checkout -t origin/nnue-data-v7-3072
RUN make -j profile-build ARCH=x86-64-bmi2
RUN cp stockfish /usr/local/bin/stockfish-output-positions-csv
RUN cp stockfish /usr/local/bin/stockfish

WORKDIR /tmp/stockfish/script
RUN cp interleave_binpacks.py /root/
RUN cp shuffle_binpack.py /root/
RUN mv /tmp/stockfish /tmp/stockfish-positions-csv-src

RUN chown -R ubuntu:ubuntu /home/ubuntu
USER ubuntu
WORKDIR /home/ubuntu/
COPY *.py *.sh *.txt .
RUN sudo cp minimize_binpack.sh /usr/local/bin/
RUN sudo cp interleave_binpacks.py /usr/local/bin/
RUN sudo cp shuffle_binpack.py /usr/local/bin/
RUN sudo chown ubuntu:ubuntu *

# prepare python 3.11 env
# RUN python3.11 -m venv venv
# RUN venv/bin/pip3 install -r requirements.txt
# RUN echo 'export PATH=/home/ubuntu/venv/bin:$PATH' >> ~/.bashrc
RUN pip3 install -r requirements.txt --break-system-packages

# WORKDIR /home/ubuntu/
CMD sleep infinity
