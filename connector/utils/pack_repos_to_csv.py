#!/usr/bin/python3


from argparse import ArgumentParser
import os
import sys
from csv import DictWriter


def print_repos(dir):
    writer = DictWriter(sys.stdout, fieldnames=["dir", "file", "json"])
    writer.writeheader()
    for subdir in os.listdir(dir):
        subdirPath = f"{dir}/{subdir}"
        if not os.path.isdir(subdirPath):
            continue
        for file in os.listdir(subdirPath):
            filePath = f"{subdirPath}/{file}"
            if not os.path.isfile(filePath):
                continue
            with open(filePath, "r") as jsonFile:
                writer.writerow({
                    "dir": subdir,
                    "file": file,
                    "json": jsonFile.read()
                })


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="pack_repos_to_csv.py",
        description="Pack repository backup to csv")
    parser.add_argument("-d", "--dir", type=str, help="Backup directory")
    args = parser.parse_args()

    print_repos(f"{args.dir}/repos")
