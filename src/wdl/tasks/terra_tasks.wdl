task CreateTableLoadFile {
    input {
        # values to update to data model
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

    parameter_meta {
        workspace_name: "Name of the workspace to which WDL should push the additional sample metadata."
        workspace_project: "Namespace/project of workspace to which WDL should push the additional sample metadata."
        tsv: "Load tsv file formatted in the Terra required format to update the sample table."
    }

    command {
        python3 /src/scripts/batch_upsert_entities.py -w ~{workspace_name} \
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