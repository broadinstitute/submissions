import argparse
import requests
import json
import os
from src.services.gdc_api import GdcApiWrapper

def check_registration(alias, program, project, token):
    response = GdcApiWrapper(program, project, token).get_entity("verify", alias)
    response = json.loads(response.text)

    if response['data'] and response['data']['aliquot'] and len(response['data']['aliquot']) > 0:
        print("True")  
    else:
        raise RuntimeError("Sample is not registered in GDC")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--sample_alias', required=True, help='list of aliases to check registration status')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    args = parser.parse_args()

    check_registration(args.sample_alias, args.token, args.program, args.project)