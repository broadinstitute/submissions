import sys
import getopt
import argparse
import json
from src import access
from src import submit, getEntity, readMetadata
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
    submit(inputData)

    # now lets sleep() for a little to ensure that gdc has finished updating the UUID
    time.sleep(100)

    # now lets grab the submitted-aligned-reads-id *Need to change this back after testing
    # submitterId = f"{inputData['alias_value']}.{inputData['data_type']}.{inputData['agg_project']}"
    submitterId = "Test_aligned_4"
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

# Parses the command line input and populates the input dictionary
def getCommandLineInput(argv):
    inputData = {}
    longOptions = [
        'program=',
        'project=',
        'token=',
        'metadata=',
        'alias_value=',
        "step="
    ]
    opts, args = getopt.getopt(argv, '', longOptions)

    for opt, arg in opts:
        # print("opt", opt)
        # print("arg", arg)
        inputData[str(opt).replace("-", "")] = arg

    print("input data", inputData)
    return inputData

# Calls GDC to check if the sample is registered
def verifyRegistration(inputData):
    response = getEntity("verify", inputData['program'], inputData['project'], inputData['alias_value'], inputData['token'])
    response = json.loads(response.text)

    f = open("/cromwell_root/isValid.txt", 'w')

    if response['data'] and response['data']['aliquot'] and len(response['data']['aliquot']) > 0:
        f.write("Registered")
        f.close()
        print("Done writing UUID to file")  
        
        return True
    else:
        f.write("Not Registered")
        f.close()
        print("Not a valid response from GDC")

        return False

def validateFileStatus(inputData):
    """Calls the GDC api 10 times to periodically check the status of the given bam file.
       Writes the status to a file named fileStatus.txt"""

    response = None
    gdcCallCounter = 0
    validResponse = False
    data = readMetadata(inputData)

    while gdcCallCounter < 10 and not validResponse:
        print(f"{gdcCallCounter}th iteration of loop when trying to validate sample in GDC")

        submitterId = f"{data['alias_value']}.{data['data_type']}.{data['aggregation_project']}"
        response = getEntity("validate", inputData['program'], inputData['project'], submitterId, inputData['token'])
        response = json.loads(response.text)

        if response['data'] and response['data']['submitted_aligned_reads'] and len(response['data']['submitted_aligned_reads']) > 0:
            responseValue = response['data']['submitted_aligned_reads'][0]

            if responseValue['state'] == "validated" and (responseValue['file_state'] == "released" or responseValue['file_state'] == "validated"):
                validResponse = True
        
        # Will need to buff this up in the long run
        time.sleep(60)
        gdcCallCounter += 1

    f = open("/cromwell_root/fileStatus.txt", 'w')

    if validResponse:
        print("Sample is validated in GDC")
        f.write(f"Sample is inside of GDC.\n Current state {response}")
    else:
        f.write("Error when calling GDC")
        raise RuntimeError("Failed to validate file in GDC")

if __name__ == "__main__":
   main(sys.argv[1:])