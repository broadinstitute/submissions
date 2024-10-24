import json
import argparse
import sys
from random import sample

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

def get_json_contents(read_group_metadata_json):
    client = storage.Client()
    parsed_url = urlparse(read_group_metadata_json)
    bucket_name = parsed_url.netloc
    file_path = parsed_url.path.lstrip("/")

    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    content = blob.download_as_string()
    json_data = json.loads(content)
    return json_data

def determine_target_capture_kit(data_type, kit_name):
    if data_type == "Exome":
        return GDC_TWIST_CAPTURE_KIT if kit_name == MERCURY_TWIST_CAPTURE_KIT else GDC_NEXTERA_CAPTURE_KIT
    elif data_type == "Custom_Selection":
        return "Unknown"
    else:
        return "Not Applicable"

def extract_reads_data(sample_id, read_group_metadata_json):
    """Grab the reads data for the given sample_id"""
    json_data = get_json_contents(read_group_metadata_json)
    sample_metadata = [r for r in json_data if r["collaboratorSampleId"] == sample_id][0]
    data_type = DATA_TYPE_CONVERSION[sample_metadata["dataType"]]
    aggregation_project = sample_metadata["researchProjectId"]
    # Dragen data doesn't have the concept of a version, so we hard-code it to 1
    version = 1

    read_group_metadata = []
    # TODO find out what the key for the read groups actually is, this is a placeholder
    for read_group in sample_metadata["readGroups"]:
        read_group_metadata.append(
            {
                # TODO add read length/read structure logic in here
                "read_length": read_group["readLength"],
                "flow_cell_barcode": sample_metadata["name"],
                "library_name": read_group["library"], # TODO fix this when they have the read group metadata populated
                "library_selection": sample_metadata["analysisType"].split(".")[0],
                "is_paired_end": sample_metadata["pairedRun"],
                "includes_spike_ins": False,
                "to_trim_adapter_sequence": True,
                "data_type": data_type,
                "sample_identifier": sample_id,
                # TODO get reference sequence version from GP
                "reference_sequences_version": sample_metadata["referenceSequenceVersion"],
                "sequencing_center": BROAD_SEQUENCING_CENTER_ABBREVIATION,
                "library_preparation_kit_version": sample_metadata["library_preparation_kit_version"],
                "experiment_name": f"{sample_id}.{data_type}.{aggregation_project}",
                "library_strand": "Not Applicable",
                "aggregation_project": aggregation_project,
                "sample_id": f"{aggregation_project}.{sample_id}.{version}.WXS_GDC",
                "library_preparation_kit_name": sample_metadata["library_preparation_kit_name"],
                "reference_sequences": sample_metadata["referenceSequence"],
                "library_preparation_kit_vendor": sample_metadata["library_preparation_kit_vendor"],
                "platform": "Illumina",
                "lane_number": read_group["lane"], # TODO fix this once they have the readgroup metadata popualted
                "library_preparation_kit_catalog_number": sample_metadata["library_preparation_kit_catalog_number"],
                "target_capture_kit": determine_target_capture_kit(
                    data_type, sample_metadata["library_preparation_kit_name"]
                ),
            }
        )

    #with open(READS_JSON_PATH, 'w') as f:
    #    f.write(json.dumps(read_group_metadata))

    #return formatted_reads


def format_read_group(read):
    submitter_id_constant = f"{read['aggregation_project']}.{read['sample_identifier']}"
    formatted_read = {
        "type": "read_group",
        "aliquots": {
            "submitter_id": read['sample_identifier']
        },
        "submitter_id": f"{read['flow_cell_barcode']}.{read['lane_number']}.{submitter_id_constant}",
        "experiment_name": read['experiment_name'],
        "sequencing_center": read['sequencing_center'],
        "platform": read['platform'],
        "library_selection": "Hybrid Selection" if read['library_selection'] == "HybridSelection" else read['library_selection'],
        "library_strategy": read['data_type'],
        "library_name": read['library_name'],
        "lane_number": read['lane_number'],
        "is_paired_end": read['is_paired_end'],
        "read_length": read['read_length'],
        "read_group_name": f"{read['flow_cell_barcode'][:5]}.{read['lane_number']}",
        "target_capture_kit": read['target_capture_kit'],
        "to_trim_adapter_sequence": True,
    }
    library_strand_dict = {key: value for key, value in read.items()
                            if "library_preperation" in key and value is not None and value != ""}

    return {**formatted_read, **library_strand_dict}


def submit_reads(reads, token, project, program):
    formatted_reads = [format_read_group(read) for read in reads]
    print(formatted_reads)
    GdcApiWrapper(program=program, project=project, token=token).submit_metadata(formatted_reads)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract and submit reads data.')
    parser.add_argument(
        '-w',
        '--workspace_name',
        required=True,
        help='The name of the workspace in which to make changes'
    )
    parser.add_argument(
        '-p',
        '--billing_project',
        required=True,
        help='The billing project (namespace) of the workspace in which to make changes'
    )
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    #parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    #parser.add_argument('-pj', '--project', required=True, help='GDC project')
    #parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument(
        "-r",
        "--read_group_metadata_json",
        required=True,
        help="GCP path to the read group metadata JSON"
    )
    args = parser.parse_args()

    reads = extract_reads_data(args.sample_id, args.read_group_metadata_json)
    #submit_reads(reads, args.token, args.project, args.program)
