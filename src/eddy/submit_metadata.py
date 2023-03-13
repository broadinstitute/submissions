import requests
import json

# Need to figure out a better way to handle the env variables
endpoint = 'https://api.gdc.cancer.gov/v0/submission'

def submit(input):
    """Submits the formatted metadata to gdc api"""

    url = f"{endpoint}/{input['program']}/{input['project']}"
    gdcFormattedMetadata = createMetadata(input)

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

def createMetadata(inputData):
    """Uses the input to format metadata to be submitted to gdc"""

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
        "file_size": int(inputData['file_size']),
        "data_type": "Aligned Reads",
        "experimental_strategy": dataTypeToExperimentalStrategy[inputData['data_type']],
        "data_format": "BAM",
        "project_id": f"{inputData['program']}-{inputData['project']}",
        "md5sum": inputData['md5'],
        "proc_internal": "dna-seq skip",
        "read_groups": getSubmitterIdForReadGroups(inputData)
    }

    print("metadata", metadata)
    # Need to write bam name and bam file to a file so we can access it in the wdl. Talk to Sushma!
    writeBamDataToFile(inputData)

    return metadata

def writeBamDataToFile(data):
    """Extracts bam path and bam name and writes to a file named bam.txt"""

    bamFileName = data['agg_path'].split('/')[-1]
    f = open("/cromwell_root/bam.txt", 'w')
    f.write(f"{data['agg_path']}\n{bamFileName}")
    f.close()

def getSubmitterIdForReadGroups(data):
    """Extracts all submitterIds for each read_group inside of sample_metadata"""

    submitterIds = []
    submitterIdConstant = f"{data['agg_project']}.{data['alias_value']}"
    read_groups = getReadGroups(data['read_groups'])

    for readGroup in read_groups:
        submitterIds.append({
            "submitter_id": f"{readGroup['flow_cell_barcode']}.{readGroup['lane_number']}.{submitterIdConstant}"
        })

    return submitterIds

def getReadGroups(read_file):
    """Opens reads file"""

    with open(read_file, 'r') as my_file:
        return json.loads(json.load(my_file))

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

    print(f"Query to gdc {query}")
    return requests.post(
        f"{endpoint}/graphql",
        json = query,
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": token
        }
    )
 
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
