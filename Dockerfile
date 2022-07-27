FROM python:3
RUN pip install requests

# Install samtools
RUN wget -q 'https://github.com/samtools/samtools/releases/download/1.10/samtools-1.10.tar.bz2' -O samtools.tar.bz && \
  tar xf samtools.tar.bz && \
  rm samtools.tar.bz && \
  cd samtools-1.10 && \
  make && \
  make install && \
  cd ../ && \
  rm -rf samtools-1.10

# Install GDC Data Transfer Tool
RUN wget -q https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.0_Ubuntu_x64-py3.7.zip -O gdc-client.zip && \
    unzip gdc-client.zip && \
    unzip gdc-client_v1.6.0_Ubuntu_x64.zip -d bin && \
    rm gdc-client_v1.6.0_Ubuntu_x64.zip && \
    rm gdc-client.zip

# Install Vault
RUN wget https://releases.hashicorp.com/vault/1.4.0/vault_1.4.0_linux_amd64.zip -O vault.zip && \
  unzip vault.zip -d /usr/bin && \
  rm vault.zip

# Install gsutil
RUN wget https://dl.google.com/dl/cloudsdk/channels/rapid/install_google_cloud_sdk.bash -O gcloud_install.sh
RUN /bin/bash gcloud_install.sh --disable-prompts && \
  ln -s /root/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud && \
  ln -s /root/google-cloud-sdk/bin/gsutil /usr/local/bin/gsutil && \
  pip3 install --upgrade oauth2client

ENTRYPOINT [ "python" ]