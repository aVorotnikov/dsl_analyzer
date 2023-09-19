import requests
import sqlite3
import os
import csv
from enum import Enum


class Connector:
    url_base = "https://api.github.com/"


    def __init__(self, data_base, repos_dir, cloc_path, token) -> None:
        self.repos_dir = repos_dir
        self.cloc_path = cloc_path

        self.data_base = data_base
        self.connection = sqlite3.connect(data_base)
        self.cursor = self.connection.cursor()

        self.headers = {
            "accept" : "application/vnd.github+json",
            "Authorization" : f"Bearer {token}",
            "X-GitHub-Api-Version" : "2022-11-28"
        }


    def __get_repo_info(self, owner, repo):
        # doc: https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
        url = f"{Connector.url_base}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers).json()
        return response


    class SortType(Enum):
        STARS = "stars"
        FORKS = "forks"
        HELP_WANTED_ISSUES = "help-wanted-issues"
        UPDATED = "updated"


    def __search_repos(self, query, page, sort):
        # doc: https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-repositories
        url = f"{Connector.url_base}/search/repositories"
        params = {
            "q": query,
            "sort": sort.value,
            "per_page": 100,
            "page": page
        }
        response = requests.get(url, headers=self.headers, params=params).json()
        return response


    def __analyze_repo(self, owner, repo, clone_url):
        owner_dir = f"{self.repos_dir}/{owner}"
        if not os.path.exists(owner_dir):
            os.mkdir(owner_dir)
        repo_dir = f"{owner_dir}/{repo}"
        os.system(f"git clone {clone_url} -l {repo_dir}")
        cloc_csv = f"{owner_dir}/{repo}.csv"
        os.system(f"{self.cloc_path} {repo_dir} --csv > {cloc_csv}")
        with open(cloc_csv, 'r') as csvFile:
            result = []
            reader = csv.DictReader(csvFile)
            for row in reader:
                if "SUM" == row["language"]:
                    continue
                result.append(row)
            return result
