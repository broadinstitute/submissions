version 1.0

workflow TransferToDbGap {
  input {
    String       flowcell_id
    String       sra_bioproject
    String       sra_data_bucket_uri
    String       prod_test = "Production" # Production or Test
    String       ftp_path_prefix

    File         sra_meta_tsv
    File         asession_table
    File?        ncbi_ftp_config_js
  }

  String prefix = "/~{prod_test}/~{ftp_path_prefix}"

  # publish to NCBI SRA
  call sra_tsv_to_xml {
      input:
        meta_submit_tsv  = sra_meta_tsv,
        config_js        = select_first([ncbi_ftp_config_js]),
        bioproject       = sra_bioproject,
        data_bucket_uri  = "~{sra_data_bucket_uri}/~{flowcell_id}"
  }
  call ncbi_sftp_upload as sra_upload {
      input:
        config_js        = select_first([ncbi_ftp_config_js]),
        submission_xml   = sra_tsv_to_xml.submission_xml,
        additional_files = [],
        target_path      = "~{prefix}/sra",
        wait_for         = "1"
  }

  output {
    Array[File] reports = sra_upload.reports_xmls
  }
}

task write_asession_to_table {
    input {
        File sra_meta_tsv
        File asession_table
    }

    command {
      python3 /main.py -s ~{sra_meta_tsv} \
                       -a ~{asession_table}
    }

    output {
        File meta_tsv = "sra_meta_tsv.tsv"
    }

    runtime {
      docker: "schaluvadi/horsefish:submissionV1"
    }
}

task ncbi_sftp_upload {
    input {
        File           submission_xml
        Array[File]    additional_files = []
        File           config_js
        String         target_path

        String         wait_for="1"  # all, disabled, some number

        String         docker = "quay.io/broadinstitute/ncbi-tools:2.10.7.10"
    }

    command <<<
        set -e
        cd /opt/converter
        cp "~{config_js}" src/config.js
        rm -rf files/tests
        cp "~{submission_xml}" files/submission.xml
        if [[ "~{length(additional_files)}" != "0" ]]; then
            cp ~{sep=' ' additional_files} files/
        fi
        MANIFEST=$(ls -1 files | paste -sd,)
        echo "uploading: $MANIFEST to destination ftp folder ~{target_path}"
        echo "Asymmetrik script version: $ASYMMETRIK_REPO_COMMIT"
        node src/main.js --debug \
            --uploadFiles="$MANIFEST" \
            --poll="~{wait_for}" \
            --uploadFolder="~{target_path}"
        ls -alF files reports
        cd -
        cp /opt/converter/reports/*report*.xml .
    >>>

    output {
        Array[File] reports_xmls = glob("*report*.xml")
    }

    runtime {
        cpu:     2
        memory:  "2 GB"
        disks:   "local-disk 100 HDD"
        dx_instance_type: "mem2_ssd1_v2_x2"
        docker:  docker
        maxRetries: 0
    }
}

task sra_tsv_to_xml {
    input {
        File     meta_submit_tsv
        File     config_js
        String   bioproject
        String   data_bucket_uri

        String   docker = "quay.io/broadinstitute/ncbi-tools:2.10.7.10"
    }
    command <<<
        set -e
        cd /opt/converter
        cp "~{config_js}" src/config.js
        cp "~{meta_submit_tsv}" files/
        echo "Asymmetrik script version: $ASYMMETRIK_REPO_COMMIT"
        node src/main.js --debug \
            -i=$(basename "~{meta_submit_tsv}") \
            --submissionType=sra \
            --bioproject="~{bioproject}" \
            --submissionFileLoc="~{data_bucket_uri}" \
            --runTestMode=true
        cd -
        cp "/opt/converter/files/~{basename(meta_submit_tsv, '.tsv')}-submission.xml" .
    >>>
    output {
        File   submission_xml = "~{basename(meta_submit_tsv, '.tsv')}-submission.xml"
    }
    runtime {
        cpu:     1
        memory:  "2 GB"
        disks:   "local-disk 50 HDD"
        dx_instance_type: "mem2_ssd1_v2_x2"
        docker:  docker
        maxRetries: 2
    }
}

task upload_file_