import argparse
import sys
from src.services.terra import TerraAPIWrapper
from dbgap_classes import Sample, ReadGroup, Experiment, Run, Submission


def run_xml_creation(sample_id, billing_project, workspace_name, md5):
    terra_service = TerraAPIWrapper(billing_project, workspace_name)
    sample_json = terra_service.call_terra_api(sample_id, "sample")
    read_group_json = terra_service.call_terra_api(sample_id, "read-group")

    sample = Sample(sample_json, md5)
    read_group = ReadGroup(read_group_json)

    experiment = Experiment(sample, read_group)
    experiment.create_file()

    run = Run(sample, read_group, experiment)
    run.create_file()

    submission = Submission(experiment, run, sample.phs)
    submission.create_file()

    print("Done creating xml files")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Create XML files for dbGaP submission')
    parser.add_argument('-w', '--workspace_name', required=True, help='Name of workspace')
    parser.add_argument('-p', '--project', required=True, help='Billing project (namespace)')
    parser.add_argument('-s', '--sample_id', required=True, help='Sample ID to extract read data')
    parser.add_argument('-m', '--md5', required=True, help='MD5 value for the sample')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    run_xml_creation(args.sample_id, args.project, args.workspace_name, args.md5)
