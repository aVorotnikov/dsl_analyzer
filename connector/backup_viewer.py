from argparse import ArgumentParser
from enum import Enum
import os
import json
import sys
from csv import DictWriter


class BackupType(Enum):
    REPOS = 'repos'
    LANGS = 'langs'
    LICENCES = 'licenses'


    def __str__(self):
        return self.value


def __read_jsons(dir):
    print(dir)
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


def __print_jsons_simple(dir):
    jsons = __read_jsons(dir)
    fieldnames = set()
    for jsonObject in jsons:
        for key in jsonObject.keys():
            fieldnames.add(key)
    writer = DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(jsons)


def print_licenses(dir):
    __print_jsons_simple(f"{dir}/licences")


def print_langs(dir):
    __print_jsons_simple(f"{dir}/langs")


def print_repos(dir):
    print("No")


if __name__ == "__main__":
    choicer = {
        BackupType.REPOS: print_repos,
        BackupType.LANGS: print_langs,
        BackupType.LICENCES: print_licenses
    }

    parser = ArgumentParser(
        prog="connector.py",
        description="backup_viewer.py")
    parser.add_argument("-t", "--type", type=BackupType, choices=list(BackupType), help="Data type")
    parser.add_argument("-d", "--dir", type=str, help="Backup directory")
    args = parser.parse_args()

    choicer[args.type](args.dir)
