task CreateSampleMetadataLoadFile {
    input {
        # values to update to data model
        String uuid
        String file_state
        String state 
        String registration_status
    }

    command {
        
        # write header to file
        echo -e "entity:sample_id\tfile_state\tstate\tregistration_status\tuuid" \
        > sample_metadata.tsv

        # write file paths to row in tsv file
        echo -e "~{file_state}\t~{state}\t~{registration_status}\t~{uuid}" \
        >> sample_metadata.tsv
    }

    runtime {
        docker: docker
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

    command {

        python3 /scripts/batch_upsert_entities.py -w ~{workspace_name} \
                                                  -p ~{workspace_project} \
                                                  -f ~{tsv}

    }

    runtime {
        docker: docker
    }

    output {
        File ingest_logs = stdout()
    }
}