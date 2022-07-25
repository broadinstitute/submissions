import sys
import getopt
import argparse
import click
from src import access

def main(argv):
    inputData = {}

    try:
        longOptions = [
            'program=',
            'project=',
            'data_format=',
            'step='
        ]
        opts, args = getopt.getopt(argv, 'gjdcs', longOptions)

        for opt, arg in opts:
            inputData[str(opt).replace("-", "")] = arg

        if inputData['step'] == "compileMetadata":
            print("Need to compile Metadata")
            access(inputData)
        else:
            print("Did not enter valid step")

        print(inputData)
    except:
        # Add better error handeling here
        print("error")

if __name__ == "__main__":
   main(sys.argv[1:])