#!/usr/bin/python3


from argparse import ArgumentParser
import os
from csv import DictReader


def unpack_repos(csv, dir):
    with open(csv, "r") as csv_file:
        reader = DictReader(csv_file)
        for row in reader:
            owner_dir = f"{dir}/{row['dir']}"
            if not os.path.exists(owner_dir):
                os.makedirs(owner_dir)
            json_path = f"{owner_dir}/{row['file']}"
            if os.path.exists(json_path):
                continue
            with open(json_path, "w") as json_file:
                json_file.write(row['json'])


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="pack_repos_to_csv.py",
        description="Unpack repository backup from csv")
    parser.add_argument("-c", "--csv", type=str, help="CSV file")
    parser.add_argument("-d", "--dir", type=str, help="Backup directory")
    args = parser.parse_args()

    repos_dir = f"{args.dir}/repos"
    if not os.path.exists(repos_dir):
        os.makedirs(repos_dir)
    unpack_repos(args.csv, repos_dir)
