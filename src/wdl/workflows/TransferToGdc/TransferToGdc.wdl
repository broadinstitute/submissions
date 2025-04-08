version 1.0

import "../../tasks/terra_tasks.wdl" as tasks
import "../../utilities/Utilities.wdl" as utils


workflow TransferToGdc {
  input {
    # Sample input
    String sample_alias
    String aggregation_path
    String agg_project
    String data_type
    String program
    String project
    String workspace_name
    String workspace_project
    File md5_file
    File gdc_token
    Boolean dry_run = false
    Boolean deliver_files = true
    File?   monitoring_script
    File? read_group_metadata_json
    Int aggregation_version
    String sample_id
  }

  if ((data_type != "WGS") && (data_type != "Exome") && (data_type != "RNA")) {
    call utils.ErrorWithMessage as ErrorMessageIncorrectInput {
        input:
            message = "data_type must be either 'WGS', 'Exome', or 'RNA'."
    }
  }
  String data_type_converted = if data_type == "Exome" then "WXS" else data_type

  String token_value = (read_lines(gdc_token))[0]
  String md5 = (read_lines(md5_file))[0]

  call tasks.verifyGDCRegistration as verified {
    input:
      program = program,
      project = project,
      gdc_token = token_value,
      sample_alias = sample_alias
  }

  if (verified.registration_status) {
    call tasks.addReadsField as reads {
      input:
        workspace_name = workspace_name,
        workspace_project = workspace_project,
        sample_alias = sample_alias,
        gdc_token = token_value,
        project = project,
        program = program,
        read_group_metadata_json = read_group_metadata_json
    }

    call submitMetadataToGDC {
      input:
        sample_alias = sample_alias,
        aggregation_path = aggregation_path,
        agg_project = agg_project,
        data_type = data_type_converted,
        md5 = md5,
        program = program,
        project = project,
        read_groups = reads.reads_json,
        gdc_token = token_value
    }

    if (deliver_files) {
      call RetrieveGdcManifest {
        input:
          program   = program,
          project   = project,
          sar_id    = submitMetadataToGDC.UUID,
          gdc_token = token_value,
          dry_run   = dry_run
      }

      call TransferBamToGdc {
        input:
          aggregation_path = aggregation_path,
          bam_name = submitMetadataToGDC.bam_file_name,
          manifest = RetrieveGdcManifest.manifest,
          gdc_token = gdc_token,
          dry_run = dry_run,
          monitoring_script = monitoring_script
      }

      call tasks.ValidateFileStatus as file_status {
        input:
          program = program,
          project = project,
          sample_alias = sample_alias,
          agg_project = agg_project,
          data_type = data_type_converted,
          gdc_token = token_value,
          previous_task = TransferBamToGdc.done
      }

      call tasks.CreateTableLoadFile as tsv_file {
        input:
          sample_id = sample_id,
          uuid = submitMetadataToGDC.UUID,
          file_state = file_status.file_state,
          state = file_status.state,
          registration_status = verified.registration_status,
          read_json_file = submitMetadataToGDC.read_json_file
      }

      call tasks.UpsertMetadataToDataModel {
        input:
          workspace_name    = workspace_name,
          workspace_project = workspace_project,
          tsv               = tsv_file.load_tsv
      }
    }
  }
}

task RetrieveGdcManifest {
  input {
    String  program
    String  project
    String  sar_id
    String  gdc_token
    Boolean dry_run
  }

  command {
    set -e

    if ~{dry_run}; then
      echo "This is a fake manifest for a dry run" > manifest.yml
    else
      curl --header "X-Auth-Token: ~{gdc_token}" \
        https://api.gdc.cancer.gov/v0/submission/~{program}/~{project}/manifest?ids=~{sar_id} \
        > manifest.yml
    fi
  }

  runtime {
    memory: "3.75 GB"
    docker: "schaluvadi/horsefish:submissionV1"
    cpu: 1
    preemptible: 3
    disks: "local-disk " + 20 + " HDD"
  }

  output {
      File manifest = "manifest.yml"
  }
}

task TransferBamToGdc {
  input {
    String  aggregation_path
    String  bam_name
    File    manifest
    File    gdc_token
    Boolean dry_run
    File?   monitoring_script
  }

  File bam_file = aggregation_path
  Int disk_size = ceil(size(bam_file, "GiB") * 1.5)

  command {
    set -e
    echo "getting gdc client version"
    gdc-client --version

    pwd
    # if the WDL/task contains a monitoring script as input
    if [ ! -z "~{monitoring_script}" ]; then
      chmod a+x ~{monitoring_script}
      ~{monitoring_script} > monitoring.log &
    else
      echo "No monitoring script given as input" > monitoring.log &
    fi

    pwd
    # put the localized bam file in the same place as the gdc-client
    mv ~{bam_file} ./~{bam_name}
    pwd
    ls /cromwell_root
    pwd

    if ~{dry_run}; then
      pwd
      echo "This was a dry run of uploading to GDC" > gdc_transfer.log
      echo "BAM_FILE=~{aggregation_path}" >> gdc_transfer.log
      echo "MANIFEST=~{manifest}" >> gdc_transfer.log
    else
      gdc-client --version
      gdc-client upload -t ~{gdc_token} -m ~{manifest} --debug --log-file gdc_transfer.log
    fi

    pwd
  }

  runtime {
    memory: "8 GB"
    docker: "schaluvadi/horsefish:submissionV1"
    cpu: 2
    disks: "local-disk " + disk_size + " HDD"
  }

  output {
    File  gdc_transfer_log = "gdc_transfer.log"
    File? monitoring_log = "monitoring.log"
    Boolean done = true
  }
}

task submitMetadataToGDC {
    input {
      String sample_alias
      String aggregation_path
      String agg_project
      String data_type
      String md5
      String program
      String project
      String read_groups
      String gdc_token
    }

    File json_file = write_json(read_groups)

    command {
      set -eo pipefail
      python3 /src/scripts/gdc/submit_metadata.py --sample_alias ~{sample_alias} \
                      --program ~{program} \
                      --project ~{project} \
                      --aggregation_path ~{aggregation_path} \
                      --agg_project ~{agg_project} \
                      --data_type ~{data_type} \
                      --md5 ~{md5} \
                      --read_groups ~{json_file} \
                      --token ~{gdc_token}
    }

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV2"
    }

    output {
      String UUID = read_lines("UUID.txt")[0]
      String bam_file_name = read_lines("bam.txt")[0]
      File read_json_file = json_file
    }
}