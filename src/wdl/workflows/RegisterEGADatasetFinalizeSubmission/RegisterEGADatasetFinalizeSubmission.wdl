version 1.0

workflow RegisterEGADatasetFinalizeSubmission {
    input {
        String submission_accession_id
        String ega_inbox
        String passwords
        String policy_title
        Array[String] library_strategy
        Array[String] run_accession_ids
        String? dataset_title
        String? dataset_description
    }

    call RegisterDatasetFinalizeSubmission {
        input:
            submission_accession_id = submission_accession_id,
            ega_inbox = ega_inbox,
            password = password,
            policy_title = policy_title,
            library_strategy = library_strategy,
            run_accession_ids = run_accession_ids,
            dataset_title = dataset_title,
            dataset_description = dataset_description
    }

}

task RegisterDatasetFinalizeSubmission {
    input {
        String submission_accession_id
        String ega_inbox
        String password
        String policy_title
        Array[String]? library_strategy
        Array[String]? run_accession_ids
        String? dataset_title
        String? dataset_description
    }

    command {
        python3 /src/scripts/ega/register_dataset_and_finalize_submission.py \
            -submission_accession_id ~{submission_accession_id} \
            -user_name ~{ega_inbox} \
            -password ~{password} \
            -policy_title ~{policy_title} \
            -library_strategy ~{library_strategy} \
            -run_accession_ids ~{run_accession_ids} \
            -dataset_title ~{dataset_title} \
            -dataset_description ~{dataset_description} \
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV2GDC"
    }
}