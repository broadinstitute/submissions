version 1.0

import "../../tasks/terra_tasks.wdl" as tasks
import "../../utilities/Utilities.wdl" as utils

workflow TransferToDbgap {
    input {
        String aggregation_project
        String collaborator_sample_id
        String data_type
        String workspace_name
        String workspace_project
        String uploadSite
        String uploadPath
        File key
        File dataFile
        File md5_file
        File? monitoring_script
        File? read_group_metadata_json
        Int aggregation_version
        String phs_id
        String sample_id
    }

    String md5 = (read_lines(md5_file))[0]

    if ((data_type != "WGS") && (data_type != "Exome") && (data_type != "RNA")) {
    call utils.ErrorWithMessage as ErrorMessageIncorrectInput {
        input:
            message = "data_type must be either 'WGS', 'Exome', or 'RNA'."
        }
    }

    String ascpUser = "asp-bi"

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

    call ascpFile as transferXml {
        input:
            key = key,
            uploadFile = xml.xml_tar,
            uploadSite = uploadSite,
            uploadPath = uploadPath,
            ascpUser = ascpUser,
            filename = "~{sample_id}.xml"
    }

    call ascpFile as transferDataFile {
        input:
            key = key,
            uploadFile = dataFile,
            uploadSite = transferXml.site,
            uploadPath = transferXml.path,
            ascpUser = ascpUser,
            filename = "~{sample_id}.bam"
    }
}

task ascpFile {
    input {
        File uploadFile
        File key
        String uploadSite
        String uploadPath
        String ascpUser
        String filename
    }
    Int disk_size = ceil(size(uploadFile, "GiB") * 3)

    command {
      set -e
      mkdir upload
      cp ~{key} upload/private.openssh
      cp ~{uploadFile} upload/~{filename}
      pwd
      ascp -k0 -Q -l 500M -i upload/private.openssh -L upload upload/~{filename} ${ascpUser}@${uploadSite}:${uploadPath};
      ERRORS=$(grep "Source file transfers failed" upload/aspera-scp-transfer.log | rev | cut -f 1 -d ' ');
      [[ $ERRORS[*] =~ '!' ]] && echo "An error was detected during aspera upload." && exit 1
      cat upload/aspera-scp-transfer.log
      cd upload
      ls
    }

    runtime {
      memory: "8 GB"
      docker: "us-central1-docker.pkg.dev/operations-portal-427515/submissions/submission_aspera:latest"
      cpu: 2
      disks: "local-disk " + disk_size + " HDD"
    }

    output {
        File transferLog = "upload/aspera-scp-transfer.log"
        String site = uploadSite
        String path = uploadPath
    }
}
