import argparse
import json
import requests
import xmltodict
import xml.etree.ElementTree as ET
# from src.services.dbgap_telemetry_report import DbgapTelemetryWrapper

FILE_STATE_PATH = '/cromwell_root/sample_status.txt'

def save_file_state(state_info):
    """Saves the file state information to a file."""
    with open(FILE_STATE_PATH, 'w') as file_state_file:
        file_state_file.write(state_info)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check the current status of sample in Dbgap by parsing the Telemetry report.')
    parser.add_argument('-sample_alias', required=True, help='Sample alias to use when querying DbGap')
    parser.add_argument('-phs_id', required=True, help='phs_id sample is linked to')
    parser.add_argument('-data_type', required=True, help='Data type to use when querying DbGap')
    args = parser.parse_args()

    sample_status = DbgapTelemetryWrapper(phs_id=args.phs_id).get_sample_status(args.sample_alias, args.data_type)
    save_file_state(f"{sample_status}")