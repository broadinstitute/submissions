import requests
import json

# Need to figure out a better way to handle the env variables
endpoint = 'https://api.gdc.cancer.gov/v0/submission'

# Currently this function uses a hardcoded file, however we can expect that this will be passed in
def submit(input):
    # TODO - Need to set up seperate environments because the path is different on VM
    file = open('/src/resources/metadata.json')
    data = json.load(file)
    url = f"{endpoint}/{input['program']}/{input['project']}"

    print("Submit METADATA to GDC dry_run endpoint for PROGRAM PROJECT.")
    try:
        # These are simply helper functions.
        # linkSampleAndAliqout(url, input)
        # getGdcShemas()

        dryRunResponse = requests.put(f'{url}/_dry_run',
            data = json.dumps(data),
            headers = getHeaders(input)
        )
        print("response for the dry commit", dryRunResponse.text)
        dryRunResponse = json.loads(dryRunResponse.text)

        print("response", dryRunResponse)
        transaction_id = dryRunResponse['transaction_id']

        if dryRunResponse['success'] == True:
            print("Successfully submitted metadata for transaction", transaction_id)
            operation = "commit"
        else:
            print("Could not submit metadata for transaction", transaction_id)
            operation = "close"

        commitResponse = requests.put(f'{url}/transactions/{transaction_id}/{operation}',
            headers = getHeaders(input)
        )
    except Exception as e:
        print("Error", e)

def getEntity(queryType, program, project, submitterId, token):
    query = ""

    if queryType == "sar":
        query = {
            "query": f"{{\n \n  submitted_aligned_reads (project_id: \"{program}-{project}\", submitter_id: \"{submitterId}\") {{\n    id\n}}\n}}",
        }
    elif queryType == "verify":
        query = {
            "query": f"{{\n \n  aliquot (project_id: \"{program}-{project}\", submitter_id: \"{submitterId}\") {{\n    id\n}}\n}}",
        }
    else:
        query = {
            "query": f"{{\n \n  submitted_aligned_reads (project_id: \"{program}-{project}\", submitter_id: \"{submitterId}\") {{\n    id\n    submitter_id\n    state\n     file_state\n    error_type\n}}\n}}",
        }

    return requests.post(
        f"{endpoint}/graphql",
        json = query,
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": token
        }
    )

def linkSampleAndAliqout(url, input):
    data = [
        {
            "type": "case",
            "projects": {
                "code": "TEST4"
            },
            "submitter_id": "BROAD-TEST4-0001"
        },
        {
            "type": "sample",
            "cases": {
                "submitter_id": "BROAD-TEST4-0001"
            },
            "submitter_id": "Test_sample_1",
            "sample_type": "Primary Tumor",
            "tissue_type": "Tumor"
        },
        {
            "type": "aliquot",
            "samples": {
                "submitter_id": "Test_sample_1"
            },
            "submitter_id": "Test_aliquot_1"
        },
        {
            "type": "read_group",
            "aliquots": {
                "submitter_id": "Test_aliquot_1"
            },
            "submitter_id": "Test_read_group_1",
            "experiment_name": "This is a test",
            "sequencing_center": "TEST",
            "platform": "Other",
            "library_selection": "Other",
            "library_strategy": "WGS",
            "library_name": "TEST",
            "is_paired_end": True,
            "read_length": 151,
            "read_group_name": "TEST",
            "target_capture_kit": "Unknown"
        }
    ]

    response = requests.put(url,
        data = json.dumps(data),
        headers = getHeaders(input)
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
    response = requests.get(f'{endpoint}/template/sample?format=json')
    print("sample response", response.text)
    f = open('src/resources/sample_template.json', 'w')
    f.write(response.text)
    f.close()
