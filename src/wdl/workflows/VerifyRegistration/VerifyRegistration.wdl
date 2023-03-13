version 1.0

workflow VerifyRegistration {
  input {
    File gdc_token
    String program
    String project
    String sample_alias
    Boolean dry_run = false
  }

  String token_value = (read_lines(gdc_token))[0]

  call verifyGDCRegistration {
    input:
      program = program,
      project = project,
      gdc_token = token_value,
      sample_alias = sample_alias
  }

  output {
    Boolean registration_status = verifyGDCRegistration.registration_status
  }
}

task verifyGDCRegistration {
    input {
        String program
        String project
        String alias_value
        String sample_alias
        String gdc_token
    }

    command {
        python3 /main.py --program ~{program} \
                        --project ~{project} \
                        --sample_alias ~{sample_alias} \
                        --step "verify_registration" \
                        --token ~{gdc_token}
    }

    runtime {
        docker: "schaluvadi/horsefish:submissionV1",
        preemptible: 1
    }

    output {
        Boolean registration_status = read_boolean("isValid.txt")
    }
}