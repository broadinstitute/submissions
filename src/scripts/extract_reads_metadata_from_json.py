import json
import re
from google.cloud import storage

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


def get_json_contents(read_group_metadata_json):
    print("Reading JSON file from GCP bucket")

    path_parts = read_group_metadata_json.strip("/").split("/")
    bucket_name = path_parts[3]
    file_path = "/".join(path_parts[4:])
    print(f"Found bucket name: {bucket_name} and file path: {file_path} for JSON metadata file")

    if not bucket_name.startswith("fc-"):
        raise ValueError(f"Bucket name must start with 'fc-', instead got: '{bucket_name}'")

    client = storage.Client()
    blob = client.bucket(bucket_name).get_blob(file_path)
    if blob is None:
        raise FileNotFoundError(f"Blob not found: gs://{bucket_name}/{file_path}")

    content = blob.download_as_string()
    json_data = json.loads(content)
    print(f"Extracted JSON metadata:\n{json_data}")
    return json_data

def determine_target_capture_kit(data_type, submissions_metadata):
    kit_name = ""
    for s in submissions_metadata:
        if s["key"] == "target_capture_kit_name":
            kit_name = s["value"]

    if data_type == "Exome":
        return GDC_TWIST_CAPTURE_KIT if kit_name == MERCURY_TWIST_CAPTURE_KIT else GDC_NEXTERA_CAPTURE_KIT
    elif data_type == "Custom_Selection":
        return "Unknown"
    else:
        return "Not Applicable"

def extract_reads_data_from_workspace_metadata(sample_alias, billing_project, workspace_name, is_gdc):
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

def get_read_length_from_read_structure(read_structure):
    # Grab the first "section" before the T in the read structure. This can either be an integer, or a mix of
    # letters and integers if it's a UMI-aware read structure
    first_read = read_structure.split("T")[0]

    try:
        # If the read structure looks something like 76T8B8B76T, we get the read length by looking at the integer
        # before the first "T" - in this case "76" and we can automatically determine by trying to convert to an int
        int(first_read)
        return int(first_read)
    except ValueError:
        # If the read structure looks something like 3M2S71T8B8B3M2S71T, the read length is the sum of the numbers
        # before the first "T" - so 3 + 2 + 71 in this example, and we need to add them manually
        integers = re.findall(pattern=r"\d+", string=first_read)
        total = sum(int(num) for num in integers)
        return int(total)


def extract_molecular_barcode_name_and_sequence(molecular_indexing_scheme):
    molecular_indexing = json.loads(molecular_indexing_scheme)
    molecular_barcode_name = molecular_indexing["name"]
    molecular_barcode_sequence = f'{molecular_indexing["mapHintToSequence"]["P5"]}-{molecular_indexing["mapHintToSequence"]["P7"]}'
    return molecular_barcode_name, molecular_barcode_sequence


def determine_library_selection(product_type):
    if product_type == "Exome":
        return "HybridSelection"
    elif product_type == "RNA":
        return "ShortRangePCR"
    else:
        return "Random"

def extract_reads_data_from_json_gdc(sample_alias, read_group_metadata_json_path):
    """Grab the reads data for the given sample_id"""
    sample_metadata = get_json_contents(read_group_metadata_json_path)

    read_group_metadata = []
    for run in sample_metadata["runs"]:
        lanes = run["lanes"]

        for lane in lanes:
            libraries = lane["libraries"]
            for library in libraries:
                data_type_converted = DATA_TYPE_CONVERSION[library["dataType"]]
                agg_project = library["researchProjectId"]
                read_group_metadata.append(
                    {
                        "attributes": {
                            "aggregation_project": agg_project,
                            "sample_identifier": sample_alias,
                            "flow_cell_barcode": run["flowcellBarcode"],
                            "experiment_name": f"{sample_alias}.{data_type_converted}.{agg_project}",
                            "sequencing_center": BROAD_SEQUENCING_CENTER_ABBREVIATION,
                            "platform": ILLUMINA_PLATFORM,
                            "library_selection": determine_library_selection(library["productFamily"]),
                            "data_type": data_type_converted,
                            "library_name": library["library"],
                            "lane_number": int(lane["name"]),
                            "is_paired_end": run["pairedRun"],
                            "read_length": get_read_length_from_read_structure(run["setupReadStructure"]),
                            "target_capture_kit": determine_target_capture_kit(
                                data_type=library["dataType"], submissions_metadata=library["submissionMetadata"]
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
                    "machine_name": read_group["sequencerModel"],
                    "flowcell_barcode": read_group["flowcellBarcode"],
                }
            }
        )
    return read_group_metadata_json