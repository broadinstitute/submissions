version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow VerifyRegistration {
  input {
    File gdc_token
    String program
    String project
    String workspace
    String project
    String sample_id
    Boolean delete = false
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

  call tasks.CreateValidationStatusTable {
      input:
        file_state = file_status.file_state
  }

  call tasks.UpsertMetadataToDataModel {
      input:

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
        String file_state = read_boolean("file_state.txt")
    }
}