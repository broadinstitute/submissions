import os

def encrypt_file(aggregation_path, crypt4gh_encryption_key):
    output_file = f'encrypted_{file_path}.c4gh'
    command = f'crypt4gh encrypt --recipient_pk {crypt4gh_encryption_key} < {aggregation_path} > {output_file}'
    print(f"command {command}")
    res = subprocess.run(command, capture_output=True, shell=True)
    print(f"res {res}")
    if res.stderr:
        raise RuntimeError(res.stderr.decode())
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="This script will encrypt the given data file using crypt4gh"
    )
    parser.add_argument(
        "-aggregation_path",
        required=True,
        help="The file to encrypt"
    )
    parser.add_argument(
        "-crypt4gh_encryption_key",
        required=True,
        help="The key supplied by ega"
    )
    args = parser.parse_args()

    encrypt_file(args.aggregation_path, args.crypt4gh_encryption_key)