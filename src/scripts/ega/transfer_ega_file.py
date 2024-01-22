import os
import sys
import logging
import argparse
import paramiko
import subprocess
sys.path.append("./")
from src.scripts.ega.utils import (
    LoginAndGetToken,
    SecretManager,
    format_request_header,
    VALID_STATUS_CODES,
    get_file_metadata_for_all_files_in_inbox,
)
from src.scripts.ega.utils import SecretManager

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)

REMOTE_PATH = "/encrypted"
SFTP_HOSTNAME = "inbox.ega-archive.org"
SFTP_PORT = 22

def get_active_account() -> str:
    """Helper function to determine which gcloud account is running the workflow"""
    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"

def file_pre_validation(encrypted_data_file: str, token: str) -> bool:
    headers = format_request_header(token)
    file_name = os.path.basename(encrypted_data_file)
    file_metadata = get_file_metadata_for_all_files_in_inbox(headers=headers)

    for file in file_metadata:
        relative_file_path = file["relative_path"]
        incoming_file_name = os.path.basename(relative_file_path)

        if file_name == incoming_file_name:
            raise ValueError(f"Found file {file_name} in metadata.")
    logging.info(f"Did not find any files with the given file name {file_name}")

    return True

def transfer_file(encrypted_data_file: str, ega_inbox: str, password: str) -> None:
    """Transfer encrypted data file to EGA inbox via SFTP."""
    try:    
        # Establish an SFTP connection
        with paramiko.Transport((SFTP_HOSTNAME, SFTP_PORT)) as transport:
            transport.connect(username=ega_inbox, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Upload the encrypted data file
            remote_file = os.path.join(REMOTE_PATH, os.path.basename(encrypted_data_file))
            sftp.put(encrypted_data_file, remote_file)
        
        logging.info(f"Successfully transferred {encrypted_data_file} to EGA inbox {ega_inbox}")
    except Exception as e:
        logging.error(f"Error transferring file: {str(e)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Transfer a file to EGA using an FTP server"
    )
    parser.add_argument(
        "--encrypted_data_file",
        required=True,
        help="Data file that is already encrypted"
    )
    parser.add_argument(
        "--ega_inbox",
        required=True,
        help="Inbox assigned to the current PM"
    )
    args = parser.parse_args()

    # Retrieve the secret value from Google Secret Manager
    # password = SecretManager(project_id="gdc-submissions", secret_id="ega_password", version_id=1).get_ega_password_secret()
    password = "qMTEX8SX"
    access_token = LoginAndGetToken(username=args.ega_inbox, password=password).login_and_get_token()
    file_pre_validation(args.encrypted_data_file, access_token)
    logging.info("Starting script to transfer file to EGA")

    # transfer_file(args.encrypted_data_file, args.ega_inbox)

    logging.info("Script finished")