version 1.0

workflow JoinDataTables {
  input {
    File samples_tsv
    File read_groups_tsv
    String workspace_name
    String workspace_project
  }

  call JoinTables {
    input:
        samples_tsv = samples_tsv,
        read_groups_tsv = read_groups_tsv,
        workspace_name = workspace_name,
        workspace_project = workspace_project
  }

  output {}
}

task JoinTables {
    input {
        samples_tsv
        read_groups_tsv
        workspace_name 
        workspace_project
    }

    command {
        python3 /src/scripts/join_data_tables.py -w ~{workspace_name} \
                                                      -p ~{workspace_project} \
                                                      -ts ~{samples_tsv} \
                                                      -tr ~{read_groups_tsv}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV1",
        preemptible: 1
    }

    output {}
}