version 1.0

import "./read_struct.wdl"

workflow PushReadGroups {
  input {
    String read_group_id
    String experiment_name
    String flow_cell_barcode
    String instrument_model
    String library_name
    String library_preperation_kit_catalog_number
    String library_preperation_kit_name
    String library_preperation_kit_vendor
    String library_preperation_kit_version
    String library_selection
    String library_strand
    String library_strategy
    String multiplex_barcode
    String platform
    String read_group_name
    String reference_sequence
    String sequencing_center
    String sequencing_date
    String target_capture_kit
    String type
    Int lane_number
    Int read_length
    Int reference_sequence_version
    Boolean is_paired_end
    Boolean includes_spike_ins
    Boolean to_trim_adapter_sequence

    String program
    String project
    String workspace_name
    String workspace_project
  }

  call PushReadGroupFile {
    input:
      read_group_id = read_group_id,
      experiment_name = experiment_name,
      flow_cell_barcode = flow_cell_barcode,
      instrument_model = instrument_model,
      library_name = library_name,
      library_preperation_kit_catalog_number = library_preperation_kit_cata
      library_preperation_kit_name = library_preperation_kit_name,
      library_preperation_kit_vendor = library_preperation_kit_vendor,
      library_preperation_kit_version = library_preperation_kit_version,
      library_selection = library_selection,
      library_strand = library_strand,
      library_strategy = library_strategy,
      multiplex_barcode = multiplex_barcode,
      platform = platform,
      read_group_name = read_group_name,
      reference_sequence = reference_sequence,
      sequencing_center = sequencing_center,
      sequencing_date = sequencing_date,
      target_capture_kit = target_capture_kit,
      type = type,
      lane_number = lane_number,
      read_length = read_length,
      reference_sequence_version = reference_sequence_version,
      is_paired_end = is_paired_end,
      includes_spike_ins = includes_spike_ins,
      to_trim_adapter_sequence = to_trim_adapter_sequence,
      program = program,
      project = project,
      workspace_name = workspace_name,
      workspace_project = workspace_project
  }

  output {}
}

task PushReadGroupFile {
    input {
        String read_group_id
        String experiment_name
        String flow_cell_barcode
        String instrument_model
        String library_name
        String library_preperation_kit_catalog_number
        String library_preperation_kit_name
        String library_preperation_kit_vendor
        String library_preperation_kit_version
        String library_selection
        String library_strand
        String library_strategy
        String multiplex_barcode
        String platform
        String read_group_name
        String reference_sequence
        String sequencing_center
        String sequencing_date
        String target_capture_kit
        String type
        Int lane_number
        Int read_length
        Int reference_sequence_version
        Boolean is_paired_end
        Boolean includes_spike_ins
        Boolean to_trim_adapter_sequence

        String program
        String project
        String workspace_name
        String workspace_project
    }

    Read_group read_group = {
        "read_group_id" = read_group_id,
        "experiment_name" = experiment_name,
        "flow_cell_barcode" = flow_cell_barcode,
        "instrument_model" = instrument_model,
        "library_name" = library_name,
        "library_preperation_kit_catalog_number" = library_preperation_kit_catalog_number,
        "library_preperation_kit_name" = library_preperation_kit_name,
        "library_preperation_kit_vendor" = library_preperation_kit_vendor,
        "library_preperation_kit_version" = library_preperation_kit_version,
        "library_selection" = library_selection,
        "library_strand" = library_strand,
        "library_strategy" = library_strategy,
        "multiplex_barcode" = multiplex_barcode,
        "platform" = platform,
        "read_group_name" = read_group_name,
        "reference_sequence" = reference_sequence,
        "sequencing_center" = sequencing_center,
        "sequencing_date" = sequencing_date,
        "target_capture_kit" = target_capture_kit,
        "type" = type,
        "lane_number" = lane_number,
        "read_length" = read_length,
        "reference_sequence_version" = reference_sequence_version,
        "is_paired_end" = is_paired_end,
        "includes_spike_ins" = includes_spike_ins,
        "to_trim_adapter_sequence" = to_trim_adapter_sequence
    }

    command {
        python3 /src/scripts/upload_read_json.py -w ~{workspace_name} \
                                                      -p ~{workspace_project} \
                                                      -r ~{write_json(read_group)}
    }
    
    runtime {
        docker: "schaluvadi/horsefish:submissionV1",
        preemptible: 1
    }

    output {}
}