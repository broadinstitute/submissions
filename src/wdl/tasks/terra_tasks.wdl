version 1.0

task CreateDbgapXmlFiles {
    input {
        String sample_id
        String workspace_name
        String billing_project
        String md5
        File? monitoring_script
        File? read_group_metadata_json
        Int aggregation_version
        String phs_id
        String data_type
    }
    Int disk_size = 32

    command {
        # if the WDL/task contains a monitoring script as input
        set -eo pipefail
        if [ ! -z "~{monitoring_script}" ]; then
            chmod a+x ~{monitoring_script}
            ~{monitoring_script} > monitoring.log &
        else
            echo "No monitoring script given as input" > monitoring.log &
        fi

        mkdir /cromwell_root/xml

        if [ ! -z "~{read_group_metadata_json}" ]; then
            python3 /src/scripts/dbgap/create_dbgap_xml_files.py --sample_id ~{sample_id} \
                                                      --md5 ~{md5} \
                                                      --workspace_name ~{workspace_name} \
                                                      --billing_project ~{billing_project} \
                                                      --aggregation_version ~{aggregation_version} \
                                                      --phs_id ~{phs_id} \
                                                      --data_type ~{data_type} \
                                                      --read_group_metadata_json ~{read_group_metadata_json}
        else
            python3 /src/scripts/dbgap/create_dbgap_xml_files.py --sample_id ~{sample_id} \
                                                      --md5 ~{md5} \
                                                      --workspace_name ~{workspace_name} \
                                                      --billing_project ~{billing_project} \
                                                      --aggregation_version ~{aggregation_version} \
                                                      --phs_id ~{phs_id} \
                                                      --data_type ~{data_type}
        fi

        cd /cromwell_root/xml
        ls
        tar czf xml_files.tgz *.xml
        mv xml_files.tgz /cromwell_root
    }

    runtime {
      memory: "32 GB"
      docker: "schaluvadi/horsefish:submissionV2GDC"
      cpu: 4
      disks: "local-disk " + disk_size + " HDD"
    }

    output {
        File xml_tar = "xml_files.tgz"
    }
}

task CreateValidationStatusTable {
    input {
        # values to update to data model
        String sample_id
        String file_state
        String state
    }

    parameter_meta {
        file_state: "State of file from transferBamFile."
        state: "state of the metadata upload"
    }

    command {
        set -eo pipefail
        # write header to file
        echo -e "entity:sample_id\tfile_state\tstate" \
        > sample_metadata.tsv

        # write metadata values to row in tsv file
        echo -e "~{sample_id}\t~{file_state}\t~{state}" \
        >> sample_metadata.tsv
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        File load_tsv = "sample_metadata.tsv"
    }
}

task verifyGDCRegistration {
    input {
        String program
        String project
        String sample_alias
        String gdc_token
    }

    command {
        set -eo pipefail
        python3 /src/scripts/gdc/verify_registration.py --program ~{program} \
                                                        --project ~{project} \
                                                        --sample_alias ~{sample_alias} \
                                                        --token ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV2GDC"
        preemptible: 1
    }

    output {
        Boolean registration_status = read_string(stdout()) == "true"
    }
}

task CreateTableLoadFile {
    input {
        # values to update to data model
        String sample_id
        String uuid
        String file_state
        String state 
        String registration_status
        File read_json_file
    }

    parameter_meta {
        uuid: "The UUID/sra_id value returned from GDC at the finish of submitMetadataGDC."
        file_state: "State of file from transferBamFile."
        state: "State of file from transferBamFile."
        registration_status: "Registration status returned from verifyRegistration."
        read_json_file: "JSON file which has all read groups for the given sample"
    }

    command {
        set -eo pipefail
        # write header to file
        echo -e "entity:sample_id\tfile_state\tstate\tregistration_status\tuuid\tread_groups" \
        > sample_metadata.tsv

        # write metadata values to row in tsv file
        echo -e "~{sample_id}\t~{file_state}\t~{state}\t~{registration_status}\t~{uuid}\t~{read_json_file}" \
        >> sample_metadata.tsv
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        File load_tsv = "sample_metadata.tsv"
    }
}

task DeleteFileFromWorkspace {
    input {
        File aggregation_path
    }

    command {
        set -eo pipefail
        gsutil rm -a ~{aggregation_path}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV1"
    }
}

task UpsertMetadataToDataModel {
    input {
        # workspace details
        String workspace_name
        String workspace_project
    
        # load file with sample metadata to ingest to table
        File   tsv
    }

    parameter_meta {
        workspace_name: "Name of the workspace to which WDL should push the additional sample metadata."
        workspace_project: "Namespace/project of workspace to which WDL should push the additional sample metadata."
        tsv: "Load tsv file formatted in the Terra required format to update the sample table."
    }

    command {
        set -eo pipefail
        python3 /src/scripts/batch_upsert_entities.py -w ~{workspace_name} \
                                                      -p ~{workspace_project} \
                                                      -t ~{tsv}
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        File ingest_logs = stdout()
    }
}

task GetMetadata {
  input {
    String bam_file
  }

  Int bam_size = ceil(size(bam_file, "GiB"))
  Int disk_size = bam_size * 2

  String output_bam_basename = basename(bam_file, ".bam")

  command <<<
    set -eo pipefail
    gsutil -m {file_path}

    # Calculate the md5 of the bam
    md5sum ~{bam_file} | awk '{print $1}' > ~{output_bam_basename}.md5

    # Calculate the byte size of the bam. This must be done in bash because WDL Ints overflow
    stat --format="%s" ~{bam_file} > ~{output_bam_basename}.size
  >>>

  runtime {
    memory: "7.5 GB"
    docker: "schaluvadi/horsefish:submissionV2GDC"
    cpu: 2
    preemptible: 3
    disks: "local-disk " + disk_size + " HDD"
  }

  output {
    File output_bam = bam_file
    String output_bam_md5 = read_string("~{output_bam_basename}.md5")
    String output_bam_size = read_string("~{output_bam_basename}.size")
  }
}

task addReadsField {
    input {
        # workspace details
        String workspace_name
        String workspace_project
        String sample_alias
        String gdc_token
        String project
        String program
        File? read_group_metadata_json
    }

    command {
        set -eo pipefail

        if [ ! -z "~{read_group_metadata_json}" ]; then
            python3 /src/scripts/gdc/extract_reads_data.py --workspace_name ~{workspace_name} \
                                                      --billing_project ~{workspace_project} \
                                                      --sample_alias ~{sample_alias} \
                                                      --token ~{gdc_token} \
                                                      --project ~{project} \
                                                      --program ~{program} \
                                                      --read_group_metadata_json ~{read_group_metadata_json}
        else
            python3 /src/scripts/gdc/extract_reads_data.py --workspace_name ~{workspace_name} \
                                                      --billing_project ~{workspace_project} \
                                                      --sample_alias ~{sample_alias} \
                                                      --token ~{gdc_token} \
                                                      --project ~{project} \
                                                      --program ~{program}

        fi
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        String reads_json = read_string("reads.json")
    }
}

task ValidateFileStatus {
    input {
        String program
        String project
        String sample_alias
        String agg_project
        String data_type
        String gdc_token
        Boolean previous_task
    }

    command {
        set -eo pipefail
        python3 /src/scripts/gdc/validate_gdc_file_status.py -program ~{program} \
                                                -project ~{project} \
                                                -sample_alias ~{sample_alias} \
                                                -aggregation_project ~{agg_project} \
                                                -data_type ~{data_type} \
                                                -token ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV2GDC"
        preemptible: 1
    }

    output {
        String file_state = read_lines("file_state.txt")[0]
        String state = read_lines("file_state.txt")[1]
    }
}