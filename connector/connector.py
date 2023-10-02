#!/usr/bin/python3


import requests
import os
import json
import shutil
import string
import time
import sys
import base64
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
        self.repos_dir = f"{backup_dir}/repos/"
        if not os.path.exists(self.repos_dir):
            os.makedirs(self.repos_dir)
        self.langs_dir = f"{backup_dir}/langs/"
        if not os.path.exists(self.langs_dir):
            os.makedirs(self.langs_dir)
        self.licenses_dir = f"{backup_dir}/licenses/"
        if not os.path.exists(self.licenses_dir):
            os.makedirs(self.licenses_dir)

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
        os.system(f"{self.cloc_path} {self.tmp_dir} --timeout {self.cloc_timeout} --json > {cloc_json}")
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
        # TODO: переделать на ElasticSearch
        return os.path.exists(f"{self.repos_dir}/{owner}/{repo}.json")


    def __license_already_added(self, key):
        # TODO: переделать на ElasticSearch
        return os.path.exists(f"{self.licenses_dir}/{key}.json")


    def __language_already_added(self, name):
        # TODO: переделать на ElasticSearch
        return os.path.exists(f"{self.langs_dir}/{base64.urlsafe_b64encode(name.encode('ascii'))}.json")


    def __add_repo(self, info):
        owner = info["owner"]["login"]
        repo = info["name"]
        owner_dir = f"{self.repos_dir}/{owner}"
        if not os.path.exists(owner_dir):
            os.makedirs(owner_dir)

        if self.__repo_already_added(owner, repo):
            return

        clone_url = info["clone_url"]
        languages = self.__analyze_repo_content(clone_url)
        for lang in languages.keys():
            if self.__language_already_added(lang):
                continue
            langJson = json.dumps({
                "name": lang,
                "type": "GPL"
            })
            # TODO: добавить язык в ElasticSearch
            with open(f"{self.langs_dir}/{base64.urlsafe_b64encode(lang.encode('ascii'))}.json", 'w') as jsonFile:
                jsonFile.write(langJson)

        license = info["license"]
        if license and not self.__license_already_added(license["key"]):
            licenseJson = json.dumps(license)
            # TODO: добавить лицензию в ElasticSearch
            with open(f"{self.licenses_dir}/{license['key']}.json", 'w') as jsonFile:
                jsonFile.write(licenseJson)

        res = json.dumps({
            "owner": owner,
            "repo": repo,
            "full_name": info["full_name"],
            "url": info["html_url"],
            "clone_url": clone_url,
            "size": info["size"],
            "forks": info["forks_count"],
            "stargazers": info["stargazers_count"],
            "watchers": info["watchers_count"],
            "pushed_at": info["updated_at"],
            "created_at": info["updated_at"],
            "updated_at": info["stargazers_count"],
            "license_key": license["key"] if license else "No license",
            "language": info["language"],
            "languages": languages
        })

        # TODO: добавить репозиторий в ElasticSearch

        with open(f"{owner_dir}/{repo}.json", 'w') as jsonFile:
            jsonFile.write(res)

        self.counter += 1
        if 0 == self.counter % 10:
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
