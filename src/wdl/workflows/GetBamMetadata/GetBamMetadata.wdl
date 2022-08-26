version 1.0

workflow GetBamMetadata {

  input {
    File bam_file
    File bai_file
  }

  call GetMetadata {
    input:
      bam_file = bam_file,
      bai_file = bai_file
  }

  output {
    File output_bam = bam_file
    File output_bam_index = bai_file
    String output_bam_md5 = GetMetadata.output_bam_md5
    String output_bam_size = GetMetadata.output_bam_size
  }
}

task GetMetadata {
  input {
    File bam_file
    File bai_file
  }

  Int bam_size = ceil(size(bam_file, "GiB"))
  Int disk_size = bam_size * 2

  String output_bam_basename = basename(bam_file, ".bam")

  command <<<
    set -eo pipefail

    # Calculate the md5 of the bam
    md5sum ~{bam_file} | awk '{print $1}' > ~{output_bam_basename}.md5

    # Calculate the byte size of the bam. This must be done in bash because WDL Ints overflow
    stat --format="%s" ~{bam_file} > ~{output_bam_basename}.size
  >>>

  runtime {
    cpu: 1
    memory: "3.75 GiB"
    disks: "local-disk ~{disk_size} HDD"
  }

  output {
    File output_bam = bam_file
    File output_bam_index = bai_file
    String output_bam_md5 = read_string("~{output_bam_basename}.md5")
    String output_bam_size = read_string("~{output_bam_basename}.size")
  }
}