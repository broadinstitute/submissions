version 1.0

workflow RegisterEGADatasetFinalizeSubmission {

    input {
        String submission_accession_id
        String user_name
        String password
        String policy_title
        String library_strategy
        Array [String] run_accession_ids
        String? dataset_title
        String? dataset_description
    }

}

task RegisterDatasetFinalizeSubmission {
    input {
        String submission_accession_id
        String user_name
        String password
        String policy_title
        String library_strategy
        Array [String] run_accession_ids
        String? dataset_title
        String? dataset_description
    }

    command {
        python3 /src/scripts/ega/register_dataset_and_finalize_submission.py \
            -submission_accession_id ~{submission_accession_id} \
            -user_name ~{user_name} \
            -password ~{password} \
            -policy_title ~{policy_title} \
            -library_strategy ~{library_strategy} \
            -run_accession_ids ~{run_accession_ids} \
            -dataset_title ~{dataset_title} \
            -dataset_description ~{dataset_description} \
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        # TODO what goes here?
    }

}