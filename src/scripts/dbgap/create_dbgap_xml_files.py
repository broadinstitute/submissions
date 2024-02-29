import json
import os
import argparse
import pandas
import requests

from src.services.terra import TerraAPIWrapper
from dbgap_classes import Sample, ReadGroup, Experiment, Run, Submission

def run(sample_id, billing_project, workspace_name, md5):
    terra_service = TerraAPIWrapper(billing_project, workspace_name)
    sample_json = terra_service.call_terra_api(sample_id, "sample")
    readGroup_json = terra_service.call_terra_api(sample_id, "read-group")

    sample = Sample(sample_json, md5)
    read_group = ReadGroup(readGroup_json)

    experiment = Experiment(sample, read_group)
    experiment.create_file()

    run = Run(sample, read_group, experiment)
    run.create_file()

    submission = Submission(experiment, run, sample.phs)
    submission.create_file()

    print("Done creating xml files")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    parser.add_argument('-m', '--md5', required=True, help='md5 value for the sample')
    args = parser.parse_args()

    run(args.sample_id, args.project, args.workspace_name, args.md5)