version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow TransferToEga {
    input {
      # Sample input
      String sample_id
      String sample_alias
      String version
      String aggregation_project
      String data_type
      String location
      String password
      String ega_inbox
      String study_accession_id
      String submission_accession_id
      String cohort_name
      String construction_protocol
      String ega_site
      String workspace_name
      String workspace_project
      File md5_file
      File gdc_token
      Boolean dry_run = false
      File?   monitoring_script
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

  call TransferFileToEga {
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

task ascpFile {
    input {
        File uploadFile
        File key
        String uploadSite
        String uploadPath
        String ascpUser
        String filename
    }

    command {
      set -e
      mkdir log_files
      export ASPERA_SCP_PASS={self.decrypt(self.password)}
      ascp -T -d -l 600m -m 1m -k 3  -L ./log_files --file-manifest-path={self.logs_directory} \
      --file-manifest=text  --src-base={self.encrypted_output_path} {self.encrypted_output_path} \
      {self.decrypt(self.ega_inbox)}@{self.ega_site}:.
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