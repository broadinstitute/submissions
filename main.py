import sys
import getopt
import argparse
import json
from src import access
from src import submit, getSubmittedAlignedReadsId
import time

def main(argv):
    inputData = getCommandLineInput(argv)
    submit(inputData)

    # now lets sleep() for a little to ensure that gdc has finished  
    time.sleep(10)

    # now lets grab the submitted-aligned-reads-id
    submitterId = f"{inputData['alias']}.{inputData['data_type']}.{inputData['agg_project']}"
    sarId = getSubmittedAlignedReadsId(inputData['program'], inputData['project'], submitterId, inputData['token'])
    print(sarId)

def getCommandLineInput(argv):
    inputData = {}
    longOptions = [
        'program=',
        'project=',
        'agg_project=',
        'alias=',
        'sequence_type=',
        'data_type=',
        'token='
    ]
    opts, args = getopt.getopt(argv, '', longOptions)

    for opt, arg in opts:
        inputData[str(opt).replace("-", "")] = arg

    return inputData

if __name__ == "__main__":
   main(sys.argv[1:])