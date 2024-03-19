version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow ValidateGDCFileStatus {
  input {
    String workspace_name
    String workspace_project
    String sample_id
    String sample_alias
    String phs_id
    String data_type
    Boolean delete = false
    File aggregation_path
  }

  call ValidateDbgapSample {
    input:
      sample_alias = sample_alias,
      phs_id = phs_id,
      data_type = data_type
  }

  call tasks.CreateValidationStatusTable as tsv {
    input:
      sample_id = sample_id,
      sample_status = ValidateDbgapSample.sample_status
  }

  call tasks.UpsertMetadataToDataModel {
    input:
      workspace_name = workspace_name,
      workspace_project = workspace_project,
      tsv = tsv.load_tsv
  }

  if (delete) {
    if (ValidateDbgapSample.sample_status == "public") {
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
        String phs_id
        String data_type
    }

    command {
        set -eo pipefail
        python3 /src/scripts/dbgap/validate_dbgap_sample.py -sample_alias ~{sample_alias} \
                                                            -phs_id ~{phs_id} \
                                                            -data_type ~{data_type}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV2GDC"
        preemptible: 1
    }

    output {
        String sample_status = read_lines("sample_status.txt")[0]
    }
}