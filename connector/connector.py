import requests
import os
import json
import shutil
import string
import time
from enum import Enum
from elasticsearch import Elasticsearch


class Connector:
    url_base = "https://api.github.com"
    alphabet = string.ascii_letters


    def __init__(self, tmp_dir, backup_dir, cloc_path, git_token, es_endpoint, es_id, es_password) -> None:
        self.tmp_dir = tmp_dir
        self.backup_dir = backup_dir
        self.cloc_path = cloc_path

        self.headers = {
            "accept" : "application/vnd.github+json",
            "Authorization" : f"Bearer {git_token}",
            "X-GitHub-Api-Version" : "2022-11-28"
        }

        self.es_client = Elasticsearch(es_endpoint, api_key=(es_id, es_password))


    def __get_repo_info(self, owner, repo):
        # doc: https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
        url = f"{Connector.url_base}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        while True:
            response = requests.get(url, headers=self.headers)
            if 200 == response.status_code:
                break
            elif 403 == response.status_code:
                wait_time = int(response.headers["X-Ratelimit-Reset"]) - int(time.time())
                print(f"WAITING {wait_time} s")
                time.sleep(wait_time)
        return response.json()


    class SortType(Enum):
        STARS = "stars"
        FORKS = "forks"
        HELP_WANTED_ISSUES = "help-wanted-issues"
        UPDATED = "updated"


    def __search_repos(self, query, page, sort=SortType.STARS):
        # doc: https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-repositories
        url = f"{Connector.url_base}/search/repositories"
        params = {
            "q": query,
            "sort": sort.value,
            "per_page": 100,
            "page": page
        }
        while True:
            response = requests.get(url, headers=self.headers, params=params)
            if 200 == response.status_code:
                break
            elif 403 == response.status_code:
                wait_time = int(response.headers["X-Ratelimit-Reset"]) - int(time.time())
                print(f"WAITING {wait_time} s")
                time.sleep(wait_time)
        return response.json()


    def __analyze_repo(self, clone_url):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        repo_dir = f"{self.tmp_dir}/repo"
        os.makedirs(repo_dir)
        os.system(f"git clone {clone_url} -l {repo_dir}")
        cloc_json = f"{self.tmp_dir}/cloc.json"
        os.system(f"{self.cloc_path} {self.tmp_dir} --json > {cloc_json}")
        with open(cloc_json, 'r') as jsonFile:
            exclude = ["header", "SUM"]
            result = dict()
            languages = json.load(jsonFile)
            for language in languages:
                if language in exclude:
                    continue
                value = languages[language]
                result[language] = {
                    "files": value["nFiles"],
                    "blank ": value["blank"],
                    "comment": value["comment"],
                    "code": value["code"],
                }
        return result
