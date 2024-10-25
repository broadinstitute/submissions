import json
import argparse
import sys

from src.scripts.extract_reads_metadata_from_json import (
    extract_reads_data_from_json,
    extract_reads_data_from_workspace_metadata,
)

sys.path.append("./")

from src.services.gdc_api import GdcApiWrapper


def get_args():
    parser = argparse.ArgumentParser(description="Extract and submit reads data.")
    workspace_args = parser.add_argument_group("Workspace Args (used when there is no JSON file for reads metadata)")
    workspace_args.add_argument(
        "-w",
        "--workspace_name",
        required=False,
        help="The name of the workspace in which to make changes"
    )
    workspace_args.add_argument(
        "-p",
        "--billing_project",
        required=False,
        help="The billing project (namespace) of the workspace in which to make changes"
    )
    json_group = parser.add_mutually_exclusive_group(required=False)
    json_group.add_argument(
        "-r",
        "--read_group_metadata_json",
        required=False,
        help="GCP path to the read group metadata JSON file"
    )

    parser.add_argument("-s", "--sample_id", required=True, help="The sample alias")
    parser.add_argument("-t", "--token", required=True, help="The API token to communicate with GDC")
    parser.add_argument("-pj", "--project", required=True, help="GDC project")
    parser.add_argument("-pg", "--program", required=True, help="GDC program")

    args = parser.parse_args()

    workspace_fields = [args.workspace_name, args.billing_project]
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


def format_read_group(read):
    submitter_id_constant = f"{read['aggregation_project']}.{read['sample_identifier']}"
    formatted_read = {
        "type": "read_group",
        "aliquots": {
            "submitter_id": read["sample_identifier"]
        },
        "submitter_id": f"{read['flow_cell_barcode']}.{read['lane_number']}.{submitter_id_constant}",
        "experiment_name": read["experiment_name"],
        "sequencing_center": read["sequencing_center"],
        "platform": read["platform"],
        "library_selection": "Hybrid Selection" if read["library_selection"] == "HybridSelection" else read["library_selection"],
        "library_strategy": read["data_type"],
        "library_name": read["library_name"],
        "lane_number": read["lane_number"],
        "is_paired_end": read["is_paired_end"],
        "read_length": read["read_length"],
        "read_group_name": f"{read['flow_cell_barcode'][:5]}.{read['lane_number']}",
        "target_capture_kit": read["target_capture_kit"],
        "to_trim_adapter_sequence": True,
    }
    library_strand_dict = {
        key: value for key, value in read.items() if "library_preparation" in key and value is not None and value != ""
    }

    return {**formatted_read, **library_strand_dict}


def submit_reads(read_metadata, token, project, program):
    formatted_reads = [format_read_group(read) for read in read_metadata]
    GdcApiWrapper(program=program, project=project, token=token).submit_metadata(formatted_reads)


if __name__ == "__main__":
    args = get_args()
    if args.read_group_metadata_json:
        reads = extract_reads_data_from_json(
            sample_alias=args.sample_id,
            read_group_metadata_json_path=args.read_group_metadata_json,
            is_gdc=True,
        )
    else:
        reads = extract_reads_data_from_workspace_metadata(
            sample_alias=args.sample_id, billing_project=args.billing_project, workspace_name=args.workspace_name
        )
    # TODO uncomment this after testing
    #submit_reads(reads, args.token, args.project, args.program)
