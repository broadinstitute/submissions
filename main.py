import sys
import getopt
import argparse
import json
from src import access
from src import submit, getEntity
import time

#### TODO - Need to add BETTER error handling for the whole application ### 

def main(argv):
    inputData = getCommandLineInput(argv)
    
    if "step" in inputData:
        # if we have agg_project in the input we know this is a submit workflow
        if inputData['step'] == "submit_metadata":
            submitMetadata(inputData)
        elif inputData['step'] == "verify_registration":
            print("Verify Registration")
            isValid = verifyRegistration(inputData)

            if isValid:
                print("Sample is valid in GDC")
            else:
                raise RuntimeError("Sample is not registered in GDC")
        elif inputData['step'] == "validate_status":
            validateFileStatus(inputData)
        else:
            print("Invalid step entered. Please check input")
    else:
        print("Input for step not found")

def submitMetadata(inputData):
    """Submits the metadata to gdc, then grabs the SAR_id and writes it to the file UUID.txt"""

    # opsMetadata = readMetadata(inputData)
    # verifySubmitInput(opsMetadata)
    submit(inputData)
    time.sleep(100)

    submitterId = f"{inputData['alias_value']}.{inputData['data_type']}.{inputData['agg_project']}"
    response = getEntity("sar", inputData['program'], inputData['project'], submitterId, inputData['token'])
    sarId = json.loads(response.text)

    if sarId and sarId['data'] and sarId['data']['submitted_aligned_reads']:
        if len(sarId['data']['submitted_aligned_reads']) > 0:
            f = open("/cromwell_root/UUID.txt", 'w')
            f.write(sarId['data']['submitted_aligned_reads'][0]['id'])
            f.close()
            print("Done writing UUID to file")
        else:
            print("No ids inside of submitted_aligned_reads array")
    else:
        print("Data was not returned from gdc properly")

def verifySubmitInput(opsMetadata):
    """Validates the input for the opsMetadata file"""

    # Basic input info
    if 'sample_alias' not in opsMetadata:
        print("Metadata file is missing sample_alias")
    if 'data_type' not in opsMetadata:
        print("Metadata file is missing data_type")
    if 'aggregation_project' not in opsMetadata:
        print("Metadata file is missing aggregation_project")

    # Submitter file info
    if 'file_size' not in opsMetadata:
        print("Metadata file is missing file_size")
    if 'md5' not in opsMetadata:
        print("Metadata file is missing md5")

    # Read Group info
    if 'read_groups' not in opsMetadata:
        print("Metadata file is missing read_groups")

def readMetadata(inputData):
    """Reads the metadata json file"""

    with open(inputData['metadata'], 'r') as my_file:
        return json.load(my_file)['samples'][0] # TODO - Need to be more defensive here

    print("Error when trying to parse the input Metadata file")

def getCommandLineInput(argv):
    """Parses the command line input and populates the input dictionary"""

    inputData = {}
    longOptions = [
        'program=',
        'project=',
        'token=',
        'metadata=',
        'alias_value=',
        "step=",
        "agg_path=",
        "agg_project=",
        "data_type=",
        "file_size=",
        "md5=",
        "read_groups="
    ]
    opts, args = getopt.getopt(argv, '', longOptions)

    for opt, arg in opts:
        inputData[str(opt).replace("-", "")] = arg

    return inputData

def verifyRegistration(inputData):
    """Calls GDC to check if the sample is registered. """

    response = getEntity("verify", inputData['program'], inputData['project'], inputData['alias_value'], inputData['token'])
    response = json.loads(response.text)

    f = open("/cromwell_root/isValid.txt", 'w')

    if response['data'] and response['data']['aliquot'] and len(response['data']['aliquot']) > 0:
        f.write("true")
        f.close()
        print("Done writing UUID to file")  
        
        return True
    else:
        f.write("false")
        f.close()
        print("Not a valid response from GDC", response)

        return False

def validateFileStatus(inputData):
    """Calls the GDC api 10 times to periodically check the status of the given bam file.
       Writes the status to a file named fileStatus.txt"""

    gdcCallCounter = 0
    fileStateDict = {
        "file_state": None,
        "state": None
    }

    while gdcCallCounter < 2 and not validFileState(fileStateDict):
        print(f"{gdcCallCounter}th iteration of loop when trying to validate sample in GDC")

        submitterId = f"{inputData['alias_value']}.{inputData['data_type']}.{inputData['agg_project']}"
        response = getEntity("validate", inputData['program'], inputData['project'], submitterId, inputData['token'])
        response = json.loads(response.text)

        if response['data'] and response['data']['submitted_aligned_reads'] and len(response['data']['submitted_aligned_reads']) > 0:
            responseValue = response['data']['submitted_aligned_reads'][0]
            fileStateDict['state'] = responseValue['state']
            fileStateDict['file_state'] = responseValue['file_state']
        
        # Will need to buff this up in the long run
        time.sleep(60)
        gdcCallCounter += 1

    f = open("/cromwell_root/fileStatus.txt", 'w')

    if fileStateDict['state'] != None and fileStateDict['file_state'] != None:
        print("Sample is validated in GDC")
        f.write(f"{fileStateDict['state']}\n{fileStateDict['file_state']}")
    else:
        print("Error when calling GDC")
        f.write("Error when calling GDC")

    f.close()

def validFileState(fileStateDict):
    """Checks to see if the file dictionary is in a valid state"""

    return (fileStateDict['state'] == "validated" and 
           (fileStateDict['file_state'] == "released" or 
            fileStateDict['file_state'] == "validated"))

if __name__ == "__main__":
   main(sys.argv[1:])