#!/usr/bin/python3


import os
import sys
import json
from opensearchpy import OpenSearch
from argparse import ArgumentParser, BooleanOptionalAction


def __read_jsons(dir):
    licenses = []
    for filename in os.listdir(dir):
        filepath = f"{dir}/{filename}"
        if os.path.isfile(filepath):
            with open(filepath, "r") as jsonFile:
                try:
                    licenses.append(json.load(jsonFile))
                except Exception:
                    print(f"Bad json file '{filepath}'", file=sys.stderr)
    return licenses


def main(ip, port, login, token, backup, create_index):
    client = OpenSearch(
        hosts = [{'host': ip, 'port': port}],
        http_auth = (login, token),
        use_ssl = True,
        verify_certs = False,
        ssl_show_warn = False
    )

    index_name = "licenses"
    index_body = {
        "settings": {
            "index": {
                "number_of_shards": 4
            },
        },
        "mappings": {
            "properties": {
                "key": {
                    "type": "keyword"
                },
                "name": {
                    "type": "keyword"
                },
                "url": {
                    "type": "keyword"
                },
                "spdx_id": {
                    "type": "keyword"
                },
                "node_id": {
                    "type": "keyword"
                }
            }
        }
    }

    if create_index:
        response = client.indices.create(index_name, body=index_body)
        print(f"Creating index: {response}")

    parent_dir = f"{backup}/licenses/"
    jsons = __read_jsons(parent_dir)
    for jsonDoc in jsons:
        id = jsonDoc["key"]
        response = client.index(
            index = index_name,
            body = jsonDoc,
            id = id,
            refresh = False
        )
        print(f"Adding document: {response}")
        print(response)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="opensearch_langs_uploader.py",
        description="Module to upload languages data to OpenSearch")
    parser.add_argument("-b", "--backup", type=str, help="Backup directory")
    parser.add_argument("-i", "--ip", type=str, help="OpenSearch IP")
    parser.add_argument("-p", "--port", type=str, help="OpenSearch port")
    parser.add_argument("-l", "--login", type=str, help="OpenSearch login")
    parser.add_argument("-t", "--token", type=str, help="OpenSearch token")
    parser.add_argument("-c", "--create", action=BooleanOptionalAction, default=False, help="Create index or not")
    args = parser.parse_args()

    main(args.ip, args.port, args.login, args.token, args.backup, args.create)
