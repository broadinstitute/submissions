import json
import os
import argparse
import pandas
import requests
from ftplib import FTP

from batch_upsert_entities import get_access_token
from dbgap_classes import Sample, ReadGroup, Experiment, Run, Submission

def run(sample_id, project, workspace_name, md5):
    sample_json = callTerraApi(sample_id, project, workspace_name, "sample")
    readGroup_json = callTerraApi(sample_id, project, workspace_name, "read-group")

    # sample_json = parse_terra_file(sample_file)
    # readGroup_json = parse_terra_file(read_file)

    sample = Sample(sample_json["results"], md5)
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
    print(f"baseurl {baseUrl}")
    parameters = {
        'page': "1", # Need to add in paging
        'pageSize': "1000",
        'filterTerms': sample_id
    }
    print(f"params {parameters}")
    headers = {"Authorization": "Bearer " + get_access_token(), "accept": "*/*", "Content-Type": "application/json"}

    response = requests.get(baseUrl, headers=headers, params=parameters)
    status_code = response.status_code

    print("response", response.text)

    return json.loads(response.text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    parser.add_argument('-m', '--md5', required=True, help='md5 value for the sample')
    # These will not be required once deployed
    # parser.add_argument('-sf', '--sample_file', required=True, help='.json file that contains all the data for the given sample')
    # parser.add_argument('-rf', '--read_file', required=True, help='.json file that contains all the data for the given sample')
    args = parser.parse_args()
    # not building
    # run(args.sample_id, args.project, args.workspace_name, args.md5, args.sample_file, args.read_file)
    run(args.sample_id, args.project, args.workspace_name, args.md5)