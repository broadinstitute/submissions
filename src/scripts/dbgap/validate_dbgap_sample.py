import argparse
from src.services.dbgap_telemetry_report import DbgapTelemetryWrapper

SAMPLE_STATUS_FILE_PATH = '/cromwell_root/sample_status.tsv'

def save_sample_status(sample_id, state_info):
    """Saves the file state information to a file."""
    with open(SAMPLE_STATUS_FILE_PATH, 'w') as file:
        # Write header
        file.write("entity:sample_id\tsample_status\n")
        # Write data
        file.write(f"{sample_id}\t{sample_status}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check the current status of sample in Dbgap by parsing the Telemetry report.')
    parser.add_argument('-sample_alias', required=True, help='Sample alias to use when querying DbGap')
    parser.add_argument('-sample_id', required=True, help='Sample id to allow us to write back to the data table')
    parser.add_argument('-phs_id', required=True, help='phs_id sample is linked to')
    parser.add_argument('-data_type', required=True, help='Data type to use when querying DbGap')
    args = parser.parse_args()

    sample_status = DbgapTelemetryWrapper(phs_id=args.phs_id).get_sample_status(args.sample_alias, args.data_type)
    save_sample_status(args.sample_id, sample_status)
    print(f"Script finished with sample status of - {sample_status}")
