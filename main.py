import sys
import getopt
import argparse
from src import access
from src import submit

def main(argv):
    inputData = {}
    longOptions = [
        'program=',
        'project=',
        'data_format=',
        'submitter_id=',
        'step='
    ]
    opts, args = getopt.getopt(argv, 'gjdics', longOptions)

    for opt, arg in opts:
        inputData[str(opt).replace("-", "")] = arg

    if inputData['step'] == "compileMetadata":
        print("Need to compile Metadata")
        access(inputData)
    else:
        print("program", inputData['program'])
        print("project", inputData['project'])
        print("submitter_id", inputData['submitter_id'])
        print("Did not enter valid step")
        submit(inputData)

    print(inputData)

if __name__ == "__main__":
   main(sys.argv[1:])