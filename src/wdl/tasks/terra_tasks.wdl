version 1.0

task CreateDbgapXmlFiles {
    input {
        String sample_id
        String workspace_name
        String billing_project
    }
    Int disk_size = 15

    command {
        python3 /src/scripts/create_dbgap_xml_files.py -w ~{workspace_name} \
                                                      -p ~{billing_project} \
                                                      -s ~{sample_id}
    }

    runtime {
      memory: "12 GB"
      docker: "schaluvadi/horsefish:submissionV2GDC"
      cpu: 4
      disks: "local-disk " + disk_size + " HDD"
    }

    output {
        File xml_tar = "xml_files.tgz"
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
        String sample_id
        String gdc_token
        String project
        String program
        File? monitoring_script
    }

    command {
        python3 /src/scripts/extract_reads_data.py -w ~{workspace_name} \
                                                      -p ~{workspace_project} \
                                                      -s ~{sample_id} \
                                                      -t ~{gdc_token} \
                                                      -pj ~{project} \
                                                      -pg ~{program}
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        String reads_json = read_string("reads.json")
    }
}