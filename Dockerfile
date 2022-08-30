FROM ubuntu:18.04

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	python3-pip \
	wget \
	curl \
	unzip \
	build-essential \
	zlib1g-dev \
	libncurses5-dev \
	libncursesw5-dev \
	libbz2-dev \
	liblzma-dev \
	libcurl4-gnutls-dev && \
	apt-get upgrade -y --no-install-recommends python

	# Install samtools
RUN wget -q 'https://github.com/samtools/samtools/releases/download/1.10/samtools-1.10.tar.bz2' -O samtools.tar.bz && \
  tar xf samtools.tar.bz && \
  rm samtools.tar.bz && \
  cd samtools-1.10 && \
  make && \
  make install && \
  cd ../ && \
  rm -rf samtools-1.10

RUN wget -q https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.1_Ubuntu_x64.zip -O gdc-client.zip && \
    unzip gdc-client.zip -d bin && \
    rm gdc-client.zip

# Install gsutil
RUN wget https://dl.google.com/dl/cloudsdk/channels/rapid/install_google_cloud_sdk.bash -O gcloud_install.sh
RUN /bin/bash gcloud_install.sh --disable-prompts && \
  ln -s /root/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud && \
  ln -s /root/google-cloud-sdk/bin/gsutil /usr/local/bin/gsutil && \
  pip3 install --upgrade oauth2client