from infra.git.git_wrapper import GitWrapper
import requests

class GitHubWrapper(GitWrapper):

    def __init__(self, git_url, git_token):
        self.git_url = git_url
        self.git_token = git_token

    def reopen_merge_request_thread(self, id_project, id_merge_request, id_thread, msg_warning):
        pass

    def get_http_url_by_project_id(self, id_project):
        pass

    def get_id_project_source_by_id_project_target(self, id_project_target, id_merge_request):
        return id_project_target

    def get_changes_by_merge(self, id_merge_request, id_project):
        pass

    def get_merge_request(self, id_merge_request, id_project):
        owner, repo = id_project.split("/")
        url = f"{self.git_url}/repos/{owner}/{repo}/pulls/{id_merge_request}"
        headers = {
            "Authorization": f"token {self.git_token}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        data_head = data['head']

        return {
            "target_branch": data['base']['ref'],
            "source_branch": data_head['ref'],
            "labels": data['labels'],
            "title": data['title'],
            "assignee": data['assignee']['url'],
            "author": {
                "username": data['user']['login']
            },
            "web_url": data['url'],
            "created_at": data['created_at'],
            "last_commit_id": data_head['sha'],
        }


    def get_commits(self, merge_request):
        pass

    def clone_repo(self, url, branch, path):
        pass

    def get_threads_by_merge_request(self, id_project, id_merge_request):
        return []

    def resolve_merge_request_thread(self, id_thread, id_project, merge_request_id):
        pass

    def create_merge_request_thread(self, comment, id_project, id_merge_request, position, merge_request):
        owner, repo = id_project.split('/')
        headers = {
            "Authorization": f"token {self.git_token}",
            "Accept": "application/vnd.github+json"
        }

        if position is None:
            url = f"{self.git_url}/repos/{owner}/{repo}/pulls/{id_merge_request}/reviews"
        
            payload = {
                "body": comment,
                "event": "REQUEST_CHANGES"
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()


        url = f"{self.git_url}/repos/{owner}/{repo}/pulls/{id_merge_request}/comments"

        payload = {
            "body": comment,
            "commit_id": merge_request['last_commit_id'],
            "path": position['path'],
            "side": "RIGHT",
            "line": position['line']
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


    def get_versions_by_merge_request(self, id_project, id_merge_request):
        pass

    def get_project_by_id_project(self, id_project):
        _, repo = id_project.split("/")
        return {
            "name": repo
        }

    def get_commits_behind(self, id_project_target, branch_target, id_project_source, branch_source):
        pass
