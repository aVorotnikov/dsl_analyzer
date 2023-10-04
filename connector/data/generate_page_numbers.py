#!/usr/bin/python3


import sys
import requests
import time
import string
from csv import DictWriter
from argparse import ArgumentParser


def __search_repos(query, token):
    # doc: https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-repositories
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "per_page": 100
    }
    headers = {
        "accept" : "application/vnd.github+json",
        "Authorization" : f"Bearer {token}",
        "X-GitHub-Api-Version" : "2022-11-28"
    }
    while True:
        response = requests.get(url, headers=headers, params=params)
        if 200 == response.status_code:
            break
        elif 403 == response.status_code:
            wait_time = 1 + int(response.headers["X-Ratelimit-Reset"]) - int(time.time())
            print(f"WAITING {wait_time} s", file=sys.stderr)
            time.sleep(wait_time)
    return response.json()


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="generate_page_numbers.py",
        description="Generate page numbers for alphabet")
    parser.add_argument("-g", "--token", type=str, help="GitHub token")
    args = parser.parse_args()

    writer = DictWriter(sys.stdout, fieldnames=["query", "number"])
    writer.writeheader()
    for ch in string.ascii_letters:
        writer.writerow({
            "query": ch,
            "number": __search_repos(ch, args.token)["total_count"]})
