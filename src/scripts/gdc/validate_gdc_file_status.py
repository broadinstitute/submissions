import argparse
import json
from src.services.gdc_api import GdcApiWrapper

FILE_STATE_PATH = '/cromwell_root/file_state.txt'

def get_file_status(program, project, alias, aggregation_project, data_type, token):
    """Calls the GDC API to check the current status of the file transfer."""
    submitter_id = f"{alias}.{data_type}.{aggregation_project}"
    response = GdcApiWrapper(program=program, project=project, token=token).get_entity("submitted_aligned_reads", submitter_id)
    response_json = response.json()

    if 'data' in response_json and response_json['data'].get('submitted_aligned_reads'):
        submitted_aligned_reads = response_json['data']['submitted_aligned_reads'][0]
        return submitted_aligned_reads['state'], submitted_aligned_reads['file_state']
    else:
        raise ValueError(f"We ran into an issue trying to query GDC - {response_json}")

def save_file_state(state_info):
    """Saves the file state information to a file."""
    with open(FILE_STATE_PATH, 'w') as file_state_file:
        file_state_file.write(state_info)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check the current status of file transfer using GDC API.')
    parser.add_argument('-program', required=True, help='GDC program')
    parser.add_argument('-project', required=True, help='GDC project')
    parser.add_argument('-alias', required=True, help='Sample alias to use when querying GDC')
    parser.add_argument('-aggregation_project', required=True, help='Aggregation project to use when querying GDC')
    parser.add_argument('-data_type', required=True, help='Data type to use when querying GDC')
    parser.add_argument('-token', required=True, help='API token to communicate with GDC')
    args = parser.parse_args()

    state, file_state = get_file_status(args.program, args.project, args.alias, args.aggregation_project, args.data_type, args.token)
    save_file_state(f"{state}\n{file_state}")
    print("Successfully received file status from GDC.")