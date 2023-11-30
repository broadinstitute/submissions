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

    Int disk_size = ceil(size(aggregation_path, "GiB") * 2.5)

    command {
        python3 /src/scripts/ega/encrypt_data_file.py \
            -aggregation_path ~{aggregation_path} \
            -crypt4gh_encryption_key ~{crypt4gh_encryption_key} \
    }

    runtime {
        memory: "30 GB"
        docker: "schaluvadi/horsefish:submissionV2GDC"
        cpu: 2
        disks: "local-disk " + disk_size + " HDD"
    }

    output {
        File encrypted_data_file = "encrypted_" + basename(aggregation_path) + ".c4gh"
    }
}

task InboxFileTransfer {
    input {
        File encrypted_data_file
        String ega_inbox
    }

    Int disk_size = ceil(size(encrypted_data_file, "GiB") * 2.5)

    command {
        python3 /src/scripts/ega/transfer_ega_file.py \
            -encrypted_data_file ~{encrypted_data_file} \
            -ega_inbox ~{ega_inbox} \
    }

    runtime {
        memory: "30 GB"
        docker: "schaluvadi/horsefish:submissionV2GDC"
        cpu: 2
        disks: "local-disk " + disk_size + " HDD"
    }

    output {}
}