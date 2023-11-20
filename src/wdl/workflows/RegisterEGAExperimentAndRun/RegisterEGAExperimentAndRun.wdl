version 1.0

import "../../tasks/terra_tasks.wdl" as terra_tasks

workflow RegisterEGAExperimentAndRun {
    input {
        String workspace_name
        String workspace_project
        String submission_accession_id
        String study_accession_id
        String ega_inbox
        String password
        String illumina_instrument
        String library_layout
        String library_strategy
        String library_source
        String library_selection
        String run_file_type
        String sample_alias
        String sample_id
        String group_library_name
        Float avg_mean_insert_size
        Float avg_standard_deviation
        String sample_material_type
        String construction_protocol
        String aggregation_path
        String aggregation_index_path
        Boolean delete_files = false
    }

    # Check the file status
    call CheckEGAFileValidationStatus {
        input:
            submission_accession_id = submission_accession_id,
            ega_inbox = ega_inbox,
            password = password,
            sample_alias = sample_alias,
            sample_id = sample_id
    }

    # Write the validation status to the Terra data tables
    call terra_tasks.UpsertMetadataToDataModel as upsert_metadata {
        input:
            workspace_name = workspace_name,
            worksapce_project = workspace_project,
            tsv = CheckEGAFileValidationStatus.sample_id_validation_status_tsv
    }

    # Check the validation status and only continue to registering the metadata if the file is valid
    if (CheckEGAFileValidationStatus.validation_status == "validated") {

        call RegisterExperimentAndRun {
            input:
                submission_accession_id = submission_accession_id,
                study_accession_id = study_accession_id,
                ega_inbox = ega_inbox,
                password = password,
                illumina_instrument = illumina_instrument,
                library_layout = library_layout,
                library_strategy = library_strategy,
                library_source = library_source,
                library_selection = library_selection,
                run_file_type = run_file_type,
                sample_alias = sample_alias,
                sample_id = sample_id,
                group_library_name = group_library_name,
                avg_mean_insert_size = avg_mean_insert_size,
                avg_standard_deviation = avg_standard_deviation,
                sample_material_type = sample_material_type,
                construction_protocol = construction_protocol
        }

        call terra_tasks.UpsertMetadataToDataModel {
            input:
                workspace_name = workspace_name,
                worksapce_project = workspace_project,
                tsv = RegisterExperimentAndRun.run_accession_tsv
        }

        # If delete_files is set to true, proceed with deleting the cram/crai/md5 from the Terra bucket
        if (delete_files) {

            call DeleteFileFromBucket {
                input:
                    aggregation_path = aggregation_path,
                    aggregation_index_path = aggregation_index_path
            }

        }

    }

}


task RegisterExperimentAndRun{
    input {
        String submission_accession_id
        String study_accession_id
        String ega_inbox
        String password
        String illumina_instrument
        String library_layout
        String library_strategy
        String library_source
        String library_selection
        String run_file_type
        String sample_alias
        String sample_id
        String group_library_name
        Float avg_mean_insert_size
        Float avg_standard_deviation
        String sample_material_type
        String construction_protocol
    }

    command {
        python3 /src/scripts/ega/register_experiment_and_run_metadata.py \
            -submission_accession_id ~{submission_accession_id} \
            -study_accession_id ~{study_accession_id} \
            -user_name ~{ega_inbox} \
            -password ~{password} \
            -instrument_model ~{illumina_instrument} \
            -library_layout ~{library_layout} \
            -library_strategy ~{library_strategy} \
            -library_source ~{library_source} \
            -library_selection ~{library_selection} \
            -run_file_type ~{run_file_type} \
            -run_file_type ~{run_file_type} \
            -technology ILLUMINA \
            -run_file_type ~{run_file_type} \
            -sample_alias ~{sample_alias} \
            -sample_id ~{sample_id} \
            -library_name ~{group_library_name} \
            -mean_insert_size ~{avg_mean_insert_size} \
            -standard_deviation ~{avg_standard_deviation} \
            -sample_material_type ~{sample_material_type} \
            -construction_protocol ~{construction_protocol} \
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        File run_accession_tsv = "sample_id_and_run_accession_id.tsv"
    }

}

task CheckEGAFileValidationStatus {
    input {
        String submission_accession_id
        String ega_inbox
        String password
        String sample_alias
        String sample_id
    }

    command {
        python3 /src/scripts/ega/check_file_validation_status.py \
            -submission_accession_id ~{submission_accession_id} \
            -user_name ~{ega_inbox} \
            -password ~{password} \
            -sample_alias ~{sample_alias} \
            -sample_id ~{sample_id} \
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV2GDC"
    }

    output {
        String validation_status = read_string("file_validation_status.tsv")
        File sample_id_validation_status_tsv = "sample_id_validation_status.tsv"
    }

}

task DeleteFileFromBucket {
    input {
        String aggregation_path
        String aggregation_index_path
    }

    String aggregation_md5_path  = aggregation_path + ".md5"

    command <<<
        set -eo pipefail
        gsutil rm -a ~{aggregation_path}
        gsutil rm -a ~{aggregation_index_path}
        gsutil rm -a ~{aggregation_md5_path}
    >>>

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV1"
    }

}