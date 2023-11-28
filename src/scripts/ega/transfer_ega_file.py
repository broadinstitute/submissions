import os
import subprocess
import argparse

def transfer_file(encrypted_data_file, ega_inbox):
    REMOTE_PATH = "/encrypted"
    SFTP_HOSTNAME = "inbox.ega-archive.org"
    SFTP_PORT = 22

    print("before")
    # Retrieve the secret value from Google Secret Manager
    secret_res = subprocess.run(['gcloud', 'secrets', 'versions', 'access', 'latest', '--secret=ega_password', '--format=get(payload.data)', '--project=gdc-submissions'], capture_output=True, text=True)
    print("after")
    # Check for errors
    if secret_res.returncode != 0:
        raise RuntimeError(secret_res.stderr)

    # Extract the secret value
    password = res.stdout.strip()

    transport = paramiko.Transport((SFTP_HOSTNAME, SFTP_PORT))
    transport.connect(username=ega_inbox, password=password)

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
    print("starting script")
    transfer_file(args.encrypted_data_file, args.ega_inbox)