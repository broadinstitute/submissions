version 1.0

workflow metadataToUUID {
    meta {
        description: "Submit metadata to GDC and return UUID"
    }

    input {
        String program
        String project
        String aggregation_project
        String alias
        String sequence_type
        File   gdcToken
    }

    call submitMetadataToGDC {
        input:
            program = program
            project = project
            aggregation_project = aggregation_project
            alias = alias
            sequence_type = sequence_type
            gdcToken = gdcToken
    }

    output {
        String UUID = submitMetadataToGDC.UUID
    }
}

task submitMetadataToGDC {
    input {
        String program
        String project
        String aggregation_project
        String alias
        String sequence_type
        File gdcToken
    }

    command {
        python3 main.py --program ~{program} \
                        --project ~{project} \
                        --agg_project ~{aggregation_project} \
                        --alias ~{alias} \
                        --sequence_type ~{sequence_type}
    }

    runtime {
        docker: "schaluvadi/horsefish/submissionV1"
    }

    output {
        String UUID = stdout()
    }
}