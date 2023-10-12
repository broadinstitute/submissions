version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow TransferToEga {
    input {
      # Sample input
      String sample_id
      String sample_alias
      String location
      String password
      String ega_inbox
      String study_accession_id
      String submission_accession_id
      String cohort_name
      String construction_protocol
      String workspace_name
      String workspace_project
      String key
      String avg_standard_deviation
      String avg_mean_insert_size
      String group_library_name
      String library_type
      String sample_material_type
      String analysis_type
      String library_selection
      String library_strategy
      String library_source
      String illumina_instrument
      String library_layout
      String run_file_type
      File aggregation_path
      Boolean dry_run = false
      File?   monitoring_script
  }

  call EncryptDataFiles {
      input:
        aggregation_path = aggregation_path,
        sample_alias = sample_alias
  }

  call DecryptPassword {
      input:
        password = password,
        ega_inbox = ega_inbox,
        key = key
  }

  call ascpFileTransfer {
    input:
      encryptedDataFile = EncryptDataFiles.encryptedDataFile,
      password = UnecryptPassword.password,
      ega_inbox = UnecryptPassword.ega_inbox
  }

  call tasks.SubmitEGAMetadata {
    input:
      sample_id = sample_id,
      password = password,
      ega_inbox = ega_inbox,
      ega_study_accession = ega_study_accession,
      ega_submission_accession = ega_submission_accession,
      cohort_name = cohort_name,
      construction_protocol = construction_protocol,
      ega_site = ega_site,
      workspace_name = workspace_name,
      workspace_project = workspace_project
  }
}

task DecryptPassword {
    input {
        String password
        String ega_inbox
        String key
    }

    command <<<
      python3 <<
        from cryptography.fernet import Fernet
        # This is not how we will want to do this moving forward
        # This is soley for testing! We will either need to use vault or secret manager
        fernet = Fernet(key.encode())
        decrypted_password = fernet.decrypt(password.encode())
        decrypted_ega_inbox = fernet.decrypt(ega_inbox.encode())
        print(decrypted_password.decode())
        print(decrypted_ega_inbox.decode())
      >>
    >>>

    runtime {
      memory: "7.5 GB"
      docker: "schaluvadi/horsefish:submissionV2GDC"
      cpu: 2
      disks: "local-disk 200 HDD"
    }

    output {
      String decrypted_password = read_string(stdout())
      String decrypted_ega_inbox = read_string(stdout())
    }
  }

task EncryptDataFiles {
    input {
        File aggregation_path
        String sample_alias
    }

    command {
        java -jar $JAR_FILE_PATH --i aggregation_path --o /cromwell_root
    }

    runtime {
      memory: "7.5 GB"
      docker: "schaluvadi/horsefish:submissionJavaJar"
      cpu: 2
      disks: "local-disk 200 HDD"
    }

    output {
        File encryptedDataFile = "/cromwell_root/~{sample_alias}.cram.gpg"
    }
}

task ascpFileTransfer {
    input {
        String password
        File encryptedDataFile
        String egaInbox
    }

    command {
      set -e
      mkdir log_files
      
      export ASPERA_SCP_PASS=~{password}
      ascp -T -d -l 600m -m 1m -k 3  -L ./log_files --file-manifest-path=/cromwell_root \
      --file-manifest=text  --src-base=~{encryptedDataFile} ~{encryptedDataFile} \
      ~{egaInbox}@webin.ebi.ac.uk:.
      ls
    }

    runtime {
      memory: "7.5 GB"
      docker: "schaluvadi/horsefish:submissionAspera"
      cpu: 2
      disks: "local-disk 200 HDD"
    }

    output {
        File transferLog = "upload/aspera-scp-transfer.log"
        String site = uploadSite
        String path = uploadPath
    }
}