version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow TransferToGdc {
  input {
    # Sample input
    String sample_id
    String bam_file
    String agg_project
    String data_type
    String file_size
    String md5
    String program
    String project
    String workspace_name
    String workspace_project
    File gdc_token
    Boolean dry_run = false
    Boolean registration_status
    File?   monitoring_script
  }

  String token_value = (read_lines(gdc_token))[0]

  call tasks.addReadsField as reads {
    input:
      workspace_name = workspace_name,
      workspace_project = workspace_project,
      sample_id = sample_id,
      gdc_token = token_value
      project = project
      program = program
  }

  if (registration_status) {
    call submitMetadataToGDC {
      input:
        sample_id = sample_id,
        bam_file = bam_file,
        agg_project = agg_project,
        data_type = data_type,
        file_size = file_size,
        md5 = md5,
        program = program,
        project = project,
        read_groups = reads.reads_json,
        gdc_token = token_value
    }

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
        bam_path = submitMetadataToGDC.bam_path,
        bam_name = submitMetadataToGDC.bam_file_name,
        manifest = RetrieveGdcManifest.manifest,
        gdc_token = gdc_token,
        dry_run = dry_run,
        monitoring_script = monitoring_script
    }

    call validateFileStatus {
      input:
        program = program,
        project = project,
        sample_id = sample_id,
        agg_project = agg_project,
        data_type = data_type,
        gdc_token = token_value,
        transfer_log = TransferBamToGdc.gdc_transfer_log
    }

    call tasks.CreateTableLoadFile as tsv_file {
      input:
        sample_id = sample_id,
        uuid = submitMetadataToGDC.UUID,
        file_state = validateFileStatus.file_state,
        state = validateFileStatus.state,
        registration_status = registration_status,
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
    docker: "schaluvadi/horsefish:submissionV2GDC"
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
    String  bam_path
    String  bam_name
    File    manifest
    File    gdc_token
    Boolean dry_run
    File?   monitoring_script
  }

  File bam_file = bam_path
  Int disk_size = ceil(size(bam_file, "GiB") * 1.5)

  command {
    set -e

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
      echo "BAM_FILE=~{bam_path}" >> gdc_transfer.log
      echo "MANIFEST=~{manifest}" >> gdc_transfer.log
    else
      gdc-client --version
      gdc-client upload -t ~{gdc_token} -m ~{manifest} --debug --log-file gdc_transfer.log
    fi

    pwd
  }

  runtime {
    memory: "7.5 GB"
    docker: "schaluvadi/horsefish:submissionV2GDC"
    cpu: 2
    preemptible: 3
    disks: "local-disk " + disk_size + " HDD"
  }

  output {
    File  gdc_transfer_log = "gdc_transfer.log"
    File? monitoring_log = "monitoring.log"
  }
}

task submitMetadataToGDC {
    input {
      String sample_id
      String bam_file
      String agg_project
      String data_type
      String file_size
      String md5
      String program
      String project
      String read_groups
      String gdc_token
    }

    File json_file = write_json(read_groups)

    command {
        python3 /main.py --step "submit_metadata" \
                        --alias_value ~{sample_id} \
                        --program ~{program} \
                        --project ~{project} \
                        --agg_path ~{bam_file} \
                        --agg_project ~{agg_project} \
                        --data_type ~{data_type} \
                        --file_size ~{file_size} \
                        --md5 ~{md5} \
                        --read_groups ~{json_file} \
                        --token ~{gdc_token}
    }

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
      String UUID = read_lines("UUID.txt")[0]
      String bam_path = read_lines("bam.txt")[0]
      String bam_file_name = read_lines("bam.txt")[1]
      File read_json_file = json_file
    }
}

task validateFileStatus {
    input {
      String program
      String project
      String sample_id
      String agg_project
      String data_type
      String gdc_token
      File transfer_log
    }

    command {
        python3 /main.py --alias_value ~{sample_id} \
                        --agg_project ~{agg_project} \
                        --data_type ~{data_type} \
                        --program ~{program} \
                        --project ~{project} \
                        --step "validate_status" \
                        --token ~{gdc_token}
    }

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
      String state = read_lines("fileStatus.txt")[0]
      String file_state = read_lines("fileStatus.txt")[1]
    }
}