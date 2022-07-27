version 1.0

workflow DeleteFromGdc {

  input {
    File program
    String project
    String sar_id
    String vault_token_path
    String gdc_token_vault_path
    Boolean dry_run = false
  }

  call RetrieveGdcManifest {
    input:
      program = program,
      project = project,
      sar_id = sar_id,
      vault_token_path = vault_token_path,
      gdc_token_vault_path = gdc_token_vault_path,
      dry_run = dry_run
    }

  call DeleteBamFromGdc {
    input:
      manifest = RetrieveGdcManifest.manifest,
      vault_token_path = vault_token_path,
      gdc_token_vault_path = gdc_token_vault_path
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
    String vault_token_path
    String gdc_token_vault_path
    Boolean dry_run
  }

  command {
    set -e
    export VAULT_ADDR=https://clotho.broadinstitute.org:8200
    export VAULT_TOKEN=$(gsutil cat ~{vault_token_path})

    gdc_token=$(vault read -field=token ~{gdc_token_vault_path})

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
    String vault_token_path
    String gdc_token_vault_path
    Boolean dry_run
  }

  command {
    set -e

    export VAULT_ADDR=https://clotho.broadinstitute.org:8200
    export VAULT_TOKEN=$(gsutil cat ~{vault_token_path})

    vault read -field=token ~{gdc_token_vault_path} > gdc_token
    chmod 600 gdc_token

    if ~{dry_run}; then
      echo "This is a fake result for a dry run" > gdc_deletion.log
    else
      gdc-client upload \
        -t gdc_token \
        -m ~{manifest} \
        --delete \
        --log-file gdc_deletion.log
    fi
  }

  runtime {
    memory: "3.75 GB"
    cpu: 1
    disks: "local-disk 10 HDD"
  }

  output {
    File gdc_deletion_log = "gdc_deletion.log"
  }
}