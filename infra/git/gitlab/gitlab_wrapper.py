import os
import shutil
import subprocess

import gitlab
import requests

from infra.git.git_wrapper import GitWrapper


class GitLabWrapper(GitWrapper):

    def __init__(self, git_url, git_token):
        self.git_url = git_url
        self.git_token = git_token
        self.gitlab_api = gitlab.Gitlab(git_url, private_token=git_token)

    def get_http_url_by_project_id(self, id_project):
        return self.gitlab_api.projects.get(id_project).http_url_to_repo

    def get_id_project_source_by_id_project_target(self, id_project_target, id_merge_request):
        return self.gitlab_api.projects.get(id_project_target).mergerequests.get(id_merge_request).source_project_id

    def get_changes_by_merge(self, id_merge_request, id_project):
        merge_request = self.gitlab_api.projects.get(id_project).mergerequests.get(id_merge_request)
        changes = merge_request.changes()['changes']

        for change in changes:
            diff = change['diff']
            change['addedLines'] = self.__parse_diff(diff)

        return changes

    def get_merge_request(self, id_merge_request, id_project):
        return self.gitlab_api.projects.get(id_project).mergerequests.get(id_merge_request)

    def clone_repo(self, url, branch, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.makedirs(path)
        command = ["git", "clone", "-b", branch, url, path]
        subprocess.run(command)

    def get_threads_by_merge_request(self, id_project, id_merge_request):
        merge_request = self.gitlab_api.projects.get(id_project).mergerequests.get(id_merge_request)
        threads = merge_request.discussions.list(
            get_all=True,
        )
        return threads

    def resolve_merge_request_thread(self, id_thread, id_project, merge_request_id):
        merge_request = self.gitlab_api.projects.get(id_project).mergerequests.get(merge_request_id)
        discussions = merge_request.discussions
        discussion = discussions.get(id_thread)
        discussion.resolved = True
        discussion.save()

    def create_merge_request_thread(self, comment, id_project, id_merge_request, position):
        merge_request = self.gitlab_api.projects.get(id_project).mergerequests.get(id_merge_request)

        obj_to_add = {
            'body': comment
        }

        if position is not None:
            obj_to_add['position'] = position

        discussion = merge_request.discussions.create(obj_to_add)

        return discussion

    def get_versions_by_merge_request(self, id_project, id_merge_request):
        url = f'{self.git_url}/api/v4/projects/{id_project}/merge_requests/{id_merge_request}/versions'
        headers = {'PRIVATE-TOKEN': self.git_token}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    def get_project_by_id_project(self, id_project):
        return self.gitlab_api.projects.get(id_project)

    def get_commits_behind(self, id_project_target, branch_target, id_project_source, branch_source):
        # TODO SE FOR DIFERENTE TA DANDO PROBLEMA SE A BRANCH NAO EXISTIR, TALVEZ ESTEJA TROCADO
        if branch_target != branch_source:
            return []

        project = self.gitlab_api.projects.get(id_project_target)
        comparison = project.repository_compare(branch_target, branch_source, from_project_id=id_project_source)
        commits_behind = []

        for commit in comparison['commits']:
            commits_behind.append({
                "id": commit['id'],
                "author_name": commit['author_name'],
                "message": commit['message'],
                "created_at": commit['created_at'],
            })

        return commits_behind

    @staticmethod
    def __parse_diff(diffs):
        added_lines = []
        diffs_line = diffs.split('\n')

        current_line = None

        for diff in diffs_line:
            if not isinstance(diff, str):
                continue

            if diff.startswith('@@'):
                add = diff.index('+')
                add = diff[add:].split(',')
                current_line = int(add[0].replace('+', ''))
                if diff.endswith('@@'):
                    continue
                pos = diff.rindex('@@')
                diff = diff[pos + 2:]
                current_line -= 1

            if diff.startswith('-'):
                continue

            if diff.startswith('+'):
                added_lines.append(current_line)

            if current_line is not None:
                current_line += 1

        return added_lines
