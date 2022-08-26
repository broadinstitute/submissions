version 1.0

workflow DeleteFromGdc {

  input {
    String program
    String project
    String sar_id
    File gdc_token
    Boolean dry_run = false
  }

  String token_value = (read_lines(gdc_token))[0]

  call RetrieveGdcManifest {
    input:
      program = program,
      project = project,
      sar_id = sar_id,
      gdc_token = (read_lines(gdc_token))[0],
      dry_run = dry_run
    }

  call DeleteBamFromGdc {
    input:
      manifest = RetrieveGdcManifest.manifest,
      gdc_token = gdc_token,
      dry_run = dry_run
  }

  output {
    File gdc_deletion_log = DeleteBamFromGdc.gdc_deletion_log
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
    docker: "us.gcr.io/broad-gotc-prod/eddy:1.1.0-1595358485"
    cpu: 1
    disks: "local-disk " + 20 + " HDD"
  }

  output {
      File manifest = "manifest.yml"
  }
}


task DeleteBamFromGdc {

  input {
    File manifest
    File gdc_token
    Boolean dry_run
  }

  command {
    set -e

    if ~{dry_run}; then
      echo "This is a fake result for a dry run" > gdc_deletion.log
    else
      gdc-client upload \
        -t ~{gdc_token} \
        -m ~{manifest} \
        --delete \
        --log-file gdc_deletion.log
    fi
  }

  runtime {
    memory: "3.75 GB"
    docker: "us.gcr.io/broad-gotc-prod/eddy:1.1.0-1595358485"
    cpu: 1
    disks: "local-disk " + 20 + " HDD"
  }

  output {
    File gdc_deletion_log = "gdc_deletion.log"
  }
}