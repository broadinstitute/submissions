version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow EGAFileTransfer {
    input {
      File aggregation_path
      File crypt4gh_encryption_key
      String ega_inbox
  }

  call InboxFileTransfer {
      input:
        aggregation_path = aggregation_path,
        crypt4gh_encryption_key = crypt4gh_encryption_key
  }

  call ascpFileTransfer {
    input:
      encryptedDataFile = EncryptDataFiles.encryptedDataFile,
      ega_inbox = ega_inbox
  }
}

task EncryptDataFiles {
    input {
        File aggregation_path
        File crypt4gh_encryption_key
    }

    command <<<
        python3 <<EOF
        import subprocess

        output_file = f'encrypted_{aggregation_path}.c4gh'
        command = f'crypt4gh encrypt --recipient_pk {crypt4gh_encryption_key} < {aggregation_path} > {output_file}'
        print(f"command {command}")
        res = subprocess.run(command, capture_output=True, shell=True)

        if res.stderr:
            raise RuntimeError(res.stderr.decode())
        EOF
    >>>

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        File encryptedDataFile = "encrypted_{aggregation_path}.c4gh"
    }
}

task InboxFileTransfer {
    input {
        File encryptedDataFile
        String ega_inbox
    }

    command <<<
        python3 <<EOF
        import subprocess
        import os

        REMOTE_PATH = "/encrypted"

        # Retrieve the secret value from Google Secret Manager
        secret_res = subprocess.run(['gcloud', 'secrets', 'versions', 'access', 'latest', f'--secret={secret_name}', '--format=get(payload.data)'], capture_output=True, text=True)

        # Check for errors
        if secret_res.returncode != 0:
          raise RuntimeError(secret_res.stderr)

        # Extract the secret value
        file_encryption_key = res.stdout.strip()

        output_file = f'encrypted_{aggregation_path}.c4gh'
        command = f'crypt4gh encrypt --recipient_pk {file_encryption_key} < {aggregation_path} > {output_file}'
        print(f"command {command}")
        res = subprocess.run(command, capture_output=True, shell=True)

        if res.stderr:
            raise RuntimeError(res.stderr.decode())
        EOF
    >>>

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        File transferLog = "upload/inbox-transfer.log"
    }
}