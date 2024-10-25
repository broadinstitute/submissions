import argparse
import sys
sys.path.append("./")

from src.scripts.extract_reads_metadata_from_json import extract_reads_data_from_json_dbgap, \
    extract_reads_data_from_workspace_metadata
from src.services.terra import TerraAPIWrapper
from dbgap_classes import Sample, ReadGroup, Experiment, Run, Submission



def run_xml_creation(
        sample_id: str, billing_project: str, workspace_name: str, md5: str, reads_metadata: list[dict]
) -> None:

    terra_service = TerraAPIWrapper(billing_project, workspace_name)
    # TODO: the sample_json may have to be manually updated to add any potential missing fields
    sample_json = terra_service.call_terra_api(sample_id, "sample")

    sample = Sample(sample_json, md5)
    read_group = ReadGroup(reads_metadata)

    experiment = Experiment(sample, read_group)
    experiment.create_file()

    run = Run(sample, read_group, experiment)
    run.create_file()

    submission = Submission(experiment, run, sample.phs)
    submission.create_file()

    print("Done creating xml files")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Create XML files for dbGaP submission")

    workspace_args = parser.add_argument_group("Workspace Args (used when there is no JSON file for reads metadata)")
    workspace_args.add_argument("-w", "--workspace_name", required=False, help="Name of workspace")
    workspace_args.add_argument("-p", "--project", required=False, help="Billing project (namespace)")

    json_group = parser.add_mutually_exclusive_group(required=False)
    json_group.add_argument(
        "-r",
        "--read_group_metadata_json",
        required=False,
        help="GCP path to the read group metadata JSON file"
    )

    parser.add_argument("-s", "--sample_id", required=True, help="Sample ID to extract read data")
    parser.add_argument("-m", "--md5", required=True, help="MD5 value for the sample")

    args = parser.parse_args()
    workspace_fields = [args.workspace_name, args.project]
    if args.read_group_metadata_json:
        if any(workspace_fields):
            parser.error(
                "Cannot provide BOTH read group metadata JSON and the combination of workspace/billing project"
            )
    else:
        if not all(workspace_fields):
            parser.error(
                "If not providing the read group metadata JSON, both workspace name and billing project must be "
                "provided"
            )

    return args


if __name__ == '__main__':
    args = parse_arguments()

    if args.read_group_metadata_json:
        reads = extract_reads_data_from_json_dbgap(read_group_metadata_json_path=args.read_group_metadata_json)
    else:
        reads = extract_reads_data_from_workspace_metadata(
            sample_alias=args.sample_id, billing_project=args.project, workspace_name=args.workspace_name, is_gdc=False,
        )

    run_xml_creation(
        sample_id=args.sample_id,
        billing_project=args.project,
        workspace_name=args.workspace_name,
        md5=args.md5,
        reads_metadata=reads
    )
