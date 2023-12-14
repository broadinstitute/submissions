import argparse
import json
import logging
from src.services.gdc_api import GdcApiWrapper

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)

def check_file_status(sample_id, token, program, project):
    """Calls the GDC API to check the current status of the file transfer."""

    try:
        [agg_project, alias, _, data_type, _] = sample_id.split("_")
        submitter_id = f"{alias}.{data_type}.{agg_project}"
        response = GdcApiWrapper(program=program, project=project, token=token).get_entity("submitted_aligned_reads", submitter_id)
        response_json = response.json()

        if response_json.get('data') and response_json['data'].get('submitted_aligned_reads') and len(response_json['data']['submitted_aligned_reads']) > 0:
            submitted_aligned_reads = response_json['data']['submitted_aligned_reads'][0]
            
            with open('/cromwell_root/file_state.txt', 'w') as file_state_file:
                file_state_file.write(f"{submitted_aligned_reads['state']}\n{submitted_aligned_reads['file_state']}")
            logging.info("Successfully recieved file status from gdc")
        else:
            logging.error(f"We ran into an issue trying to query GDC - {response_json}")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check the current status of file transfer using GDC API.')
    parser.add_argument('-s', '--sample_id', required=True, help='List of aliases to check registration status')
    parser.add_argument('-t', '--token', required=True, help='API token to communicate with GDC')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    args = parser.parse_args()

    check_file_status(args.sample_id, args.token, args.program, args.project)