import requests
import json

# Need to figure out a better way to handle the env variables
endpoint = 'https://api.gdc.cancer.gov/v0/submission'

# Currently this function uses a hardcoded file, however we can expect that this will be passed in
def submit(input):
    file = open('src/resources/metadata.json')
    data = json.load(file)
    url = f"{endpoint}/{input['program']}/{input['project']}"

    print("Submit METADATA to GDC dry_run endpoint for PROGRAM PROJECT.")
    try:
        dryRunResponse = requests.post(f'{url}/_dry_run',
            data = json.dumps(data),
            headers = getHeaders()
        )
        print("dryRunResponse", json.loads(dryRunResponse.text))
        transaction_id = json.loads(dryRunResponse.text).transaction_id

        if dryRunResponse.success == true:
            print("Successfully submitted metadata for transaction", transaction_id)
            operation = "commit"
        else:
            print("Could not submit metadata for transaction", transaction_id)
            operation = "close"

        commitResponse = requests.post(f'{url}/transactions/{transaction_id}/{operation}',
            headers = getHeaders()
        )
    except Exception as e:
        print("Error", e)

def getHeaders():
    fileToken = open('tokens/gdc-token.txt')
    token = fileToken.read()

    return {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }

# Run this function if you would like to see all entity schemas in GDC
def getGdcShemas():
    response = requests.get(f'{endpoint}/_dictionary/_all', params = {})
    f = open('src/resources/reads_output.json', 'w')
    f.write(response.text)
    f.close()
