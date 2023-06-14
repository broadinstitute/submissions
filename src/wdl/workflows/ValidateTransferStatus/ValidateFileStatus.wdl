version 1.0

workflow VerifyRegistration {
  input {
    File gdc_token
    String program
    String project
    String sample_id
    Boolean delete = false
  }

  String token_value = (read_lines(gdc_token))[0]

  call validateFileStatus {
    input:
      program = program,
      project = project,
      sample_id = sample_id,
      gdc_token = token_value,
      delete = delete
  }

  output {
    Boolean file_state = validateFileStatus.file_state
  }
}

task validateFileStatus {
    input {
        String program
        String project
        String sample_id
        String gdc_token
        Boolean delete
    }

    command {
        python3 /src/scripts/validateFileStatus.py -pg ~{program} \
                                                -pj ~{project} \
                                                -s ~{sample_id} \
                                                -d ~{delete} \
                                                -t ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV2GDC"
        preemptible: 1
    }

    output {
        String file_state = read_boolean("file_state.txt")
    }
}