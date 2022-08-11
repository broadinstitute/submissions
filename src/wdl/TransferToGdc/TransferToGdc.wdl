version 1.0

workflow TransferToGdc {

  input {
    File bam_file
    String gdc_bam_file_name
    String program
    String project
    String aggregation_project
    String alias_value
    String data_type
    File gdc_token
    Boolean dry_run = false
  }

  String token_value = (read_lines(gdc_token))[0]

  call verifyGDCRegistration {
    input:
      program = program,
      project = project,
      alias_value = alias_value,
      gdc_token = token_value
  }

  call submitMetadataToGDC {
    input:
      program = program,
      project = project,
      aggregation_project = aggregation_project,
      alias_value = alias_value,
      data_type = data_type,
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
      bam_file = bam_file,
      gdc_bam_file_name = gdc_bam_file_name,
      manifest = RetrieveGdcManifest.manifest,
      gdc_token = token_value,
      dry_run = dry_run
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
      curl --header "X-Auth-Token: $gdc_token" \
        https://api.gdc.cancer.gov/v0/submission/~{program}/~{project}/manifest?ids=~{sar_id} \
        > manifest.yml
    fi
  }

  runtime {
    memory: "3.75 GB"
    docker: "us.gcr.io/broad-gotc-prod/eddy:1.1.0-1595358485"
    cpu: 1
    disks: "local-disk " + 20 + " HDD"
  }

  output {
      File manifest = "manifest.yml"
  }
}

task TransferBamToGdc {

  input {
    File bam_file
    String gdc_bam_file_name
    File manifest
    String gdc_token
    Boolean dry_run
  }

  Int disk_size = ceil(size(bam_file, "GiB") * 1.5)

  command {
    set -e

    if ~{dry_run}; then
      echo "This was a dry run of uploading to GDC" > gdc_transfer.log
      echo "BAM_FILE=~{bam_file}" >> gdc_transfer.log
      echo "MANIFEST=~{manifest}" >> gdc_transfer.log
    else
      mv ~{bam_file} ./~{gdc_bam_file_name}
      gdc-client upload \
          -t gdc_token \
          -m ~{manifest} \
          --log-file gdc_transfer.log
    fi
  }

  runtime {
    memory: "7.5 GB"
    docker: "us.gcr.io/broad-gotc-prod/eddy:1.1.0-1595358485"
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
        String aggregation_project
        String alias_value
        String data_type
        String gdc_token
    }

    command {
        python3 /main.py --program ~{program} \
                        --project ~{project} \
                        --agg_project ~{aggregation_project} \
                        --alias_value ~{alias_value} \
                        --data_type ~{data_type} \
                        --token ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        String UUID = (read_lines("/UUID.txt"))[0]
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
                        --token ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        String UUID = (read_lines("/isValid.txt"))[0]
    }
}