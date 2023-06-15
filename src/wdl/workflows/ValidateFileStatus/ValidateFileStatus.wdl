version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow VerifyRegistration {
  input {
    File gdc_token
    String program
    String project
    String workspace
    String billing_project
    String sample_id
    Boolean delete = false
    File? aggregation_path
  }

  String token_value = (read_lines(gdc_token))[0]

  call validateFileStatus as file_status {
    input:
      program = program,
      project = project,
      sample_id = sample_id,
      gdc_token = token_value,
      delete = delete
  }

  call tasks.CreateValidationStatusTable as tsv {
      input:
        file_state = file_status.file_state
  }

  call tasks.UpsertMetadataToDataModel {
      input:
        workspace_name = workspace,
        workspace_project = billing_project,
        tsv = tsv.load_tsv
  }

  if (delete) {
      if (file_status.file_state == "validated") {
        call tasks.DeleteFileFromWorkspace {
            input:
              aggregation_path = aggregation_path
        }
      }
  }

  output {
    Boolean file_state = file_status.file_state
  }
}

task validateFileStatus {
    input {
        String program
        String project
        String sample_id
        String gdc_token
        Boolean delete
    }

    command {
        python3 /src/scripts/validateFileStatus.py -pg ~{program} \
                                                -pj ~{project} \
                                                -s ~{sample_id} \
                                                -d ~{delete} \
                                                -t ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV2GDC"
        preemptible: 1
    }

    output {
        String file_state = read_string("file_state.txt")
    }
}