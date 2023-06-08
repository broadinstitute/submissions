import argparse
import requests
import json

"""
    Overview:   
        This is a script that will take in a list of samples aliases and return which ones are registred in GDC

    Run:
        - Save the GDC auth token to a file in the same directory as the script
        
        python3 verify_registration.py -s [list of alias] -t [token_file] -pg [program] -pj [project]

        ex. with real samples
            python3 verify_registration.py -s "TCGA-CV-7183-01A-11D-A92Z-36, TCGA-4P-AA8J-01A-11D-A92Z-36, TCGA-4P-AA8J-10A-01D-A92Z-36" -t ./auth_token.txt -pj "HNSC" -pg "TCGA"

        logs.
            Starting check registration
            Registered Samples - ['TCGA-4P-AA8J-01A-11D-A92Z-36', 'TCGA-4P-AA8J-10A-01D-A92Z-36']
            Not Registered Samples - ['TCGA-CV-7183-01A-11D-A92Z-36']
            Script is finished
"""

def check_registration(aliases, token_file, program, project):
    """Takes in a list of aliases and will print to the console which ones are registered and which ones are not"""

    valid_samples = []
    invalid_samples = []

    print("Starting check registration")

    for alias in aliases.split(","):
        alias = alias.strip() # remove any spaces that could have been entered in the command line
        token = get_token_from_file(token_file)
        response = getEntity(program, project, alias, token)
        response = json.loads(response.text)

        if response['data'] and response['data']['aliquot'] and len(response['data']['aliquot']) > 0:
            valid_samples.append(alias)
        else:
            invalid_samples.append(alias)

    if len(invalid_samples) == 0:
        print("Congrats all samples are registred in GDC")
    else:
        print("Registered Samples -", valid_samples)
        print("Not Registered Samples -", invalid_samples)

def get_token_from_file(token_file):
    with open(token_file) as f:
        return f.readline()

def getEntity(program, project, submitterId, token):
    """Constructs graphql query to hit the gdc api"""

    query = {
        "query": f"{{\n \n  aliquot (project_id: \"{program}-{project}\", submitter_id: \"{submitterId}\") {{\n    id\n}}\n}}",
    }
    gdc_endpoint = 'https://api.gdc.cancer.gov/v0/submission'

    return requests.post(
        f"{gdc_endpoint}/graphql",
        json = query,
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": token
        }
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--aliases', required=True, help='list of aliases to check registration status')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    args = parser.parse_args()

    check_registration(args.aliases, args.token, args.program, args.project)
    print("Script is finished")