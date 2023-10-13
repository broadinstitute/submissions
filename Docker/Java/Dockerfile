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

# Copy your JAR file into the container
COPY . .

# Define the command to run your JAR file
CMD ["java", "-jar", "your_app.jar"]

docker build -t my-java-app --build-arg JAR_FILE=your_app.jar .