import argparse

from src.scripts.extract_reads_metadata_from_json import (
    extract_reads_data_from_json_dbgap,
    extract_reads_data_from_workspace_metadata
)
from src.services.terra import TerraAPIWrapper
from dbgap_classes import Sample, ReadGroup, Experiment, Run, Submission



def run_xml_creation(
        sample_id: str,
        billing_project: str,
        workspace_name: str,
        md5: str,
        reads_metadata: list[dict],
        aggregation_version: int,
        phs_id: str,
        data_type: str,
) -> None:

    terra_service = TerraAPIWrapper(billing_project, workspace_name)
    sample_json = terra_service.call_terra_api(sample_id, "sample")

    # If this is a dragen sample, some fields may be missing from the metadata, in which case we add them
    if not sample_json[0]["attributes"].get("aggregation_project"):
        sample_json[0]["attributes"]["aggregation_project"] = sample_json[0]["attributes"]["research_project"]
        sample_json[0]["attributes"]["location"] = "TDR"
        sample_json[0]["attributes"]["version"] = aggregation_version
        sample_json[0]["attributes"]["phs_id"] = phs_id
        sample_json[0]["attributes"]["data_type"] = data_type
        # TODO fix this once the metadata is updated
        sample_json[0]["attributes"]["aggregation_path"] = sample_json[0]["attributes"]["aggregation_path"]

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
    parser.add_argument("-w", "--workspace_name", required=True, help="Name of workspace")
    parser.add_argument("-b", "--billing_project", required=True, help="Billing project (namespace)")
    parser.add_argument("-s", "--sample_id", required=True, help="Sample ID to extract read data")
    parser.add_argument("-m", "--md5", required=True, help="MD5 value for the sample")
    parser.add_argument("-v", "--aggregation_version", required=True, help="The sample's aggregation version")
    parser.add_argument("-p", "--phs_id", required=True, help="The PHS ID")
    parser.add_argument("-d", "--data_type", required=True, help="The sample's data type")
    parser.add_argument(
        "-r",
        "--read_group_metadata_json",
        required=False,
        help="GCP path to the read group metadata JSON file"
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    if args.read_group_metadata_json:
        reads = extract_reads_data_from_json_dbgap(read_group_metadata_json_path=args.read_group_metadata_json)
    else:
        reads = extract_reads_data_from_workspace_metadata(
            sample_alias=args.sample_id, billing_project=args.billing_project, workspace_name=args.workspace_name, is_gdc=False,
        )

    run_xml_creation(
        sample_id=args.sample_id,
        billing_project=args.billing_project,
        workspace_name=args.workspace_name,
        md5=args.md5,
        reads_metadata=reads,
        aggregation_version=args.aggregation_version,
        phs_id=args.phs_id,
        data_type=args.data_type,
    )
