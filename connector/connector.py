import requests
import sqlite3
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
        url = f"{Connector.url_base}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers).json()
        return response


    class SortType(Enum):
        STARS = "stars"
        FORKS = "forks"
        HELP_WANTED_ISSUES = "help-wanted-issues"
        UPDATED = "updated"


    def __search_repos(self, query, page, sort):
        url = f"{Connector.url_base}/search/repositories"
        params = {
            "q": query,
            "sort": sort.value,
            "per_page": 100,
            "page": page
        }
        response = requests.get(url, headers=self.headers).json()
        return response
