import requests
import os
import json
import shutil
import string
import time
import sys
from enum import Enum
from argparse import ArgumentParser
from elasticsearch import Elasticsearch


class Connector:
    url_base = "https://api.github.com"
    alphabet = string.ascii_letters


    def __init__(self, tmp_dir, backup_dir, cloc_path, git_token,
                 es_id, es_password, es_endpoint, cloc_timeout=60) -> None:
        self.tmp_dir = tmp_dir
        self.backup_dir = backup_dir

        self.cloc_path = cloc_path
        self.cloc_timeout = cloc_timeout

        self.headers = {
            "accept" : "application/vnd.github+json",
            "Authorization" : f"Bearer {git_token}",
            "X-GitHub-Api-Version" : "2022-11-28"
        }

        # self.es_client = Elasticsearch(es_endpoint, api_key=(es_id, es_password))
        self.counter = 0


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
                print(f"WAITING {wait_time} s", file=sys.stderr)
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
                print(f"WAITING {wait_time} s", file=sys.stderr)
                time.sleep(wait_time)
        return response.json()


    def __analyze_repo_content(self, clone_url):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        repo_dir = f"{self.tmp_dir}/repo"
        os.makedirs(repo_dir)
        os.system(f"git clone {clone_url} -l {repo_dir}")
        cloc_json = f"{self.tmp_dir}/cloc.json"
        os.system(f"{self.cloc_path} {self.tmp_dir} --  {self.cloc_timeout} --json > {cloc_json}")
        with open(cloc_json, 'r') as jsonFile:
            exclude = ["header", "SUM"]
            result = dict()
            try:
                languages = json.load(jsonFile)
            except Exception:
                return result
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


    def __repo_already_added(self, owner, repo):
        # TODO: переделать на ElastiSearch
        return os.path.exists(f"{self.backup_dir}/{owner}/{repo}.json")


    def __add_repo(self, info):
        owner = info["owner"]["login"]
        repo = info["name"]
        owner_dir = f"{self.backup_dir}/{owner}"
        if not os.path.exists(owner_dir):
            os.makedirs(owner_dir)

        if self.__repo_already_added(owner, repo):
            return

        clone_url = info["clone_url"]
        languages = self.__analyze_repo_content(clone_url)
        # TODO: проанализировать языки + ElasticSearch

        license = info["license"]
        # TODO: проанализировать лицензия + ElasticSearch

        res = {
            "owner": owner,
            "repo": repo,
            "full_name": info["full_name"],
            "url": info["html_url"],
            "clone_url": clone_url,
            "forks": info["forks_count"],
            "stargazers": info["stargazers_count"],
            "watchers": info["watchers_count"],
            "pushed_at": info["updated_at"],
            "created_at": info["updated_at"],
            "updated_at": info["stargazers_count"],
            "license_key": license["key"] if license else "No license",
            "language": info["language"],
            "languages": languages
        }

        # TODO: добавить в ElasticSearch

        with open(f"{owner_dir}/{repo}.json", 'w') as jsonFile:
            jsonFile.write(json.dumps(res))

        self.counter += 1
        if 0 == self.counter % 100:
            print(f"Analyzed {self.counter} repositories")


    def analyze(self):
        page = 1
        while True:
            for ch in Connector.alphabet:
                print(f"ANALYZING PAGE {page}, LETTER {ch}")
                repos_info = self.__search_repos(ch, page)
                for repo_info in repos_info["items"]:
                    self.__add_repo(repo_info)
            page += 1


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="connector.py",
        description="Connector for GitHub API")
    parser.add_argument("-t", "--tmp", type=str, help="Temporary directory")
    parser.add_argument("-b", "--backup", type=str, help="Backup directory")
    parser.add_argument("-c", "--cloc", type=str, help="Cloc executable path")
    parser.add_argument("-g", "--token", type=str, help="GitHub token")
    parser.add_argument("-i", "--id", type=str, help="ElasticSearch ID")
    parser.add_argument("-p", "--password", type=str, help="ElasticSearch password")
    parser.add_argument("-e", "--es", type=str, help="ElasticSearch entry point")
    parser.add_argument("-o", "--timeout", type=int, default=60, help="Cloc analyzer timeout")
    args = parser.parse_args()

    connector = Connector(args.tmp, args.backup, args.cloc, args.token,
                          args.id, args.password, args.es, args.timeout)
    connector.analyze()
