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
    f.write(formattedReads)
    f.close()
    print("Done writing read json to file") 

def formatReads(readsData):
    """Normalize data returned from Terra API"""

    readsArray = []

    if readsData['result']:
        for read in readsData.result:
            if read['attributes']:
                readsArray.append(read['attributes'])
            else
                print("Reads data is not correct", read)
    else:
        print("No result fields in response")

    return readsArray

def callTerraApi(sample_id, project, workspace_name):
    """Call the Terra api to retrieve reads data"""

    baseUrl = f"https://rawls.dsde-prod.broadinstitute.org/api/workspaces/{project}/{workspace_name}/entityQuery/read_group"
    parameters = {
        'page': "1", # Need to add in paging
        'pageSize': "50",
        'filterTerms': sample_id
    }
    headers = {"Authorization": "Bearer " + get_access_token(), "accept": "*/*", "Content-Type": "application/json"}

    response = requests.get(baseUrl, headers=headers, params=parameters)
    status_code = response.status_code

    if status_code != 204:
        print(f"WARNING: Failed to retrieve entities.")
        print(response.text)
        return

    print("respose", response)

    return response

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    args = parser.parse_args()

    extractReadsData(args.sample_id, args.project, args.workspace_name)