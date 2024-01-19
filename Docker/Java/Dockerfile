# Use an official Ubuntu base image
FROM ubuntu:20.04

# Set environment variables for Java installation
ENV DEBIAN_FRONTEND=noninteractive \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 \
    PATH=$PATH:/usr/lib/jvm/java-11-openjdk-amd64/bin

# Install OpenJDK 11
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a directory for your JAR file
WORKDIR /app

# Define an ARG to accept the JAR file name as a build argument
ARG JAR_FILE

# Copy the JAR file into the container at /app
COPY ${JAR_FILE} /app/

ENV JAR_FILE_PATH=/app/${JAR_FILE}

CMD ["/bin/bash"]# Use an official Ubuntu base image
FROM ubuntu:20.04

# Set environment variables for Java installation
ENV DEBIAN_FRONTEND=noninteractive \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 \
    PATH=$PATH:/usr/lib/jvm/java-11-openjdk-amd64/bin

# Install OpenJDK 11
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a directory for your JAR file
WORKDIR /app

# Define an ARG to accept the JAR file name as a build argument
ARG JAR_FILE

# Copy the JAR file into the container at /app
COPY ${JAR_FILE} /app/

ENV JAR_FILE_PATH=/app/${JAR_FILE}

CMD ["/bin/bash"]