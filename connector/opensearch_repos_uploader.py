#!/usr/bin/python3


import os
import sys
import json
from csv import DictReader
from opensearchpy import OpenSearch
from argparse import ArgumentParser, BooleanOptionalAction


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


def main(ip, port, login, token, backup, langs_csv, create_index, delete_index):
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
                    "type": "long"
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
                    "type": "date",
                    "format": "date_optional_time"
                },
                "license_key": {
                    "type": "keyword"
                },
                "language": {
                    "type": "keyword"
                },
                "languages": {
                    "properties": {
                        "language": {
                            "properties":
                            {
                                "name": {
                                    "type": "keyword"
                                },
                                "type": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "files": {
                            "type": "integer"
                        },
                        "blank": {
                            "type": "long"
                        },
                        "comment": {
                            "type": "long"
                        },
                        "code": {
                            "type": "long"
                        }
                    }
                }
            }
        }
    }

    if delete_index:
        response = client.indices.delete(index_name)
        print(f"Deleting index: {response}")

    if create_index:
        response = client.indices.create(index_name, body=index_body)
        print(f"Creating index: {response}")

    languageTypes = dict()
    with open(langs_csv, 'r') as csv_file:
        reader = DictReader(csv_file)
        for row in reader:
            languageTypes[row["name"]] = row["type"]

    parent_dir = f"{backup}/repos/"
    repo_count = 0
    for subdir in os.listdir(parent_dir):
        subdirPath = f"{parent_dir}/{subdir}"
        if os.path.isdir(subdirPath):
            jsons = __read_jsons(subdirPath)
            for json_doc in jsons:
                # Check correctness of time fields
                if type(json_doc["updated_at"]) != str:
                    print(f"Ignore document due to time fields: {json_doc['owner']}/{json_doc['repo']}")
                    continue
                # Correct languages data type:
                languagesDict = json_doc["languages"]
                languagesArray = []
                for language, info in languagesDict.items():
                    arrayInfo = info.copy()
                    arrayInfo["language"] = {
                        "name": language,
                        "type": languageTypes[language] if language in languageTypes else "GPL"
                    }
                    languagesArray.append(arrayInfo)
                json_doc["languages"] = languagesArray
                id = json_doc["full_name"]
                response = client.index(
                    index = index_name,
                    body = json_doc,
                    id = id,
                    refresh = False
                )
                print(f"Adding document: {response}")
                repo_count += 1
    print(f"Added repos: {repo_count}")


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="opensearch_repos_uploader.py",
        description="Module to upload repos data to OpenSearch")
    parser.add_argument("-b", "--backup", type=str, help="Backup directory")
    parser.add_argument("-c", "--csv", type=str, help="CSV with languages info")
    parser.add_argument("-i", "--ip", type=str, help="OpenSearch IP")
    parser.add_argument("-p", "--port", type=str, help="OpenSearch port")
    parser.add_argument("-l", "--login", type=str, help="OpenSearch login")
    parser.add_argument("-t", "--token", type=str, help="OpenSearch token")
    parser.add_argument( "--create", action=BooleanOptionalAction, default=False, help="Create index or not")
    parser.add_argument( "--delete", action=BooleanOptionalAction, default=False, help="Delete index or not")
    args = parser.parse_args()

    main(args.ip, args.port, args.login, args.token, args.backup, args.csv, args.create, args.delete)
