import argparse

from src.services.gdc_api import GdcApiWrapper
from src.scripts.extract_reads_metadata_from_json import DATA_TYPE_CONVERSION


FILE_STATE_PATH = "/cromwell_root/file_state.txt"


def get_file_status(program, project, sample_alias, aggregation_project, data_type, token):
    """Calls the GDC API to check the current status of the file transfer."""
    submitter_id = f"{sample_alias}.{data_type}.{aggregation_project}"
    response = GdcApiWrapper(program=program, project=project, token=token).get_entity("submitted_aligned_reads", submitter_id)
    response_json = response.json()

    if "data" in response_json and response_json["data"].get("submitted_aligned_reads"):
        submitted_aligned_reads = response_json["data"]["submitted_aligned_reads"][0]
        return submitted_aligned_reads["state"], submitted_aligned_reads["file_state"]
    else:
        raise ValueError(f"We ran into an issue trying to query GDC - {response_json}")

def save_file_state(state_info):
    """Saves the file state information to a file."""
    with open(FILE_STATE_PATH, "w") as file_state_file:
        file_state_file.write(state_info)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Check the current status of file transfer using GDC API.")
    parser.add_argument("--program", required=True, help="GDC program")
    parser.add_argument("--project", required=True, help="GDC project")
    parser.add_argument("--sample_alias", required=True, help="Sample alias to use when querying GDC")
    parser.add_argument("--aggregation_project", required=True, help="Aggregation project to use when querying GDC")
    parser.add_argument("--data_type", required=True, help="Data type to use when querying GDC")
    parser.add_argument("--token", required=True, help="API token to communicate with GDC")
    args = parser.parse_args()

    data_type = ""
    if args.data_type in DATA_TYPE_CONVERSION.values():
        # If the provided data type is already an allowed GDC value, use it the way it was provided
        data_type = args.data_type
    else:
        try:
            # Otherwise, attempt to map it to an allowed data type
            data_type = DATA_TYPE_CONVERSION[args.data_type]
        except KeyError:
            print(
                f"Provided data type must either be one of the allowed GDC values: ({','.join(DATA_TYPE_CONVERSION.values())}) "
                f"OR it must be one of the data types we can map: ({','.join(DATA_TYPE_CONVERSION.keys())}). Instead received: '{args.data_type}'"
            )

    state, file_state = get_file_status(
        program=args.program,
        project=args.project,
        sample_alias=args.sample_alias,
        aggregation_project=args.aggregation_project,
        data_type=data_type,
        token=args.token
    )
    print(f"Successfully received file status from GDC. \nState - {state}. File_state - {file_state}")
    save_file_state(f"{file_state}\n{state}")