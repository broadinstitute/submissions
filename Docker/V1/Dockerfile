FROM python:3

RUN pip install requests
RUN wget -q 'https://github.com/samtools/samtools/releases/download/1.10/samtools-1.10.tar.bz2' -O samtools.tar.bz && \
  tar xf samtools.tar.bz && \
  rm samtools.tar.bz && \
  cd samtools-1.10 && \
  make && \
  make install && \
  cd ../ && \
  rm -rf samtools-1.10

RUN wget https://releases.hashicorp.com/vault/1.4.0/vault_1.4.0_linux_amd64.zip -O vault.zip && \
  unzip vault.zip -d /usr/bin && \
  rm vault.zip
RUN wget https://dl.google.com/dl/cloudsdk/channels/rapid/install_google_cloud_sdk.bash -O gcloud_install.sh
RUN /bin/bash gcloud_install.sh --disable-prompts && \
  ln -s /root/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud && \
  ln -s /root/google-cloud-sdk/bin/gsutil /usr/local/bin/gsutil && \
  pip3 install --upgrade oauth2client

# Set up the GDC client
# Install client
RUN wget -q https://gdc.cancer.gov/system/files/public/file/gdc-client_2.3_Ubuntu_x64-py3.8-ubuntu-20.04.zip -O gdc-client.zip
# Unzip the tar file
RUN unzip gdc-client.zip
RUN unzip gdc-client_2.3_Ubuntu_x64.zip -d bin
RUN rm gdc-client.zip && \
    rm gdc-client_2.3_Ubuntu_x64.zip



CMD ["/bin/bash"]