import os
import logging
import argparse
import paramiko
import subprocess
import google_crc32c
from google.cloud import secretmanager

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)

def get_active_account():
    """Helper function to determine which gcloud account is running the workflow"""
    try:
        result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"

def get_ega_password_secret():
    project_id = "gdc-submissions"
    secret_id = "ega_password"
    version_id = 1

    # Connect to the client to allow secret access
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    
    # Verify payload checksum.
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        logging.error("Data corruption detected.")
    else:
        logging.info("Successfully accessed secret")

    # Decode payload using UTF-8
    secret_payload = response.payload.data.decode("UTF-8")

    return secret_payload

def transfer_file(encrypted_data_file, ega_inbox):
    REMOTE_PATH = "/encrypted"
    SFTP_HOSTNAME = "inbox.ega-archive.org"
    SFTP_PORT = 22

    # Retrieve the secret value from Google Secret Manager
    ega_password = get_ega_password_secret()\
    transport = paramiko.Transport((SFTP_HOSTNAME, SFTP_PORT))
    transport.connect(username=ega_inbox, password=ega_password)

    # Create an SFTP client from the transport
    sftp = paramiko.SFTPClient.from_transport(transport)
    remote_file = os.path.join(REMOTE_PATH, os.path.basename(encrypted_data_file))
    sftp.put(encrypted_data_file, remote_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="This script will use an ftp server to transfer file to ega"
    )
    parser.add_argument(
        "-encrypted_data_file",
        required=True,
        help="Data file that is already encrypted"
    )
    parser.add_argument(
        "-ega_inbox",
        required=True,
        help="Inbox assigned to the current PM"
    )
    args = parser.parse_args()
    logging.info("Starting script to transfer file to ega")

    transfer_file(args.encrypted_data_file, args.ega_inbox)
    logging.info("Successfully finished script")