import sys
# from rich import print, print_json
from .clio import callClio

def access(input):
    # First we need to call Clio to start compiling the metadata
    print("We made it here")
    clio = callClio(input)
    print_json(clio)