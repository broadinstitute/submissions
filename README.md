# Submissions 
This repository contains workflows to submit and verify data with two different government repositories: [GDC](https://portal.gdc.cancer.gov/) and [dbGaP](https://www.ncbi.nlm.nih.gov/gap/)

## Submitting Data to GDC
There are two steps to submitting data to the GDC: submission and validation. 
* First, use the [transferToGDC](https://dockstore.org/workflows/github.com/broadinstitute/submissions/transferToGDC:main?tab=info) workflow to transfer your files. The README is located at the bottom of the page at that link, which describes what each input to the workflow is. 
  * Note that read-group level metadata can either be provided in the Terra metadata tables (this should be used for older samples run via Zamboni), OR it can be provided in a JSON file (the `read_group_metadata_json`, which should be used for newer samples run via DRAGEN). 
* After samples have been submitted, their validation status can be checked by using the [validateGDCStatus](https://dockstore.org/workflows/github.com/broadinstitute/submissions/validateGDCStatus:main?tab=info) workflow. This workflow will check each sample's validation status within the GDC and update the Terra metadata tables with the validation status. 

## Submitting Data to dbGaP 
There are two steps to submitting data to dbGapP: submission and validation.
* First, use the [transferToDbgap](https://dockstore.org/workflows/github.com/broadinstitute/submissions/transferToDbgap:main?tab=info) workflow to transfer your files. The README is located at the bottom of the page at that link, which described what each input to the workflow is.
  * Note that read-group level metadata can either be provided in the Terra metadata tables (this should be used for older samples run via Zamboni), OR it can be provided in a JSON file (the `read_group_metadata_json`, which should be used for newer samples run via DRAGEN).
* After samples have been submitted, their validation status can be checked by using the [validateDbGapStatus](https://dockstore.org/workflows/github.com/broadinstitute/submissions/validateDbGapStatus:main?tab=info) workflow. This workflow will check each sample's validation status within dbGaP and update the Terra metadata tables with the validation status.


## Deploying Changes in this Repository 
### When making changes to the .wdl files
Nothing is required if only the .wdl files are changed. Once your branch is merged to `main`, dockstore will automatically get updated with the most recent changes. In your Terra workspace, you can always verify what code is running by looking at the source code (in Terra on GCP, this can be found in the "SCRIPT" tab when you're navigated to your workflow configuration page). 

### When making changes to the Python files
If you've made a change to your Python file, most likely you'll need to recreate and push the image using the [V2 Dockerfile](Docker/V2/Dockerfile) since this is the one that contains all the Python code. You'll need to build, tag and push the docker image to [this repository](https://hub.docker.com/r/schaluvadi/horsefish/tags). Note that even though this repository is public, you'll need to be added as a collaborator in order to successfully push changes to it. 

#### Building the Docker image - how to find which image to re-build
If you've updated any of the Python code, the docker image(s) will have to be rebuilt and pushed to DockerHub. First track down where in which `.wdl` file that Python code is called. Now in that `.wdl`, find the Docker image that's defined in the runtime attributes. This should correspond to one of the Docker files that are located within a subdirectory of [Docker](Docker). Once you've found the Dockerfile you'll need to re-create, you can use the following commands to build and push the docker images (note, you don't have to necessarily build all three images, but these are the commands to use in case you do): 
```commandline
docker build -t schaluvadi/horsefish:submissionAspera -f Docker/Aspera/Dockerfile . --platform="linux/amd64"

docker build -t schaluvadi/horsefish:submissionV2 -f Docker/V2/Dockerfile . --platform="linux/amd64"

docker build -t schaluvadi/horsefish:submissionV1 -f Docker/V1/Dockerfile . --platform="linux/amd64"
```
You'll need to add the `--platform="linux/amd64`  in case your default platform is different on your machine. 
Once you've successfully created the Docker image, you can run `docker images` and you should see a newly created image. If you're like to verify anything, you can open the image in an interactive shell. First run `docker images` and copy the `IMAGE ID` of your new image. Next run `docker run -it {IMAGE_ID}`. This opens an interactive shell where you can run regular unix commands such as `cd`, `grep`, `vim`, etc.

#### Pushing your new Docker image
Once you're recreated your image and verified that your changes have propagated locally, you'll need to push your new image version to [this public repository](https://hub.docker.com/r/schaluvadi/horsefish/tags).
You can do so by running any of the following commands (depending on which image you have built and need to push): 
```commandLine
docker push schaluvadi/horsefish:submissionAspera
docker push schaluvadi/horsefish:submissionV2
docker push schaluvadi/horsefish:submissionV1
```

## SSH Key Creation and Usage Guide
This guide provides instructions for creating an SSH key pair and utilizing it to establish secure connections with dbGaP.

### SSH Key Generation
To generate an SSH key pair, follow these steps:
1. Open a terminal or command prompt.
2. Use the following command:
    ```
    ssh-keygen -t rsa -m PEM -f ./private.openssh
    ```
This command will generate two files in your current directory:
- `private.openssh`: Your private key.
- `private.openssh.pub`: Your public key.

### Linking Your Public Key
Once you have generated your SSH key pair, follow these steps to link your public key:
1. Send your public SSH key (`private.openssh.pub`) to `richard.lapoint@nih.gov`.

### Uploading Your Private Key
After linking your public key, you can upload your private key to the designated workspace.
![Updating key in Terra](images/key_upload.png)
**Note:** Keep your private key secure and do not share it with anyone.

## Support
For any inquiries or assistance, please contact Nareh Sahakian at `sahakian@broadinstitute.org`.

## Disclaimer
Ensure you follow your organization's security policies and guidelines when managing SSH keys and accessing workspaces.
