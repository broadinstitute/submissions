version 1.0

import "../../tasks/terra_tasks.wdl" as tasks

workflow TransferToDbgap {
    input {
        String sample_id
        String workspace_name
        String workspace_project
        String uploadSite
        String uploadPath
        String ascpUser
        File key
        File dataFile
        File md5_file
        File? monitoring_script
    }

    String md5 = (read_lines(md5_file))[0]

    call tasks.CreateDbgapXmlFiles as xml {
        input:
            workspace_name = workspace_name,
            billing_project = workspace_project,
            sample_id = sample_id,
            monitoring_script = monitoring_script,
            md5 = md5
    }

    call ascpFile as transferXml {
        input:
            key = key,
            uploadFile = xml.xml_tar,
            uploadSite = uploadSite,
            uploadPath = uploadPath,
            ascpUser = "asp-bi",
            filename = "~{sample_id}.xml"
    }

    call ascpFile as transferDataFile {
        input:
            key = key,
            uploadFile = dataFile,
            uploadSite = transferXml.site,
            uploadPath = transferXml.path,
            ascpUser = "asp-bi",
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
    Int disk_size = ceil(size(uploadFile, "GiB") * 1.5)

    command {
      set -e
      mkdir upload
      mv ~{key} upload/private.openssh
      mv ~{uploadFile} upload/~{filename}
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
      docker: "schaluvadi/horsefish:submissionAspera"
      cpu: 2
      disks: "local-disk " + disk_size + " HDD"
    }

    output {
        File transferLog = "upload/aspera-scp-transfer.log"
        String site = uploadSite
        String path = uploadPath
    }
}
