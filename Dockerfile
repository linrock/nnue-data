FROM ubuntu:23.04

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
  apt update && \
  apt install -y vim git tmux cmake wget curl g++ software-properties-common zstd python3-pip

# RUN useradd --create-home --shell /bin/bash ubuntu
# WORKDIR /home/ubuntu
WORKDIR /root
COPY .bash_profile .
RUN echo 'source ~/.bash_profile' >> .bashrc

# build latest zstd from source for best performance
# WORKDIR /tmp
# RUN git clone https://github.com/facebook/zstd /tmp/zstd
# WORKDIR /tmp/zstd
# RUN make
# RUN cp programs/zstd /usr/local/bin/

# stockfish binpack minimizer
WORKDIR /tmp
RUN git clone https://github.com/official-stockfish/Stockfish /tmp/stockfish
WORKDIR /tmp/stockfish/src
RUN git fetch origin && git checkout -t origin/tools
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
RUN cp stockfish /usr/local/bin/stockfish
WORKDIR /tmp/stockfish/script
# RUN cp interleave_binpacks.py /home/ubuntu/
# RUN cp shuffle_binpack.py /home/ubuntu/
RUN cp interleave_binpacks.py /root/
RUN cp shuffle_binpack.py /root/
RUN mv /tmp/stockfish /tmp/stockfish-positions-csv-src

# RUN chown -R ubuntu:ubuntu /home/ubuntu
# USER ubuntu
# WORKDIR /home/ubuntu/
WORKDIR /root/
COPY *.py *.sh *.txt .
USER root
RUN cp minimize_binpack.sh /usr/local/bin/
# RUN chown ubuntu:ubuntu *
# USER ubuntu

# prepare python 3.11 env
# RUN python3.11 -m venv venv
# RUN venv/bin/pip3 install -r requirements.txt
# RUN echo 'export PATH=/home/ubuntu/venv/bin:$PATH' >> ~/.bashrc
RUN pip3 install -r requirements.txt --break-system-packages

# WORKDIR /home/ubuntu/
CMD sleep infinity
