
def uploadReads()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-w', '--workspace_name', required=True, help='name of workspace in which to make changes')
    parser.add_argument('-p', '--project', required=True, help='billing project (namespace) of workspace in which to make changes')
    parser.add_argument('-r', '--read_file', required=True, help='json object that is passed from the wdl')
    args = parser.parse_args()

    createTSV(args.file)