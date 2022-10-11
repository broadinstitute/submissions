# Docker Containers
Currently we have two different images being pushed up to Dockerhub. 

Dockerhub repo - schaluvadi/horsefish

## Python
This image is strictly for being able to run the python scripts. It will install all python dependencies from the requirements.txt file onto the docker image.

### Build and Push Image
    cd docker/python
    docker build . -t schaluvadi/horsefish:submissionV1
    docker push schaluvadi/horsefish:submissionV1

## Bash
This image will be so certain task can run specific cli commands such as sam-tools, gdc-client and gsutil.

Current task list
- RetrieveGdcManifest
- TransferBamToGdc

All other task will use the python image