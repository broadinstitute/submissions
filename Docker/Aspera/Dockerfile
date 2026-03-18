FROM python:3

RUN pip install requests

# Download and install Aspera client
RUN curl -o aspera.tar.gz https://d3gcli72yxqn2z.cloudfront.net/downloads/connect/latest/bin/ibm-aspera-connect_4.2.12.780_linux_x86_64.tar.gz \
    && tar -xzf aspera.tar.gz \
    && rm aspera.tar.gz

RUN chmod +x ibm-aspera-connect_4.2.12.780_linux_x86_64.sh

# Create a non-root user
RUN useradd -ms /bin/bash aspera-user


# DO NOT CHANGE ANYTHING BELOW THIS UNLESS YOU'RE ALSO PLANNING ON CHANGING THE TransferFile.wdl WHICH RELIES ON THIS
# SPECIFIC USER AND WHERE THESE FILES ARE INSTALLED

# Switch to the non-root user
USER aspera-user

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

RUN /ibm-aspera-connect_4.2.12.780_linux_x86_64.sh

ENV PATH="/home/aspera-user/.aspera/connect/bin:${PATH}"

CMD ["/bin/bash"]