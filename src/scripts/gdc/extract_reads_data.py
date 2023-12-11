import json
import argparse
import pandas
import requests

from batch_upsert_entities import get_access_token

def extractReadsData(sample_id, project, workspace_name):
    """Grab the reads data for the given sample_id"""

    readsData = callTerraApi(sample_id, project, workspace_name)
    formattedReads = formatReads(readsData)

    f = open("/cromwell_root/reads.json", 'w')
    f.write(json.dumps(formattedReads))
    f.close()

    print("Done writing read json to file")

    return formattedReads

def parse_terra_file(file):
    """Reads the dummy json file"""

    with open(file, 'r') as my_file:
        return json.load(my_file) # TODO - Need to be more defensive here

    print("Error when trying to parse the input file")

def formatReads(readsData):
    """Normalize data returned from Terra API"""

    readsArray = []

    if readsData['results']:
        readsArray = [read['attributes'] for read in readsData['results']]
    else:
        print("No result fields in response")

    return readsArray

def callTerraApi(sample_id, project, workspace_name):
    """Call the Terra api to retrieve reads data"""

    baseUrl = f"https://rawls.dsde-prod.broadinstitute.org/api/workspaces/{project}/{workspace_name}/entityQuery/read-group"
    parameters = {
        'page': "1", # Need to add in paging
        'pageSize': "1000",
        'filterTerms': sample_id
    }
    headers = {"Authorization": "Bearer " + get_access_token(), "accept": "*/*", "Content-Type": "application/json"}

    response = requests.get(baseUrl, headers=headers, params=parameters)
    status_code = response.status_code

    print("respose", response.text)

    return json.loads(response.text)

def getHeaders(token):
    """Returns general headers for gdc api call"""

    return {
        "Content-Type": "application/json",
        "X-Auth-Token": token
    }

def linkAliqout(linkData, token, program, project):
    """Helper function to create entities inside of gdc"""

    endpoint = 'https://api.gdc.cancer.gov/v0/submission'
    url = f"{endpoint}/{program}/{project}"

    response = requests.put(url,
        data = json.dumps(linkData),
        headers = getHeaders(token)
    )

    print("response for creating links", response.text)

def createSubmittableReadGroups(reads):
    """Creates an array of readGroups"""

    def formatReadGroup(read):
        submitterIdConstant = f"{read['aggregation_project']}.{read['sample_identifier']}"
        formattedRead = {
            "type": "read_group",
            "aliquots": {
                "submitter_id": read['sample_identifier']
            },
            "submitter_id": f"{read['flow_cell_barcode']}.{read['lane_number']}.{submitterIdConstant}",
            "experiment_name": read['experiment_name'],
            "sequencing_center": read['sequencing_center'],
            "platform": read['platform'],
            "library_selection": read['library_selection'],
            "library_strategy": read['data_type'],
            "library_name": read['library_name'],
            "lane_number": read['lane_number'],
            "is_paired_end": read['is_paired_end'],
            "read_length": read['read_length'],
            "read_group_name": f"{read['flow_cell_barcode'][:5]}.{read['lane_number']}",
            "target_capture_kit": read['target_capture_kit'],
            "to_trim_adapter_sequence": True,
            "platform": "Illumina"
        }
        library_strand_dict = {
            key: value
            for key, value in read.items()
            if "library_selection" in key and value is not None and value != ""
        }


        return {**formattedRead, **library_strand_dict}

    return [formatReadGroup(read) for read in reads]

def submitReads(reads, token, project, program):
    formattedReads = createSubmittableReadGroups(reads)

    print(formattedReads)

    linkAliqout(formattedReads, token, program, project)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--billing_project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    args = parser.parse_args()

    reads = extractReadsData(args.sample_id, args.billing_project, args.workspace_name)
    submitReads(reads, args.token, args.project, args.program)