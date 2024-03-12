version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow ValidateGDCFileStatus {
  input {
    File gdc_token
    String program
    String project
    String workspace_name
    String workspace_project
    String sample_id
    String sample_alias
    String agg_project
    String data_type
    Boolean delete = false
    File aggregation_path
  }

  String token_value = (read_lines(gdc_token))[0]

  call tasks.ValidateFileStatus as file_status {
    input:
      program = program,
      project = project,
      sample_alias = sample_alias,
      agg_project = agg_project,
      data_type = data_type,
      gdc_token = token_value,
      previous_task = true
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