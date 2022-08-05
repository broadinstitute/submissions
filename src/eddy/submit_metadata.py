import requests
import json

# Need to figure out a better way to handle the env variables
endpoint = 'https://api.gdc.cancer.gov/v0/submission'

# Currently this function uses a hardcoded file, however we can expect that this will be passed in
def submit(input):
    file = open('src/resources/metadata.json')
    data = json.load(file)
    url = f"{endpoint}/{input['program']}/{input['project']}"

    # print("Submit METADATA to GDC dry_run endpoint for PROGRAM PROJECT.")
    try:
        dryRunResponse = requests.post(f'{url}/_dry_run',
            data = json.dumps(data),
            headers = getHeaders(input)
        )
        dryRunResponse = json.loads(dryRunResponse.text)
        transaction_id = dryRunResponse['transaction_id']

        if dryRunResponse['success'] == true:
            # print("Successfully submitted metadata for transaction", transaction_id)
            operation = "commit"
        else:
            # print("Could not submit metadata for transaction", transaction_id)
            operation = "close"

        commitResponse = requests.post(f'{url}/transactions/{transaction_id}/{operation}',
            headers = getHeaders(input)
        )
    except Exception as e:
        print("Error", e)

def getSubmittedAlignedReadsId(program, project, submitterId, token):
    query = """query submitted_aligned_reads ($project_id: String, $submitter_id: Int) { id }"""
    variables = {
        'project_id': f'{program}-{project}',
        'submitter_id': submitterId
    }

    return requests.post(
        endpoint,
        json = {
            'query': query,
            'variables': variables
        },
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": token
        }
    )

def getHeaders(input):
    # fileToken = open('tokens/gdc-token.txt')
    # token = fileToken.read()

    return {
        "Content-Type": "application/json",
        "X-Auth-Token": input['token']
    }

# Run this function if you would like to see all entity schemas in GDC
def getGdcShemas():
    response = requests.get(f'{endpoint}/_dictionary/_all', params = {})
    f = open('src/resources/reads_output.json', 'w')
    f.write(response.text)
    f.close()
