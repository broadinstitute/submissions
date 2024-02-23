import json
import argparse
from src.services.gdc_api import GdcApiWrapper
from src.services.terra import TerraAPIWrapper

# Constants
READS_JSON_PATH = "/cromwell_root/reads.json"

def extract_reads_data(sample_id, billing_project, workspace_name):
    """Grab the reads data for the given sample_id"""
    reads_data = TerraAPIWrapper(billing_project, workspace_name).call_terra_api(sample_id, "read-group")
    formatted_reads = [read['attributes'] for read in reads_data]

    with open(READS_JSON_PATH, 'w') as f:
        f.write(json.dumps(formatted_reads))

    return formatted_reads

def format_read_group(read):
    if read['library_selection'] == "HybridSelection":
        print("HybridSelection")
        library_selection = "Hybrid Selection"
    else:
        print("other")
        library_selection = read['library_selection']

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
        "library_selection": library_selection,
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
    print("formatted reads", formatted_read)
    print("library dict", library_strand_dict)
    return {**formatted_read, **library_strand_dict}

def submit_reads(reads, token, project, program):
    formatted_reads = [format_read_group(read) for read in reads]
    print(formatted_reads)
    GdcApiWrapper(program=program, project=project, token=token).submit_metadata(formatted_reads)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract and submit reads data.')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--billing_project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-s', '--sample_id', required=True, help='sample_id to extract read data')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    args = parser.parse_args()

    reads = extract_reads_data(args.sample_id, args.billing_project, args.workspace_name)
    submit_reads(reads, args.token, args.project, args.program)
