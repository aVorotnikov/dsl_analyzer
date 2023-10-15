#!/usr/bin/python3


from csv import DictReader
from opensearchpy import OpenSearch
from argparse import ArgumentParser, BooleanOptionalAction


def main(ip, port, login, token, csv, create_index):
    client = OpenSearch(
        hosts = [{'host': ip, 'port': port}],
        http_auth = (login, token),
        use_ssl = True,
        verify_certs = False,
        ssl_show_warn = False
    )

    index_name = "langs"
    index_body = {
        "settings": {
            "index": {
                "number_of_shards": 4
            },
        },
        "mappings": {
            "properties": {
                "name": {
                    "type": "text"
                },
                "type": {
                    "type": "text"
                }
            }
        }
    }

    if create_index:
        response = client.indices.create(index_name, body=index_body)
        print(f"Creating index: {response}")

    with open(csv, 'r') as csv_file:
        reader = DictReader(csv_file)
        for row in reader:
            id = row["name"]
            response = client.index(
                index = index_name,
                body = row,
                id = id,
                refresh = False
            )
            print(f"Adding document: {response}")
            print(response)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="opensearch_langs_uploader.py",
        description="Module to upload languages data to OpenSearch")
    parser.add_argument("-s", "--csv", type=str, help="CSV file")
    parser.add_argument("-i", "--ip", type=str, help="OpenSearch IP")
    parser.add_argument("-p", "--port", type=str, help="OpenSearch port")
    parser.add_argument("-l", "--login", type=str, help="OpenSearch login")
    parser.add_argument("-t", "--token", type=str, help="OpenSearch token")
    parser.add_argument("-c", "--create", action=BooleanOptionalAction, default=False, help="Create index or not")
    args = parser.parse_args()

    main(args.ip, args.port, args.login, args.token, args.csv, args.create)
