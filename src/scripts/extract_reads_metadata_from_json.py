import json
import re
from google.cloud import storage
from urllib.parse import urlparse

from src.services.terra import TerraAPIWrapper

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

def extract_reads_data_from_workspace_metadata(
        sample_alias: str, billing_project: str, workspace_name: str, is_gdc: bool,
) -> list[dict]:
    """Grab the reads data for the given sample_id"""
    reads_data = TerraAPIWrapper(billing_project, workspace_name).call_terra_api(sample_alias, "read-group")
    formatted_reads = [read["attributes"] for read in reads_data]

    if is_gdc:
        reads = reads_data
    else:
        reads = formatted_reads

    with open(READS_JSON_PATH, "w") as f:
        f.write(json.dumps(reads))

    return reads

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


def extract_reads_data_from_json_gdc(sample_alias: str, read_group_metadata_json_path: str) -> list[dict]:
    """Grab the reads data for the given sample_id"""
    sample_metadata = get_json_contents(read_group_metadata_json_path)
    data_type = DATA_TYPE_CONVERSION[sample_metadata["dataType"]]

    aggregation_project = sample_metadata["researchProjectId"]
    # TODO determine if any old samples with versions will be submitted at all and if this should be hard-coded or not
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

def extract_reads_data_from_json_dbgap(read_group_metadata_json_path: str):
    sample_metadata = get_json_contents(read_group_metadata_json_path)

    read_group_metadata_json = []
    # TODO find out what the key for the read groups actually is, this is a placeholder
    for read_group in sample_metadata["readGroups"]:
        read_group_metadata_json.append(
            {
                "attributes": {
                    "product_order_id": sample_metadata["productOrderKey"],
                    # TODO this will have to be changed to be grabbed from the read groups metadata
                    "library_name": read_group["library"],
                    "library_type": sample_metadata["analysisType"].split(".")[0],
                    "work_request_id": sample_metadata["productOrderKey"],
                    "analysis_type": sample_metadata["analysisType"].split(".")[1],
                    "paired_run": 0 if sample_metadata["paired_run"] == "false" else 1,
                    # TODO this is currently a field but not populated in the metadata JSON
                    "read_structure": sample_metadata["setupReadStructure"],
                    # TODO this is currently missing from the metadata JSON
                    "sample_lsid": sample_metadata["sampleLsid"],
                    "reference_sequence": sample_metadata["referenceSequence"],
                    "model": sample_metadata["sequencerModel"],
                    "research_project_id": sample_metadata["researchProjectId"],
                    "bait_set": sample_metadata.get("baitSetName", ""),
                    "sample_barcode": sample_metadata.get("sampleBarcode", ""),
                }
            }
        )
