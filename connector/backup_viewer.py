from argparse import ArgumentParser
from enum import Enum
import os
import json
import sys
from csv import DictWriter


class BackupType(Enum):
    REPOS = 'repos'
    LANGS = 'langs'
    LICENSES = 'licenses'


    def __str__(self):
        return self.value


def __read_jsons(dir):
    licenses = []
    for filename in os.listdir(dir):
        filepath = f"{dir}/{filename}"
        if os.path.isfile(filepath):
            with open(filepath, 'r') as jsonFile:
                try:
                    licenses.append(json.load(jsonFile))
                except Exception:
                    print(f"Bad json file '{filepath}'", file=sys.stderr)
    return licenses


def __print_jsons_simple(dir, fieldnames=None):
    jsons = __read_jsons(dir)
    if fieldnames is not None:
        fields = fieldnames
    else:
        fields = set()
        for jsonObject in jsons:
            for key in jsonObject.keys():
                fields.add(key)
    writer = DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()
    writer.writerows(jsons)


def print_licenses(dir):
    __print_jsons_simple(f"{dir}/licenses", ["key", "name", "spdx_id", "url", "node_id"])


def print_langs(dir):
    __print_jsons_simple(f"{dir}/langs", ["name", "type"])


def print_repos(dir):
    parent_dir = f"{dir}/repos"
    writer = DictWriter(sys.stdout, extrasaction='ignore', fieldnames=[
        "owner",
        "repo",
        "language",
        "forks",
        "stargazers",
        "watchers",
        "license_key"
    ])
    writer.writeheader()
    for subdir in os.listdir(parent_dir):
        subdirPath = f"{parent_dir}/{subdir}"
        if os.path.isdir(subdirPath):
            jsons = __read_jsons(subdirPath)
            writer.writerows(jsons)


if __name__ == "__main__":
    choicer = {
        BackupType.REPOS: print_repos,
        BackupType.LANGS: print_langs,
        BackupType.LICENSES: print_licenses
    }

    parser = ArgumentParser(
        prog="connector.py",
        description="backup_viewer.py")
    parser.add_argument("-t", "--type", type=BackupType, choices=list(BackupType), help="Data type")
    parser.add_argument("-d", "--dir", type=str, help="Backup directory")
    args = parser.parse_args()

    choicer[args.type](args.dir)
