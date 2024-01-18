import os
import logging
import argparse
import paramiko
import subprocess
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

def file_pre_validation(password: str, ega_inbox: str, token: str) -> bool:
    headers = format_request_header(token)
    file_metadata = get_file_metadata_for_all_files_in_inbox(headers=headers)

    logging.info(f"Found file metadata. Now attempting to link all files associated with {self.sample_alias}")

    files = []

    for file in file_metadata:
        relative_file_path = file["relative_path"]
        file_name = Path(relative_file_path).name
        sample_alias_from_path = Path(file_name).stem

        # There could be multiple files associated with a given sample, so we loop through ALL files and append
        # all the file provisional IDs to a list
        if sample_alias_from_path == self.sample_alias:
            files.append(file["provisional_id"])

    if files:
        logging.info(f"Found {len(files)} associated with sample {self.sample_alias}!")
        sample_metadata["files"] = files
        return sample_metadata
    else:
        raise Exception(
            f"Expected to find at least 1 file associated with sample {self.sample_alias}. Instead found none."
        )


def transfer_file(data_file, encrypted_data_file: str, ega_inbox: str) -> None:
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
        "--encrypted-data-file",
        required=True,
        help="Data file that is already encrypted"
    )
    parser.add_argument(
        "--ega-inbox",
        required=True,
        help="Inbox assigned to the current PM"
    )
    args = parser.parse_args()

    # Retrieve the secret value from Google Secret Manager
    password = SecretManager(project_id="gdc-submissions", secret_id="ega_password", version_id=1).get_ega_password_secret()
    access_token = LoginAndGetToken(username=args.user_name, password=password).login_and_get_token()

    logging.info("Starting script to transfer file to EGA")

    transfer_file(args.encrypted_data_file, args.ega_inbox)

    logging.info("Script finished")