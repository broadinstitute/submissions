version 1.0

workflow TransferToGdc {
  input {
    File metadata
    File gdc_token
    String program
    String project
    Boolean dry_run = false
  }

  String token_value = (read_lines(gdc_token))[0]

  call verifyGDCRegistration {
    input:
      program = program,
      project = project,
      gdc_token = token_value
  }

  call submitMetadataToGDC {
    input:
      program = program,
      project = project,
      metadata = metadata,
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
      metadata = metadata,
      gdc_token = token_value,
      transfer_log = TransferBamToGdc.gdc_transfer_log
  }

  output {
    File gdc_transfer_log = TransferBamToGdc.gdc_transfer_log
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
        File metadata
        String gdc_token
    }

    command {
        python3 /main.py --metadata ~{metadata} \
                        --step "submit_metadata" \
                        --token ~{gdc_token} \
                        --program ~{program} \
                        --project ~{project}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        String UUID = read_lines("UUID.txt")[0]
        String bam_path = read_lines("bam.txt")[0]
        String bam_name = read_lines("bam.txt")[1]
    }
}

task verifyGDCRegistration {
    input {
        String program
        String project
        String alias_value
        String gdc_token
    }

    command {
        python3 /main.py --program ~{program} \
                        --project ~{project} \
                        --alias_value ~{alias_value} \
                        --step "verify_registration" \
                        --token ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        String UUID = read_lines("isValid.txt")[0]
    }
}

task validateFileStatus {
    input {
        String program
        String project
        File metadata
        String gdc_token,
        File transfer_log
    }

    command {
        python3 /main.py --program ~{program} \
                        --project ~{project} \
                        --metadata ~{metadata} \
                        --step "validate_status" \
                        --token ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        String UUID = read_lines("fileStatus.txt")[0]
    }
}