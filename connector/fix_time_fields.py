#!/usr/bin/python3


import requests
import json
import os
import time
import sys
from argparse import ArgumentParser


class BackupFixer:
    url_base = "https://api.github.com"


    def __init__(self, backup_dir, git_token):
        self.repos_dir = f"{backup_dir}/repos/"
        self.headers = {
            "accept" : "application/vnd.github+json",
            "Authorization" : f"Bearer {git_token}",
            "X-GitHub-Api-Version" : "2022-11-28"
        }
        self.unfound = []


    @staticmethod
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


    def __get_repo_info(self, owner, repo):
        # doc: https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
        url = f"{BackupFixer.url_base}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        while True:
            response = requests.get(url, headers=self.headers)
            if 200 == response.status_code:
                break
            elif 403 == response.status_code:
                wait_time = 1 + int(response.headers["X-Ratelimit-Reset"]) - int(time.time())
                print(f"WAITING {wait_time} s", file=sys.stderr)
                time.sleep(wait_time)
            elif 404 == response.status_code:
                print(f"Failed to find: ({owner}, {repo})")
                self.unfound.append((owner, repo))
                return None
            else:
                print(f"Unexpected error: {response}")
        return response.json()


    def fix(self):
        for subdir in os.listdir(self.repos_dir):
            subdir_path = f"{self.repos_dir}/{subdir}"
            if os.path.isdir(subdir_path):
                jsons = BackupFixer.__read_jsons(subdir_path)
                for json_doc in jsons:
                    if type(json_doc["updated_at"]) == str:
                        print(f"{json_doc['owner']}/{json_doc['repo']} already correct")
                        continue
                    repo_info = self.__get_repo_info(json_doc["owner"], json_doc["repo"])
                    if repo_info is None:
                        continue
                    json_doc["pushed_at"] = repo_info["pushed_at"]
                    json_doc["created_at"] = repo_info["created_at"]
                    json_doc["updated_at"] = repo_info["updated_at"]
                    with open(f"{subdir_path}/{json_doc['repo']}.json", 'w') as jsonFile:
                        jsonFile.write(json.dumps(json_doc))
                    print(f"{json_doc['owner']}/{json_doc['repo']} corrected")
        print(f"Unfound repos: {self.unfound}")


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="fix_time_fields.py",
        description="Fix repos connector data: created_at, pushed_at, updated_at")
    parser.add_argument("-b", "--backup", type=str, help="Backup directory")
    parser.add_argument("-g", "--token", type=str, help="GitHub token")
    args = parser.parse_args()

    fixer = BackupFixer(args.backup, args.token)
    fixer.fix()
