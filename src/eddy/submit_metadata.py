import requests
import json

# Need to figure out a better way to handle the env variables
endpoint = 'https://api.gdc.cancer.gov/v0/submission'

def submit(input, opsMetadata):
    """Submits the formatted metadata to gdc api"""

    url = f"{endpoint}/{input['program']}/{input['project']}"
    gdcFormattedMetadata = createMetadata(input, opsMetadata)

    print("Submit METADATA to GDC dry_run endpoint for PROGRAM PROJECT.")
    try:
        dryRunResponse = requests.put(f'{url}/_dry_run',
            data = json.dumps(gdcFormattedMetadata),
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

def createMetadata(inputData, opsMetadata):
    """Uses the opsMetadata file to format metadata to be submitted to gdc"""

    submitterId = f"{opsMetadata['sample_alias']}.{opsMetadata['data_type']}.{opsMetadata['aggregation_project']}"
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
        "file_size": opsMetadata['file_size'],
        "data_type": "Aligned Reads",
        "experimental_strategy": dataTypeToExperimentalStrategy[opsMetadata['data_type']],
        "data_format": "BAM",
        "project_id": f"{inputData['program']}-{inputData['project']}",
        "md5sum": opsMetadata['md5'],
        "proc_internal": "dna-seq skip",
        "read_groups": getSubmitterIdForReadGroups(opsMetadata)
    }
    # Need to write bam name and bam file to a file so we can access it in the wdl. Talk to Sushma!
    # writeBamDataToFile(opsMetadata)

    return metadata

def writeBamDataToFile(data):
    """Extracts bam path and bam name and writes to a file named bam.txt"""

    bamFileName = data['aggregation_path'].split('/')[-1]
    f = open("/cromwell_root/bam.txt", 'w')
    f.write(f"{data['aggregation_path']}\n{bamFileName}")
    f.close()

def getSubmitterIdForReadGroups(data):
    """Extracts all submitterIds for each read_group inside of sample_metadata"""

    submitterIds = []
    submitterIdConstant = f"{data['aggregation_project']}.{data['sample_alias']}"

    for readGroup in data['read_groups']:
        submitterIds.append({
            "submitter_id": f"{readGroup['flow_cell_barcode']}.{readGroup['lane_number']}.{submitterIdConstant}"
        })

    return submitterIds

def getEntity(queryType, program, project, submitterId, token):
    """Constructs graphql query to hit the gdc api"""

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
    """Helper function to create entities inside of gdc"""

    f = open('src/resources/linkData.json')
    data = json.load(f)
    response = requests.put(url,
        data = json.dumps(data),
        headers = getHeaders(input)
    )

    print("response for creating links", response.text)
    
def getHeaders(input):
    """Returns general headers for gdc api call"""

    return {
        "Content-Type": "application/json",
        "X-Auth-Token": input['token']
    }

def getGdcShemas():
    """Queries gdc to get specific schema. Replace submitted_aligned_reads with any entity with any gdc entity"""

    response = requests.get(f'{endpoint}/template/submitted_aligned_reads?format=json')
    f = open('src/resources/sample_template.json', 'w')
    f.write(response.text)
    f.close()
