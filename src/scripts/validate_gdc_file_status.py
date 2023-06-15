import argparse
import requests
import json

def check_file_status(sample_id, token, program, project):
    """Calls the GDC api to check the current status of the file transfer"""

    [agg_project, alias, _, data_type, _] = sample_id.split("_")
    submitter_id = f"{alias}.{data_type}.{agg_project}"
    print("Before call")
    response = get_entity(program, project, submitter_id, token)
    print("After call")

    if response['data'] and response['data']['submitted_aligned_reads'] and len(response['data']['submitted_aligned_reads']) > 0:
        # We have a valid response from gdc, so we write that value to file_state.txt so we can call the wdl to update the data table
        file_state = response['data']['submitted_aligned_reads'][0]['file_state']

        print(f"Current GDC file_state {file_state}")

        with open('/cromwell_root/file_state.txt', 'w') as fp:
            fp.write(file_state)
    else:
        print(f"We ran into an issue trying to query gdc - {response}")

def get_entity(program, project, submitter_id, token):
    """Constructs graphql query to hit the gdc api"""

    query = {
        "query": f"{{\n \n  submitted_aligned_reads (project_id: \"{program}-{project}\", submitter_id: \"{submitter_id}\") {{\n    id\n    submitter_id\n    state\n     file_state\n    error_type\n}}\n}}",
    }
    gdc_endpoint = 'https://api.gdc.cancer.gov/v0/submission'

    print("Inside of gdc call")

    gdc_response = requests.post(
        f"{gdc_endpoint}/graphql",
        json = query,
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": token
        }
    )

    return json.loads(gdc_response.text) 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--sample_id', required=True, help='list of aliases to check registration status')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    parser.add_argument('-d', '--delete', required=True, help='If this is true we will delete the bam from the workspace')
    args = parser.parse_args()

    print("Validation script is starting")

    check_file_status(args.sample_id, args.token, args.program, args.project)

    print("Script is finished")