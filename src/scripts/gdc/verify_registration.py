import argparse
import json
import logging

from src.services.gdc_api import GdcApiWrapper

logging.basicConfig(
    format="%(levelname)s: %(asctime)s : %(message)s", level=logging.INFO
)


def check_registration(alias, program, project, token):
    response = GdcApiWrapper(program=program, project=project, token=token).get_entity("verify", alias)
    response = json.loads(response.text)

    if response["data"] and response["data"]["aliquot"] and len(response["data"]["aliquot"]) > 0:
        logging.info("true")
    else:
        raise RuntimeError(f"Sample is not registered in GDC. Response - {response}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Verify sample registration in GDC")
    parser.add_argument('-s', '--sample_alias', required=True, help='list of aliases to check registration status')
    parser.add_argument('-t', '--token', required=True, help='Api token to communicate with GDC')
    parser.add_argument('-pg', '--program', required=True, help='GDC program')
    parser.add_argument('-pj', '--project', required=True, help='GDC project')
    args = parser.parse_args()

    check_registration(args.sample_alias, args.program, args.project, args.token)