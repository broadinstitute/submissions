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
    data = readMetadata(inputData)
    submitterId = f"{data['sample_alias']}.{data['data_type']}.{data['aggregation_project']}"
    dataTypeToExperimentalStrategy = {
        "WGS": "WGS",
        "Exome": "WXS",
        "RNA": "RNA-Seq",
        "Custom_Selection": "Targeted Sequencing"
    }

    print("this is the data", data)
    metadata = {
        "file_name": f"{submitterId}.bam",
        "submitter_id": submitterId,
        "data_category": "Sequencing Reads",
        "type": "submitted_aligned_reads",
        "file_size": data['file_size'],
        "data_type": "Aligned Reads",
        "experimental_strategy": dataTypeToExperimentalStrategy[data['data_type']],
        "data_format": "BAM",
        "project_id": f"{inputData['program']}-{inputData['project']}",
        "md5sum": data['md5'],
        "proc_internal": "dna-seq skip",
        "read_groups": getSubmitterIdForReadGroups(data)
    }

    print("metadata after", metadata)

    return metadata

def readMetadata(inputData):
    with open(inputData['metadata'], 'r') as my_file:
        return json.load(my_file)['samples'][0] # TODO - Need to be more defensive here

    print("Error when trying to parse the input Metadata file")

def getSubmitterIdForReadGroups(data):
    submitterIds = []
    submitterIdConstant = f"{data['aggregation_project']}.{data['sample_alias']}"

    for readGroup in data['read_groups']:
        submitterIds.append({
            "submitter_id": f"{readGroup['flow_cell_barcode']}.{readGroup['lane_number']}.{submitterIdConstant}"
        })

    return submitterIds

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

    f = open('src/resources/sample_template.json', 'w')
    f.write(response.text)
    f.close()
