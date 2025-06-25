import argparse
import logging

from src.scripts.extract_reads_metadata_from_json import (
    extract_reads_data_from_json_gdc,
    extract_reads_data_from_workspace_metadata,
    DATA_TYPE_CONVERSION
)
from src.services.gdc_api import GdcApiWrapper


logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)


def get_args():
    parser = argparse.ArgumentParser(description="Extract and submit reads data.")
    parser.add_argument(
        "-w",
        "--workspace_name",
        required=True,
        help="The name of the workspace in which to make changes"
    )
    parser.add_argument(
        "-b",
        "--billing_project",
        required=True,
        help="The billing project of the workspace in which to make changes"
    )
    parser.add_argument("-s", "--sample_alias", required=True, help="The sample alias")
    parser.add_argument("-t", "--token", required=True, help="The API token to communicate with GDC")
    parser.add_argument("-pj", "--project", required=True, help="GDC project")
    parser.add_argument("-pg", "--program", required=True, help="GDC program")
    parser.add_argument(
        "-r",
        "--read_group_metadata_json",
        required=False,
        help="GCP path to the read group metadata JSON file"
    )
    return parser.parse_args()


def format_read_group(read):
    submitter_id_constant = f"{read['aggregation_project']}.{read['sample_identifier']}"

    data_type = ""
    if read["data_type"] in DATA_TYPE_CONVERSION.values():
        # If the provided data type is already an allowed GDC value, use it the way it was provided
        data_type = read["data_type"]
    else:
        try:
            # Otherwise, attempt to map it to an allowed data type
            data_type = DATA_TYPE_CONVERSION[read["data_type"]]
        except KeyError:
            logging.error(
                f"Provided data type must either be one of the allowed GDC values: ({','.join(DATA_TYPE_CONVERSION.values())}) "
                f"OR it must be one of the data types we can map: ({','.join(DATA_TYPE_CONVERSION.keys())}). Instead received: '{read['data_type']}'"
            )

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
        "library_strategy": data_type,
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
    formatted_reads = [format_read_group(read["attributes"]) for read in read_metadata]
    operation = GdcApiWrapper(
        program=program,
        project=project,
        token=token
    ).submit_metadata(formatted_reads)

    if operation == "close":
        raise Exception(f"Failed to submit reads, operation: {operation}")
    if operation == "commit":
        logging.info(f"Successfully submitted reads, operation: {operation}")


if __name__ == "__main__":
    args = get_args()
    if args.read_group_metadata_json:
        reads = extract_reads_data_from_json_gdc(
            sample_alias=args.sample_alias,
            read_group_metadata_json_path=args.read_group_metadata_json,
        )
    else:
        reads = extract_reads_data_from_workspace_metadata(
            sample_alias=args.sample_alias,
            billing_project=args.billing_project,
            workspace_name=args.workspace_name,
            is_gdc=True,
        )

    submit_reads(reads, args.token, args.project, args.program)
