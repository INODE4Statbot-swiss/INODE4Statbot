FROM nvcr.io/nvidia/pytorch:23.07-py3

COPY download_nltk.py /tmp
COPY load_hf_models.py /tmp
RUN apt update
RUN apt-get -y install default-libmysqlclient-dev




# the following lines are necessary to remote debug into the docker via SSH.
# make sure you also start the ssh service at the entrypoint!
EXPOSE 22

RUN apt-get install -y openssh-server
RUN mkdir /var/run/sshd

ADD authorized_keys /tmp/
ADD known_hosts /tmp/
RUN mkdir -p /root/.ssh \
    && mv /tmp/authorized_keys /root/.ssh/authorized_keys \
    && mv /tmp/known_hosts /root/.ssh/known_hosts \
    && chown root:root /root/.ssh/*\
    && rm -rf /tmp/authorized_keys


RUN pip install --upgrade pip setuptools
#ADD /langchain /langchain
ADD requirements.txt /tmp/
WORKDIR /tmp/





#requirements.txt
RUN pip install -r requirements.txt

# in contrary to the pipfile we need some binaries for postgres too.
RUN pip install psycopg2-binary

#RUN wandb login 9496fad3a01360f3738da1943f702a02fa17d5d2

# Define environment variables
ENV MODEL_NAME="NumbersStation/nsql-llama-2-7B"
# Run your Python script

RUN python /tmp/load_hf_models.py
RUN python /tmp/download_nltk.py

ENV PYTHONPATH /workspace

WORKDIR /workspace


ENTRYPOINT service ssh restart && bash