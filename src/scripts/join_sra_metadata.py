import pandas

def joinTSVFiles(metadata, telemetryReport):
    """Joins the metadata file and the telemetry report"""

    metaTSV = pandas.read_csv(metadata, , sep='\t')
    telemetryTSV = pandas.read_csv(telemetryReport, , sep='\t')

    joinedTable = pandas.merge(metaTSV, telemetryTSV, how='inner', left_on=["which filed"], right_on=["which field"])

    f = open("/cromwell_root/sra_meta_tsv.tsv", 'w')
    f.write(joinedTable)
    f.close()

    print("Done writing read json to file") 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-a', '--meta', required=True, help='tsv file containing metadata for the sra samples')
    parser.add_argument('-s', '--asession', required=True, help='tsv file containing all of the data from the sra telemetry report')
    args = parser.parse_args()

    joinTSVFiles(args.meta, args.asession)