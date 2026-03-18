version 1.0

import "../../tasks/terra_tasks.wdl" as tasks
import "../../utilities/Utilities.wdl" as utils

workflow TransferToDbgap {
    input {
        String aggregation_project
        String data_type
        String workspace_name
        String workspace_project
        String upload_site
        String upload_path
        File data_file
        File md5_file
        Int aggregation_version
        String phs_id
        String sample_id
        Boolean generate_and_upload_xml

        File? monitoring_script
        File? read_group_metadata_json
    }

    String md5 = (read_lines(md5_file))[0]

    if ((data_type != "WGS") && (data_type != "Exome") && (data_type != "RNA") && (data_type != "Targeted-Capture")) {
    call utils.ErrorWithMessage as ErrorMessageIncorrectInput {
        input:
            message = "data_type must be either 'WGS', 'Exome', 'RNA' or 'Targeted-Capture'. "
        }
    }

    String ascp_user = "asp-dbgap"

    if (generate_and_upload_xml) {
        call tasks.CreateDbgapXmlFiles as xml {
            input:
                workspace_name = workspace_name,
                billing_project = workspace_project,
                sample_id = sample_id,
                monitoring_script = monitoring_script,
                md5 = md5,
                read_group_metadata_json = read_group_metadata_json,
                aggregation_version = aggregation_version,
                phs_id = phs_id,
                data_type = data_type
        }

        call AscpFile as TransferXml {
            input:
                data_file = xml.xml_tar,
                upload_site = upload_site,
                upload_path = upload_path,
                ascp_user = ascp_user,
                sample_id = sample_id,
                xml_file = true
        }
    }

    call AscpFile as TransferDataFile {
        input:
            data_file = data_file,
            upload_site = upload_site,
            upload_path = upload_path,
            ascp_user = ascp_user,
            sample_id = sample_id,
            xml_file = false
    }
}

task AscpFile {
    input {
        File data_file
        String upload_site
        String upload_path
        String ascp_user
        String sample_id
        Boolean xml_file
    }
    Int disk_size = ceil(size(data_file, "GiB") * 3)
    String file_ext = sub(basename(data_file), ".*(\\..+)$", "$1")
    String filename = if xml_file then "~{sample_id}.xml" else "~{sample_id}" + file_ext

    command {
      set -e

      mkdir upload
      cp ~{data_file} upload/~{filename}

      export ASPERA_SCP_PASS=743128bf-3bf3-45b5-ab14-4602c67f2950

      ascp -k0 -Q -l 500M \
        -i /home/aspera-user/.aspera/connect/etc/aspera_tokenauth_id_rsa \
        -L upload \
        upload/~{filename} \
        ~{ascp_user}@~{upload_site}:~{upload_path}

      cat upload/aspera-scp-transfer.log
}

    runtime {
      memory: "8 GB"
      docker: "schaluvadi/horsefish:submissionAspera"
      cpu: 2
      disks: "local-disk " + disk_size + " HDD"
    }

    output {
        File transferLog = "upload/aspera-scp-transfer.log"
    }
}
