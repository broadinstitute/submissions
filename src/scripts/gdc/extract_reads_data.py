import json
import argparse
import sys
import re

from google.cloud import storage
from urllib.parse import urlparse
sys.path.append("./")
from src.services.gdc_api import GdcApiWrapper
from src.services.terra import TerraAPIWrapper

# Constants
# TODO revert this
#READS_JSON_PATH = "/cromwell_root/reads.json"
READS_JSON_PATH = "reads.json"
BROAD_SEQUENCING_CENTER_ABBREVIATION = "BI"
DATA_TYPE_CONVERSION = {
    "Exome": "WXS",
    "WGS": "WGS",
    "RNA": "RNA"
}
GDC_TWIST_CAPTURE_KIT = "Custom Twist Broad Exome v1.0 - 35.0 Mb"
MERCURY_TWIST_CAPTURE_KIT = "Kit,xGen Hybridization + Wash(96Rxn/BX)"
GDC_NEXTERA_CAPTURE_KIT = "Nextera Rapid Capture Exome v1.2"


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

def get_json_contents(read_group_metadata_json: str) -> dict:
    client = storage.Client()
    parsed_url = urlparse(read_group_metadata_json)
    bucket_name = parsed_url.netloc
    file_path = parsed_url.path.lstrip("/")

    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    content = blob.download_as_string()
    json_data = json.loads(content)
    return json_data

def determine_target_capture_kit(data_type: str, kit_name: str) -> str:
    if data_type == "Exome":
        return GDC_TWIST_CAPTURE_KIT if kit_name == MERCURY_TWIST_CAPTURE_KIT else GDC_NEXTERA_CAPTURE_KIT
    elif data_type == "Custom_Selection":
        return "Unknown"
    else:
        return "Not Applicable"

def extract_reads_data_from_workspace_metadata(sample_alias: str, billing_project: str, workspace_name: str) -> list:
    """Grab the reads data for the given sample_id"""
    reads_data = TerraAPIWrapper(billing_project, workspace_name).call_terra_api(sample_alias, "read-group")
    formatted_reads = [read["attributes"] for read in reads_data]

    with open(READS_JSON_PATH, "w") as f:
        f.write(json.dumps(formatted_reads))

    return formatted_reads

def get_read_length_from_read_structure(read_structure: str) -> str:
    # Grab the first "section" before the T in the read structure. This can either be an integer, or a mix of
    # letters and integers if it's a UMI-aware read structure
    first_read = read_structure.split("T")[0]

    try:
        # If the read structure looks something like 76T8B8B76T, we get the read length by looking at the integer
        # before the first "T" - in this case "76" and we can automatically determine by trying to convert to an int
        int(first_read)
        return str(first_read)
    except ValueError:
        # If the read structure looks something like 3M2S71T8B8B3M2S71T, the read length is the sum of the numbers
        # before the first "T" - so 3 + 2 + 71 in this example, and we need to add them manually
        integers = re.findall(pattern=r"\d+", string=first_read)
        total = sum(int(num) for num in integers)
        return str(total)


def extract_reads_data_from_json(sample_alias, read_group_metadata_json_path):
    """Grab the reads data for the given sample_id"""
    sample_metadata = get_json_contents(read_group_metadata_json_path)
    data_type = DATA_TYPE_CONVERSION[sample_metadata["dataType"]]
    aggregation_project = sample_metadata["researchProjectId"]
    version = 1 # DRAGEN data doesn't have the concept of a version, so we hard-code it to 1

    read_group_metadata = []
    # TODO find out what the key for the read groups actually is, this is a placeholder
    for read_group in sample_metadata["readGroups"]:
        read_group_metadata.append(
            {
                "read_length": get_read_length_from_read_structure(read_structure=read_group["setupReadStructure"]),
                "flow_cell_barcode": sample_metadata["name"],
                "library_name": read_group["library"], # TODO fix this when they have the read group metadata populated
                "library_selection": sample_metadata["analysisType"].split(".")[0],
                "is_paired_end": sample_metadata["pairedRun"],
                "includes_spike_ins": False,
                "data_type": data_type,
                "sample_identifier": sample_alias,
                # TODO get reference sequence version from GP
                "reference_sequences_version": sample_metadata["referenceSequenceVersion"],
                "sequencing_center": BROAD_SEQUENCING_CENTER_ABBREVIATION,
                "library_preparation_kit_version": sample_metadata["library_preparation_kit_version"],
                "experiment_name": f"{sample_alias}.{data_type}.{aggregation_project}",
                "library_strand": "Not Applicable",
                "aggregation_project": aggregation_project,
                "sample_id": f"{aggregation_project}.{sample_alias}.{version}.WXS_GDC",
                "library_preparation_kit_name": sample_metadata["library_preparation_kit_name"],
                "reference_sequences": sample_metadata["referenceSequence"],
                "library_preparation_kit_vendor": sample_metadata["library_preparation_kit_vendor"],
                "platform": "Illumina",
                "lane_number": read_group["lane"], # TODO fix this once they have the read group metadata populated
                "library_preparation_kit_catalog_number": sample_metadata["library_preparation_kit_catalog_number"],
                "target_capture_kit": determine_target_capture_kit(
                    data_type, sample_metadata["library_preparation_kit_name"]
                ),
            }
        )

    with open(READS_JSON_PATH, "w") as f:
        f.write(json.dumps(read_group_metadata))

    return read_group_metadata


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
            read_group_metadata_json_path=args.read_group_metadata_json
        )
    else:
        reads = extract_reads_data_from_workspace_metadata(
            sample_alias=args.sample_id, billing_project=args.billing_project, workspace_name=args.workspace_name
        )
    # TODO uncomment this after testing
    #submit_reads(reads, args.token, args.project, args.program)
