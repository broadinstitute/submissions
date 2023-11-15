version 1.0

import "../../tasks/terra_tasks.wdl" as terra_tasks

workflow RegisterEGAExperimentAndRun {
    input {
        String workspace_name
        String workspace_project
        String submission_accession_id
        String study_accession_id
        String user_name
        String password
        String instrument_model
        String library_layout
        String library_strategy
        String library_source
        String library_selection
        String run_file_type
        String sample_alias
        String sample_id
        String library_name
        Float mean_insert_size
        Float standard_deviation
        String sample_material_type
        String construction_protocol
    }

    # TODO add the step to check for the file status here and only move on if it's a valid status

    call RegisterExperimentAndRun as register_experiment_and_run {
        input:
            submission_accession_id = submission_accession_id,
            study_accession_id = study_accession_id,
            user_name = user_name,
            password = password,
            instrument_model = instrument_model,
            library_layout = library_layout,
            library_strategy = library_strategy,
            library_source = library_source,
            library_selection = library_selection,
            run_file_type = run_file_type,
            sample_alias = sample_alias,
            sample_id = sample_id,
            library_name = library_name,
            mean_insert_size = mean_insert_size,
            standard_deviation = standard_deviation,
            sample_material_type = sample_material_type,
            construction_protocol = construction_protocol
    }

    call terra_tasks.UpsertMetadataToDataModel as upsert_metadata {
        input:
            workspace_name = workspace_name,
            worksapce_project = workspace_project,
            # TODO is this the correct way to get this file path?
            tsv = "sample_id_and_run_accession_id.tsv"
    }

}


task RegisterExperimentAndRun{
    input {
        String submission_accession_id
        String study_accession_id
        String user_name
        String password
        String instrument_model
        String library_layout
        String library_strategy
        String library_source
        String library_selection
        String run_file_type
        String sample_alias
        String sample_id
        String library_name
        Float mean_insert_size
        Float standard_deviation
        String sample_material_type
        String construction_protocol
    }

    command {
        python3 /src/scripts/ega/register_experiment_and_run_metadata.py \
            -submission_accession_id ~{submission_accession_id} \
            -study_accession_id ~{study_accession_id} \
            -user_name ~{user_name} \
            -password ~{password} \
            -instrument_model ~{instrument_model} \
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
            -library_name ~{library_name} \
            -mean_insert_size ~{mean_insert_size} \
            -standard_deviation ~{standard_deviation} \
            -sample_material_type ~{sample_material_type} \
            -construction_protocol ~{construction_protocol} \
    }

    runtime {
        preemptible: 3
        docker: "schaluvadi/horsefish:submissionV1"
    }

    output {
        # TODO what goes here?
    }

}