version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow TransferToGdc {
  input {
    # Sample input
    String sample_id
    String bam_file
    String bam_name
    String agg_project
    String data_type
    String file_size
    String md5
    String program
    String project

    # ReadGroup input
    String read_group_id
    String experiment_name
    String flow_cell_barcode
    String instrument_model
    String library_name
    String library_preperation_kit_catalog_number
    String library_preperation_kit_name
    String library_preperation_kit_vendor
    String library_preperation_kit_version
    String library_selection
    String library_strand
    String library_strategy
    String multiplex_barcode
    String platform
    String read_group_name
    String reference_sequence
    String sequencing_center
    String sequencing_date
    String target_capture_kit
    String type
    Int lane_number
    Int read_length
    Int reference_sequence_version
    Boolean is_paired_end
    Boolean includes_spike_ins
    Boolean to_trim_adapter_sequence

    String workspace_name
    String workspace_project
    File gdc_token
    Boolean dry_run = false
    Boolean registration_status
  }

  if (registration_status) {
    String token_value = (read_lines(gdc_token))[0]

    call submitMetadataToGDC {
      input:
        sample_id = sample_id,
        bam_file = bam_file,
        bam_name = bam_name,
        agg_projec = agg_projec,
        data_type = data_type,
        file_size = file_size,
        md5 = md5,
        read_group_id = read_group_id,
        experiment_name = experiment_name,
        flow_cell_barcode = flow_cell_barcode,
        instrument_model = instrument_model,
        library_name = library_name,
        library_preperation_kit_catalog_number = library_preperation_kit_catalog_number,
        library_preperation_kit_name = library_preperation_kit_name,
        library_preperation_kit_vendor = library_preperation_kit_vendor,
        library_preperation_kit_version = library_preperation_kit_version,
        library_selection = library_selection,
        library_strand = library_strand,
        library_strategy = library_strategy,
        multiplex_barcode = multiplex_barcode,
        platform = platform,
        read_group_name = read_group_name,
        reference_sequence = reference_sequence,
        sequencing_center = sequencing_center,
        sequencing_date = sequencing_date,
        target_capture_kit = target_capture_kit,
        lane_number = lane_number,
        read_length = read_length,
        reference_sequence_version = reference_sequence_version,
        is_paired_end = is_paired_end,
        includes_spike_ins = includes_spike_ins,
        to_trim_adapter_sequence = to_trim_adapter_sequence,
        program = program,
        project = project,
        gdc_token = token_value
    }

    call RetrieveGdcManifest {
      input:
        program = program,
        project = project,
        sar_id = submitMetadataToGDC.UUID,
        gdc_token = token_value,
        dry_run = dry_run
    }

    call TransferBamToGdc {
      input:
        bam_path = submitMetadataToGDC.bam_path,
        bam_name = submitMetadataToGDC.bam_name,
        manifest = RetrieveGdcManifest.manifest,
        gdc_token = gdc_token,
        dry_run = dry_run
    }

    call validateFileStatus {
      input:
        program = program,
        project = project,
        # metadata = metadata,
        gdc_token = token_value,
        transfer_log = TransferBamToGdc.gdc_transfer_log
    }

    call tasks.CreateTableLoadFile as tsv_file {
      input:
        sample_id = sample_id,
        uuid = submitMetadataToGDC.UUID,
        file_state = validateFileStatus.file_state,
        state = validateFileStatus.state,
        registration_status = registration_status
    }

    call tasks.UpsertMetadataToDataModel {
      input:
        workspace_name = workspace_name,
        workspace_project = workspace_project,
        tsv = tsv_file.load_tsv
    }
  }
}

task RetrieveGdcManifest {

  input {
    String program
    String project
    String sar_id
    String gdc_token
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
    String bam_path
    String bam_name
    File manifest
    File gdc_token
    Boolean dry_run
  }

  File bam_file = bam_path
  Int disk_size = ceil(size(bam_file, "GiB") * 1.5)

  command {
    set -e
    mv ~{bam_file} ./~{bam_name}
    ls /cromwell_root

    if ~{dry_run}; then
      echo "This was a dry run of uploading to GDC" > gdc_transfer.log
      echo "BAM_FILE=~{bam_path}" >> gdc_transfer.log
      echo "MANIFEST=~{manifest}" >> gdc_transfer.log
    else
      gdc-client --version
      gdc-client upload -t ~{gdc_token} -m ~{manifest} --debug --log-file gdc_transfer.log
    fi
  }

  runtime {
    memory: "7.5 GB"
    docker: "schaluvadi/horsefish:submissionV2GDC"
    cpu: 2
    preemptible: 3
    disks: "local-disk " + disk_size + " HDD"
  }

  output {
    File gdc_transfer_log = "gdc_transfer.log"
  }
}

task submitMetadataToGDC {
    input {
      String program
      String project
      # File metadata
      String gdc_token
    }

    command {
        python3 /main.py --step "submit_metadata" \
                        --token ~{gdc_token} \
                        --program ~{program} \
                        --project ~{project}
    }

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
      String UUID = read_lines("UUID.txt")[0]
      String bam_path = read_lines("bam.txt")[0]
      String bam_name = read_lines("bam.txt")[1]
    }
}

task validateFileStatus {
    input {
      String program
      String project
      # File metadata
      String gdc_token
      File transfer_log
    }

    command {
        python3 /main.py --program ~{program} \
                        --project ~{project} \
                        --step "validate_status" \
                        --token ~{gdc_token}
    }

    runtime {
      preemptible: 3
      docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
      String state = read_lines("fileStatus.txt")[0]
      String file_state = read_lines("fileStatus.txt")[1]
    }
}