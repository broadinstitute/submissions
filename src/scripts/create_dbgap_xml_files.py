import json
import argparse
import pandas
import requests
from ftplib import FTP

from batch_upsert_entities import get_access_token
from dbgap_classes import Sample, ReadGroup, Experiment, Run, Submission

def run(sample_id, project, workspace_name, sample_file, read_file):
    # sample = callTerraApi(sample_id, project, workspace_name, "sample")
    # readGroups = callTerraApi(sample_id, project, workspace_name, "read_group")

    sample_json = parse_terra_file(sample_file)
    readGroup_json = parse_terra_file(read_file)

    sample = Sample(sample_json["results"])
    read_group = ReadGroup(readGroup_json["results"])

    experiment = Experiment(sample, read_group)
    experiment.create_file()

    run = Run(sample, read_group, experiment)
    run.create_file()

    submission = Submission(experiment, run, sample.phs)
    submission.create_file()

    print("Done creating xml files")

def parse_terra_file(file):
    """Reads the dummy json file"""

    with open(file, 'r') as my_file:
        return json.load(my_file) # TODO - Need to be more defensive here

    print("Error when trying to parse the input file")

def callTerraApi(sample_id, project, workspace_name, table):
    """Call the Terra api to retrieve reads data"""

    baseUrl = f"https://rawls.dsde-prod.broadinstitute.org/api/workspaces/{project}/{workspace_name}/entityQuery/{table}"
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    # These will not be required once deployed
    parser.add_argument('-sf', '--sample_file', required=True, help='.json file that contains all the data for the given sample')
    parser.add_argument('-rf', '--read_file', required=True, help='.json file that contains all the data for the given sample')
    args = parser.parse_args()

    run(args.sample_id, args.project, args.workspace_name, args.sample_file, args.read_file)