import json
import re
from google.cloud import storage
from urllib.parse import urlparse

from src.services.terra import TerraAPIWrapper

READS_JSON_PATH = "/cromwell_root/reads.json"
BROAD_SEQUENCING_CENTER_ABBREVIATION = "BI"
DATA_TYPE_CONVERSION = {
    "Exome": "WXS",
    "WGS": "WGS",
    "RNA": "RNA"
}
GDC_TWIST_CAPTURE_KIT = "Custom Twist Broad Exome v1.0 - 35.0 Mb"
MERCURY_TWIST_CAPTURE_KIT = "Kit,xGen Hybridization + Wash(96Rxn/BX)"
GDC_NEXTERA_CAPTURE_KIT = "Nextera Rapid Capture Exome v1.2"
ILLUMINA_PLATFORM = "Illumina"


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


def determine_target_capture_kit(data_type: str, submissions_metadata: str) -> str:
    submissions_info = json.loads(submissions_metadata)
    kit_name = ""
    for s in submissions_info:
        if s["key"] == "target_capture_kit_name":
            kit_name = s["value"]

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

# TODO find out if this is the right way to extract the molecular barcode sequence
def extract_molecular_barcode_name_and_sequence(molecular_indexing_scheme: str):
    molecular_indexing = json.loads(molecular_indexing_scheme)
    molecular_barcode_name = molecular_indexing["name"]
    molecular_barcode_sequence = molecular_indexing["mapHintToAnalysisSequence"]["P5"]
    return molecular_barcode_name, molecular_barcode_sequence


def determine_library_selection(product_type):
    # TODO determine what the types of products are here (for Exome, WGS and RNA)
    if product_type == "HybridSelection":
        return "HybridSelection"
    elif product_type == "ShortRangePCR":
        return "ShortRangePCR"
    else:
        return "Random"

def extract_reads_data_from_json_gdc(sample_alias: str, read_group_metadata_json_path: str) -> list[dict]:
    """Grab the reads data for the given sample_id"""
    sample_metadata = get_json_contents(read_group_metadata_json_path)

    read_group_metadata = []
    for read_group in sample_metadata["readGroups"]:
        data_type = DATA_TYPE_CONVERSION[read_group["dataType"]]
        aggregation_project = read_group["researchProjectId"]
        read_group_metadata.append(
            {
                "attributes": {
                    "aggregation_project": aggregation_project,
                    "sample_identifier": sample_alias,
                    "flow_cell_barcode": read_group["flowcellBarcode"],
                    "experiment_name": f"{sample_alias}.{data_type}.{aggregation_project}",
                    "sequencing_center": BROAD_SEQUENCING_CENTER_ABBREVIATION,
                    "platform": ILLUMINA_PLATFORM,
                    "library_selection": determine_library_selection(read_group["productFamily"]),
                    "data_type": data_type,
                    "library_name": read_group["library"],
                    "lane_number": read_group["lane"],
                    "is_paired_end": read_group["pairedRun"],
                    "read_length": get_read_length_from_read_structure(read_group["setupReadStructure"]),
                    "target_capture_kit": determine_target_capture_kit(
                        data_type=read_group["dataType"], submissions_metadata=read_group["submissionsMetadata"]
                    ),

                }
            }
        )

    with open(READS_JSON_PATH, "w") as f:
        f.write(json.dumps(read_group_metadata))

    return read_group_metadata

def extract_reads_data_from_json_dbgap(read_group_metadata_json_path: str):
    sample_metadata = get_json_contents(read_group_metadata_json_path)

    read_group_metadata_json = []
    for read_group in sample_metadata["readGroups"]:

        molecular_barcode_name, molecular_barcode_sequence = extract_molecular_barcode_name_and_sequence(
            read_group["molecularIndexingScheme"]
        )

        read_group_metadata_json.append(
            {
                "attributes": {
                    "product_order_id": read_group["productOrderKey"],
                    "library_name": read_group["library"],
                    "library_type": read_group["analysisType"].split(".")[0],
                    "work_request_id": read_group["productOrderKey"],
                    "analysis_type": read_group["analysisType"].split(".")[1],
                    "paired_run": 0 if read_group["pairedRun"] == "false" else 1,
                    "read_structure": read_group["setupReadStructure"],
                    "sample_lsid": read_group["lsid"],
                    "reference_sequence": read_group["referenceSequence"],
                    "model": read_group["sequencerModel"],
                    "research_project_id": read_group["researchProjectId"],
                    "bait_set": read_group.get("baitSetName", ""),
                    "sample_barcode": read_group.get("sampleBarcode", ""),
                    "run_barcode": read_group["barcode"],
                    "lane": read_group["lane"],
                    "run_name": read_group["name"],
                    "molecular_barcode_name": molecular_barcode_name,
                    "molecular_barcode_sequence": molecular_barcode_sequence,
                    # TODO figure out if this is the correct mapping of machine
                    "machine_name": read_group["dragenPipeline"],
                    "flowcell_barcode": read_group["flowcellBarcode"],
                }
            }
        )
    return read_group_metadata_json