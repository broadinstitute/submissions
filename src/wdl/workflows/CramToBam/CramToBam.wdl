version 1.0

workflow CramToBam {

  input {
    File cram_file
    File ref_fasta
    File ref_fasta_index
  }

  parameter_meta {
    ref_fasta: { help: "A FASTA format reference file."}
    ref_fasta_indx: { help: "A FASTA index file to speed up conversion."}
    cram_file: { help: "The input CRAM file to be convereted."}
  }

  call CramToBamConversion {
    input:
      ref_fasta = ref_fasta,
      ref_fasta_index = ref_fasta_index,
      cram_file = cram_file
  }

  output {
    File output_bam = CramToBamConversion.output_bam
    File output_bam_index = CramToBamConversion.output_bam_index
    String output_bam_md5 = CramToBamConversion.output_bam_md5
    String output_bam_size = CramToBamConversion.output_bam_size
  }
}

task CramToBamConversion {
  input {
    File ref_fasta
    File ref_fasta_index
    File cram_file
  }

  parameter_meta {
    ref_fasta: { help: "A FASTA format reference file."}
    cram_file: { help: "The input CRAM file to be convereted."}
  }

  Int cram_size = ceil(size(cram_file, "GiB"))
  Int disk_size = (cram_size * 3) + ceil(size(ref_fasta, "GiB")) + 30

  String output_bam_basename = basename(cram_file, ".cram")

  command <<<
    set -eo pipefail

    # -h: Include the header in the outputs
    # -b: Output in the BAM format
    # -T: A FASTA format reference FILE, the index of the reference is optional
    # -o: Output to FILE [stdout]
    # -@: Number of BAM compression threads to use in addition to main thread [0]

    # cram->bam
    samtools view -h -b -T ~{ref_fasta} ~{cram_file} -o ~{output_bam_basename}.bam -@ 8

    # Index the bam
    samtools index -b ~{output_bam_basename}.bam
    mv ~{output_bam_basename}.bam.bai ~{output_bam_basename}.bai

    # Calculate the md5 of the bam
    md5sum ~{output_bam_basename}.bam | awk '{print $1}' > ~{output_bam_basename}.md5

    # Calculate the byte size of the bam. This must be done in bash because WDL Ints overflow
    stat --format="%s" ~{output_bam_basename}.bam > ~{output_bam_basename}.size
  >>>

  runtime {
    cpu: 8
    memory: "30 GiB"
    disks: "local-disk ~{disk_size} HDD"
  }

  output {
    File output_bam = "~{output_bam_basename}.bam"
    File output_bam_index = "~{output_bam_basename}.bai"
    String output_bam_md5 = read_string("~{output_bam_basename}.md5")
    String output_bam_size = read_string("~{output_bam_basename}.size")
  }
}
