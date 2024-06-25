# Deploying Changes
## When making changes to the .wdl files
Nothing is required if only the .wdl files are changed. Once your branch is merged to `main`, dockstore will automatically get updated with the most recent changes. In your Terra workspace, you can always verify what code is running by looking at the source code (in Terra on GCP, this can be found in the "SCRIPT" tab when you're navigated to your workflow configuration page). 

## When making changes to the Python files
If you've made a change to your Python file, most likely you'll need to recreate and push the image using the [V2 Dockerfile](Docker/V2/Dockerfile) since this is the one that contains all the Python code. You'll need to build, tag and push the docker image to [this repository](https://hub.docker.com/r/schaluvadi/horsefish).

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
