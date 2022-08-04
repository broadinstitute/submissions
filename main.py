import sys
import getopt
import argparse
from src import access
from src import submit
import time

def main(argv):
    inputData = getCommandLineInput(argv)
    submit(inputData)

    # now lets sleep() for a little to ensure that gdp has finished  
    time.sleep(10)

    # now lets grab the submitted-aligned-reads-id
    submitterId = f"{inputData['alias']}.{inputData['type']}.{inputData['agg_project']}"
    sarId = getSubmittedAlignedReadsId(inputData['program'], inputData['project'], submitterId)
    print("sarId", sarId)

def getCommandLineInput(argv):
    inputData = {}
    longOptions = [
        'program=',
        'project=',
        'agg_project=',
        'alias=',
        'type='
    ]
    opts, args = getopt.getopt(argv, '', longOptions)

    for opt, arg in opts:
        inputData[str(opt).replace("-", "")] = arg

    return inputData

def getSubmittedAlignedReadsId(program, project, submitterId):
    query = """query {

    }"""

if __name__ == "__main__":
   main(sys.argv[1:])