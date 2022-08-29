import requests
import json

# Need to figure out a better way to handle the env variables
endpoint = 'https://api.gdc.cancer.gov/v0/submission'

# Currently this function uses a hardcoded file, however we can expect that this will be passed in
def submit(input):
    # getGdcShemas()
    url = f"{endpoint}/{input['program']}/{input['project']}"
    # linkSampleAndAliqout(url, input)

    # TODO - Need to set up seperate environments because the path is different on VM
    # file = open('/src/resources/metadataUpdated.json')
    # data = json.load(file)
    data = createMetadata(input)

    print("Submit METADATA to GDC dry_run endpoint for PROGRAM PROJECT.")
    try:
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

def createMetadata(inputData):
    submitterId = f"{inputData['alias_value']}.{inputData['data_type']}.{inputData['agg_project']}"
    dataTypeToExperimentalStrategy = {
        "WGS": "WGS",
        "Exome": "WXS",
        "RNA": "RNA-Seq",
        "Custom_Selection": "Targeted Sequencing"
    }

    metadata = {
        "file_name": f"{submitterId}.bam",
        "submitter_id": submitterId,
        "data_category": "Sequencing Reads",
        "type": "submitted_aligned_reads",
        "file_size": inputData['bam_filesize'],
        "data_type": "Aligned Reads",
        "experimental_strategy": dataTypeToExperimentalStrategy[inputData['data_type']],
        "data_format": "BAM",
        "project_id": f"{inputData['program']}-{inputData['project']}",
        "md5sum": inputData['bam_md5'],
        "proc_internal": "dna-seq skip",
        "read_groups": findReadGroups()
    }

def findReadGroups(inputData):
    data = json.load(inputData[''])
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
    f = open('src/resources/linkData.json')
    data = json.load(f)

    response = requests.put(url,
        data = json.dumps(data),
        headers = getHeaders(input)
    )

    print("response for creating links", response.text)
    
def getHeaders(input):
    return {
        "Content-Type": "application/json",
        "X-Auth-Token": input['token']
    }

# Run this function if you would like to see all entity schemas in GDC
def getGdcShemas():
    response = requests.get(f'{endpoint}/template/submitted_aligned_reads?format=json')
    print("sample response", response.text)
    f = open('src/resources/sample_template.json', 'w')
    f.write(response.text)
    f.close()
