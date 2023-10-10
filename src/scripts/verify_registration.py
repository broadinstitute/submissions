import argparse
import requests
import json
import os

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

def getGraphQlSchema(token):
    """Constructs graphql query to hit the gdc api"""

    # Define the GraphQL endpoint URL
    endpoint_url = "https://api.gdc.cancer.gov/v0/submission/graphql"

    # Define the introspection query
    type_name = "aliquot"

    introspection_query = f"""
        query IntrospectionQuery {{
            __type(name: "{type_name}") {{
            name
            fields {{
                name
                type {{
                name
                kind
                }}
            }}
            }}
        }}
    """
    # Create a headers dictionary with the Authorization header
    print(get_token_from_file(token))
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": get_token_from_file(token)
    }

    # Make a POST request to the GraphQL endpoint with the introspection query and headers
    response = requests.post(endpoint_url, json={'query': introspection_query}, headers=headers)

    # Check if the request was successful (HTTP status code 200)
    if response.status_code == 200:
        # Parse and print the response, which contains the schema information
        schema_data = response.json()
        print(schema_data)
    else:
        # Handle errors
        print(f"Error: {response.status_code}, {response.text}")

def getGdcShemas():
    """Queries gdc to get specific schema. Replace submitted_aligned_reads with any entity with any gdc entity"""

    endpoint = 'https://api.gdc.cancer.gov/v0/submission'
    response = requests.get(f'{endpoint}/template/aliquot?format=json')
    print(response)
    f = open(os.path.join(os.getcwd(), "sample_template.json"), 'w')
    f.write(response.text)
    f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--aliases', required=True, help='list of aliases to check registration status')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    args = parser.parse_args()

    getGraphQlSchema(args.token)
    check_registration(args.aliases, args.token, args.program, args.project)
    print("Script is finished")