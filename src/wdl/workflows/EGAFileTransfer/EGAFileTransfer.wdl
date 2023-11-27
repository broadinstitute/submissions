version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow EGAFileTransfer {
    input {
      File aggregation_path
      File crypt4gh_encryption_key
      String ega_inbox
  }

  call EncryptDataFiles {
      input:
        aggregation_path = aggregation_path,
        crypt4gh_encryption_key = crypt4gh_encryption_key
  }

  call InboxFileTransfer {
    input:
      encrypted_data_file = EncryptDataFiles.encrypted_data_file,
      ega_inbox = ega_inbox
  }
}

task EncryptDataFiles {
    input {
        File aggregation_path
        File crypt4gh_encryption_key
    }

    command <<<
        python <<CODE
            import subprocess

            key = ~{crypt4gh_encryption_key}
            file_path = ~{aggregation_path}

            output_file = f'encrypted_{file_path}.c4gh'
            command = f'crypt4gh encrypt --recipient_pk {key} < {file_path} > {output_file}'
            print(f"command {command}")
            res = subprocess.run(command, capture_output=True, shell=True)

            if res.stderr:
                raise RuntimeError(res.stderr.decode())
        CODE
    <<<

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        File encrypted_data_file = "encrypted_{aggregation_path}.c4gh"
    }
}

task InboxFileTransfer {
    input {
        File encrypted_data_file
        String ega_inbox
    }

    command {
        python <<CODE
            import subprocess
            import os

            REMOTE_PATH = "/encrypted"
            SFTP_HOSTNAME = "inbox.ega-archive.org"
            SFTP_PORT = 22

            # Retrieve the secret value from Google Secret Manager
            secret_res = subprocess.run(['gcloud', 'secrets', 'versions', 'access', 'latest', f'--secret={secret_name}', '--format=get(payload.data)'], capture_output=True, text=True)

            # Check for errors
            if secret_res.returncode != 0:
                raise RuntimeError(secret_res.stderr)

            # Extract the secret value
            password = res.stdout.strip()

            transport = paramiko.Transport((SFTP_HOSTNAME, SFTP_PORT))
            transport.connect(username=ega_inbox, password=password)

            # Create an SFTP client from the transport
            sftp = paramiko.SFTPClient.from_transport(transport)
            remote_file = os.path.join(self.REMOTE_PATH, os.path.basename(encrypted_data_file))
            sftp.put(encrypted_data_file, remote_file)
        CODE
    }

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        File transferLog = "upload/inbox-transfer.log"
    }
}