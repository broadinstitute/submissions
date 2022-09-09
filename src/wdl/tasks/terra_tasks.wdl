version 1.0

task CreateTableLoadFile {
    input {
        # values to update to data model
        String sample_id
        String uuid
        String file_state
        String state 
        String registration_status
    }

    parameter_meta {
        uuid: "The UUID/sra_id value returned from GDC at the finish of submitMetadataGDC."
        file_state: "State of file from transferBamFile."
        state: "State of file from transferBamFile."
        registration_status: "Registration status returned from verifyRegistration."
    }

    command {
        # write header to file
        echo -e "entity:sample_id\tfile_state\tstate\tregistration_status\tuuid" \
        > sample_metadata.tsv

        # write metadata values to row in tsv file
        echo -e "~{sample_id}\t~{file_state}\t~{state}\t~{registration_status}\t~{uuid}" \
        >> sample_metadata.tsv
    }

    runtime {
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
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        File ingest_logs = stdout()
    }
}

task GetMetadata {
  input {
    File bam_file
  }

  Int bam_size = ceil(size(bam_file, "GiB"))
  Int disk_size = bam_size * 2

  String output_bam_basename = basename(bam_file, ".bam")

  command <<<
    set -eo pipefail

    # Calculate the md5 of the bam
    md5sum ~{bam_file} | awk '{print $1}' > ~{output_bam_basename}.md5

    # Calculate the byte size of the bam. This must be done in bash because WDL Ints overflow
    stat --format="%s" ~{bam_file} > ~{output_bam_basename}.size
  >>>

  runtime {
    cpu: 1
    memory: "3.75 GiB"
    disks: "local-disk ~{disk_size} HDD"
  }

  output {
    File output_bam = bam_file
    String output_bam_md5 = read_string("~{output_bam_basename}.md5")
    String output_bam_size = read_string("~{output_bam_basename}.size")
  }
}