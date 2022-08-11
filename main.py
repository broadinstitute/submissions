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
    
    # if we have agg_project in the input we know this is a submit workflow
    if "agg_project" in inputData:
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
                f = open("UUID.txt", 'w')
                f.write(sarId['data']['submitted_aligned_reads'][0]['id'])
                f.close()
                print("Done writing UUID to file")
            else:
                print("No ids inside of submitted_aligned_reads array")
        else:
            print("Data was not returned from gdc properly")
    else:
        print("Verify Registration")
        isValid = verifyRegistration(inputData)

        if isValid:
            print("Sample is valid in GDC")
        else:
            raise RuntimeError("Sample is not registered in GDC")

# Parses the command line input and populates the input dictionary
def getCommandLineInput(argv):
    inputData = {}
    longOptions = [
        'program=',
        'project=',
        'agg_project=',
        'alias_value=',
        'data_type=',
        'token='
    ]
    opts, args = getopt.getopt(argv, '', longOptions)

    for opt, arg in opts:
        inputData[str(opt).replace("-", "")] = arg

    return inputData

# Calls GDC to check if the sample is registered
def verifyRegistration(inputData):
    response = getEntity("verify", inputData['program'], inputData['project'], inputData['alias_value'], inputData['token'])
    response = json.loads(response.text)

    if response['data'] and response['data']['aliquot'] and len(response['data']['aliquot']) > 0:
        return True
    else:
        return False

if __name__ == "__main__":
   main(sys.argv[1:])