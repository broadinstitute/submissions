version 1.0

# Print given message to stderr and return an error
task ErrorWithMessage {
  input {
    String message
  }
  command <<<
    >&2 echo "Error: ~{message}"
    exit 1
  >>>

  runtime {
    docker: "us-central1-docker.pkg.dev/operations-portal-427515/submissions/submission_v2:latest"
  }
}
