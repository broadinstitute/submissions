version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow ValidateGDCFileStatus {
  input {
    String workspace_name
    String workspace_project
    String sample_alias
    Boolean delete = false
    File aggregation_path
  }

  call ValidateDbgapSample {
    input:
      sample_alias = sample_alias
  }

  call tasks.CreateValidationStatusTable as tsv {
    input:
      sample_id = sample_id,
      file_state = file_status.file_state,
      state = file_status.state
  }

  call tasks.UpsertMetadataToDataModel {
    input:
      workspace_name = workspace_name,
      workspace_project = workspace_project,
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
    String file_state = file_status.file_state
  }
}

task ValidateDbgapSample {
    input {
        String sample_alias
    }

    command {
        set -eo pipefail
        python3 /src/scripts/dbgap/validate_dbgap_sample.py -sample_alias ~{sample_alias}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV2GDC"
        preemptible: 1
    }

    output {
        String file_state = read_lines("file_state.txt")[0]
        String state = read_lines("file_state.txt")[1]
    }
}