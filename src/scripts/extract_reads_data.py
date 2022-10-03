import json
import argparse
import pandas
import requests

from batch_upsert_entities import get_access_token

def extractReadsData(sample_id, project, workspace_name):
    """Grab the reads data for the given sample_id"""

    readsData = callTerraApi(sample_id, project, workspace_name)
    # readsData = returnTestObj()
    formattedReads = formatReads(readsData)

    f = open("/cromwell_root/reads.json", 'w')
    f.write(json.dumps(formattedReads))
    f.close()

    print("Done writing read json to file") 

def formatReads(readsData):
    """Normalize data returned from Terra API"""

    readsArray = []

    if readsData['results']:
        for read in readsData['results']:
            if read['attributes']:
                readsArray.append(read['attributes'])
            else:
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

    print("respose", response.text)

    return json.loads(response.text)

def returnTestObj():
    return {
        "results": [
            {
                "attributes": {
                    "read_length": 151,
                    "library_strand": "Not Applicable",
                    "library_preparation_kit_name": "KAPA HyperPrep Kit (no amp)",
                    "flow_cell_barcode": "HMH72DSX3",
                    "library_name": "0415052444_Illumina_P5-Fezex_P7-Halex",
                    "library_selection": "Random",
                    "is_paired_end": True,
                    "includes_spike_ins": False,
                    "library_strategy": "WGS",
                    "library_preparation_kit_vendor": "Kapa BioSystems",
                    "type": "read_group",
                    "sequencing_center": "BI",
                    "library_preparation_kit_version": "v1.1",
                    "experiment_name": "CTSP-B6F9-TTP1-A-1-0-D-A92B-36.WGS.RP-1329",
                    "to_trim_adapter_sequence": True,
                    "instrument_model": "Other",
                    "sample_identifier": "CTSP-B6F9-TTP1-A-1-0-D-A92B-36.WGS.RP-1329",
                    "multiplex_barcode": "ATCTTCTC+CAACTCTC",
                    "platform": "Illumina",
                    "lane_number": 1,
                    "reference_sequence": "Homo_sapiens_assembly38",
                    "library_preparation_kit_catalog_number": "KK8505",
                    "target_capture_kit": "Not Applicable",
                    "sequencing_date": "2022-07-13T11:06:01",
                    "reference_sequence_version": 0,
                    "read_group_name": "HMH72.1"
                },
                "entityType": "read_group",
                "name": "HMH72DSX3.1.RP-1329.CTSP-B6F9-TTP1-A-1-0-D-A92B-36"
            }
        ]
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    args = parser.parse_args()

    extractReadsData(args.sample_id, args.project, args.workspace_name)