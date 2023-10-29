#!/usr/bin/python3


import os
import sys
import json
from opensearchpy import OpenSearch
from argparse import ArgumentParser, BooleanOptionalAction


NUMBER_OF_FIELDS = 2000


def __read_jsons(dir):
    repos = []
    for filename in os.listdir(dir):
        filepath = f"{dir}/{filename}"
        if os.path.isfile(filepath):
            with open(filepath, "r") as jsonFile:
                try:
                    repos.append(json.load(jsonFile))
                except Exception:
                    print(f"Bad json file '{filepath}'", file=sys.stderr)
    return repos


def main(ip, port, login, token, backup, create_index):
    client = OpenSearch(
        hosts = [{'host': ip, 'port': port}],
        http_auth = (login, token),
        use_ssl = True,
        verify_certs = False,
        ssl_show_warn = False
    )

    index_name = "repos"
    index_body = {
        "settings": {
            "index": {
                "number_of_shards": 4
            },
        },
        "mappings": {
            "properties": {
                "owner": {
                    "type": "keyword"
                },
                "repo": {
                    "type": "keyword"
                },
                "full_name": {
                    "type": "keyword"
                },
                "url": {
                    "type": "keyword"
                },
                "clone_url": {
                    "type": "keyword"
                },
                "size": {
                    "type": "integer"
                },
                "forks": {
                    "type": "integer"
                },
                "stargazers": {
                    "type": "integer"
                },
                "watchers": {
                    "type": "integer"
                },
                "pushed_at": {
                    "type": "date",
                    "format": "date_optional_time"
                },
                "created_at": {
                    "type": "date",
                    "format": "date_optional_time"
                },
                "updated_at": {
                    "type": "integer"
                },
                "license_key": {
                    "type": "keyword"
                },
                "language": {
                    "type": "keyword"
                },
                "languages": {
                    "type": "object"
                }
            }
        }
    }

    if create_index:
        response = client.indices.create(index_name, body=index_body)
        print(f"Creating index: {response}")
        response = client.indices.put_settings(index=index_name, body={
            "index.mapping.total_fields.limit": NUMBER_OF_FIELDS
        })
        print(f"Putting settings: {response}")

    parent_dir = f"{backup}/repos/"
    for subdir in os.listdir(parent_dir):
            subdirPath = f"{parent_dir}/{subdir}"
            if os.path.isdir(subdirPath):
                jsons = __read_jsons(subdirPath)
                for jsonDoc in jsons:
                    id = jsonDoc["full_name"]
                    response = client.index(
                        index = index_name,
                        body = jsonDoc,
                        id = id,
                        refresh = False
                    )
                    print(f"Adding document: {response}")
                    number += 1


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="opensearch_repos_uploader.py",
        description="Module to upload repos data to OpenSearch")
    parser.add_argument("-b", "--backup", type=str, help="Backup directory")
    parser.add_argument("-i", "--ip", type=str, help="OpenSearch IP")
    parser.add_argument("-p", "--port", type=str, help="OpenSearch port")
    parser.add_argument("-l", "--login", type=str, help="OpenSearch login")
    parser.add_argument("-t", "--token", type=str, help="OpenSearch token")
    parser.add_argument("-c", "--create", action=BooleanOptionalAction, default=False, help="Create index or not")
    args = parser.parse_args()

    main(args.ip, args.port, args.login, args.token, args.backup, args.create)
