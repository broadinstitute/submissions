import os
import subprocess
import argparse
from google.cloud import secretmanager
import google_crc32c

def get_active_account():
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

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})

    # Verify payload checksum.
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        print("Data corruption detected.")

    # Print the secret payload.
    payload = response.payload.data.decode("UTF-8")
    print(f"Plaintext: {payload}")

    return payload

def transfer_file(encrypted_data_file, ega_inbox):
    REMOTE_PATH = "/encrypted"
    SFTP_HOSTNAME = "inbox.ega-archive.org"
    SFTP_PORT = 22

    print("before - current running account", get_active_account())
    # Retrieve the secret value from Google Secret Manager
    ega_password = get_ega_password_secret()
    print("got password")
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
    print("starting script")
    transfer_file(args.encrypted_data_file, args.ega_inbox)