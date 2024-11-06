# Deploying Changes
## When making changes to the .wdl files
Nothing is required if only the .wdl files are changed. Once your branch is merged to `main`, dockstore will automatically get updated with the most recent changes. In your Terra workspace, you can always verify what code is running by looking at the source code (in Terra on GCP, this can be found in the "SCRIPT" tab when you're navigated to your workflow configuration page). 

## When making changes to the Python files
If you've made a change to your Python file, most likely you'll need to recreate and push the image using the [V2 Dockerfile](Docker/V2/Dockerfile) since this is the one that contains all the Python code. You'll need to build, tag and push the docker image to [this repository](https://hub.docker.com/r/schaluvadi/horsefish/tags). Note that even though this repository is public, you'll need to be added as a collaborator in order to successfully push changes to it. 

### Building the Docker image - how to find which image to re-build
Say you've updated some Python code and you want this available in Terra. First track down where in which `.wdl` file that Python code is called. Now in that `.wdl`, find the Docker image that's defined in the runtime attributes. This should correspond to one of the Docker files that are located within a subdirectory of [Docker](Docker). Once you've found the Dockerfile you'll need to re-create, you can do so with a command such as the following from the ROOT of the repository: 
```commandline
docker build -t schaluvadi/horsefish:submissionV2GDC -f Docker/V2/Dockerfile . --platform="linux/amd64"
```
Be sure to replace `horsefish:submissionV2GDC` with the correct tag from [this repository](https://hub.docker.com/r/schaluvadi/horsefish/tags), and replace `Docker/V2/Dockerfile` with the Dockerfile you're trying to update. You'll need to add the `--platform="linux/amd64`  in case your default platform is different. 
Once you've successfully created the Docker image, you can run `docker images` and you should see a newly created image. If you're like to verify anything, you can open the image in an interactive shell. First run `docker images` and copy the `IMAGE ID` of your new image. Next run `docker run -it {IMAGE_ID}`. This opens an interactive shell where you can run regular unix commands such as `cd`, `grep`, `vim`, etc.

### Pushing your new Docker image
Once you're recreated your image and verified that your changes have propagated locally, you'll need to push your new image version to [this public repository](https://hub.docker.com/r/schaluvadi/horsefish/tags).
You can do so by running a command such as (be sure to replace `submissionV2GDC` with the correct image tag!): 
```
docker push schaluvadi/horsefish:submissionV2GDC
```

# SSH Key Creation and Usage Guide

## Introduction
This guide provides instructions for creating an SSH key pair and utilizing it to establish secure connections with DbGap.

## SSH Key Generation
To generate an SSH key pair, follow these steps:
1. Open a terminal or command prompt.
2. Use the following command:
    ```
    ssh-keygen -t rsa -m PEM -f ./private.openssh
    ```
This command will generate two files in your current directory:
- `private.openssh`: Your private key.
- `private.openssh.pub`: Your public key.

## Linking Your Public Key
Once you have generated your SSH key pair, follow these steps to link your public key:
1. Send your public SSH key (`private.openssh.pub`) to `richard.lapoint@nih.gov`.

## Uploading Your Private Key
After linking your public key, you can upload your private key to the designated workspace.
![Updating key in Terra](images/key_upload.png)
**Note:** Keep your private key secure and do not share it with anyone.

## Support
For any inquiries or assistance, please contact Paul Hendriksen at `phendrik@broadinstitute.org`.

## Disclaimer
Ensure you follow your organization's security policies and guidelines when managing SSH keys and accessing workspaces.
