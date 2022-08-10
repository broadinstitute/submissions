import sys
import getopt
import argparse
import json
from src import access
from src import submit, getEntity
import time

def main(argv):
    inputData = getCommandLineInput(argv)
    # This needs to go in its own workflow - verifyRegistration(inputData)
    if "agg_project" in inputData:
        submit(inputData)

        # now lets sleep() for a little to ensure that gdc has finished  
        time.sleep(10)

        # now lets grab the submitted-aligned-reads-id
        submitterId = f"{inputData['alias']}.{inputData['data_type']}.{inputData['agg_project']}"
        sarId = getEntity("sar", inputData['program'], inputData['project'], submitterId, inputData['token'])
        print(sarId)
    else:
        print("Verify Registration")
        isValid = verifyRegistration(inputData)
        print("isvalid", isValid)

def getCommandLineInput(argv):
    inputData = {}
    longOptions = [
        'program=',
        'project=',
        'agg_project=',
        'alias=',
        'data_type=',
        'token='
    ]
    opts, args = getopt.getopt(argv, '', longOptions)

    for opt, arg in opts:
        inputData[str(opt).replace("-", "")] = arg

    return inputData

def verifyRegistration(inputData):
    response = getEntity("verify", inputData['program'], inputData['project'], inputData['alias'], inputData['token'])
    response = json.loads(response.text)

    print("response", response)
    if response['data'] and response['data']['aliquot'] and len(response['data']['aliquot']) > 0:
        return True
    else:
        return False

if __name__ == "__main__":
   main(sys.argv[1:])