version 1.0

import "../../tasks/terra_tasks.wdl" as tasks
import "../../utilities/Utilities.wdl" as utils

workflow ValidateDbGapSampleStatus {
    input {
        String workspace_name
        String workspace_project
        String sample_id
        String sample_alias
        String phs_id
        String data_type
    }

    if ((data_type != "WGS") && (data_type != "Exome") && (data_type != "RNA")) {
        call utils.ErrorWithMessage as ErrorMessageIncorrectInput {
            input:
                message = "data_type must be either 'WGS', 'Exome', or 'RNA'."
        }
    }

      call ValidateDbgapSample {
        input:
          sample_alias = sample_alias,
          sample_id = sample_id,
          phs_id = phs_id,
          data_type = data_type
      }

      call tasks.UpsertMetadataToDataModel {
        input:
          workspace_name = workspace_name,
          workspace_project = workspace_project,
          tsv = ValidateDbgapSample.sample_status_tsv
      }

      output { }
    }

task ValidateDbgapSample {
    input {
        String sample_alias
        String sample_id
        String phs_id
        String data_type
    }

    command {
        set -eo pipefail
        python3 /src/scripts/dbgap/validate_dbgap_sample.py -sample_alias ~{sample_alias} \
                                                            -sample_id ~{sample_id} \
                                                            -phs_id ~{phs_id} \
                                                            -data_type ~{data_type}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV2GDC"
        preemptible: 1
    }

    output {
        File sample_status_tsv = "sample_status.tsv"
    }
}
