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
    submit(inputData)

    # now lets sleep() for a little to ensure that gdc has finished updating the UUID
    time.sleep(10)

    # now lets grab the submitted-aligned-reads-id *Need to change this back after testing
    # submitterId = f"{inputData['alias_value']}.{inputData['data_type']}.{inputData['agg_project']}"
    submitterId = "Test_aligned_1"
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
        'agg_project=',
        'alias_value=',
        'data_type=',
        'token=',
        "step="
    ]
    opts, args = getopt.getopt(argv, '', longOptions)

    for opt, arg in opts:
        inputData[str(opt).replace("-", "")] = arg

    return inputData

# Calls GDC to check if the sample is registered
def verifyRegistration(inputData):
    response = getEntity("verify", inputData['program'], inputData['project'], inputData['alias_value'], inputData['token'])
    response = json.loads(response.text)

    f = open("/cromwell_root/isValid.txt", 'w')

    if response['data'] and response['data']['aliquot'] and len(response['data']['aliquot']) > 0:
        f.write("isValid")
        
        return True
    else:
        f.write("Not valid")

        return False

    f.close()
    print("Done writing UUID to file")

def validateFileStatus(inputData):
    gdcCallCounter = 0
    validResponse = false

    while gdcCounter < 10 and not validResponse:
        print(f"{gdcCallCounter}th iteration of loop when trying to validate sample in GDC")

        # submitterId = f"{inputData['alias_value']}.{inputData['data_type']}.{inputData['agg_project']}"
        submitterId = "Test_aligned_1"
        response = getEntity("validate", inputData['program'], inputData['project'], submitterId, inputData['token']).text
        
        if response['data'] and response['data']['submitted_aligned_reads'] and len(response['data']['submitted_aligned_reads']) > 0:
            responseValue = response['data']['submitted_aligned_reads']

            if responseValue['state'] == "validated" and (responseValue['file_state'] == "registered" or responseValue['file_state'] == "validated"):
                validResponse = true
        
        # Will need to buff this up in the long run
        sleep(600)
        gdcCallCounter += 1

    
    if validResponse:
        print("Sample is validated in GDC")
    else:
        raise RuntimeError("Failed to validate file in GDC")

if __name__ == "__main__":
   main(sys.argv[1:])