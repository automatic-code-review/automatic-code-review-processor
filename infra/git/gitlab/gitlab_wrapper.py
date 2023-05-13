import os
import shutil
import subprocess

import gitlab

from infra.git.git_wrapper import GitWrapper


class GitLabWrapper(GitWrapper):

    def __init__(self, git_url, git_token):
        self.gitlab_api = gitlab.Gitlab(git_url, private_token=git_token)

    def get_http_url_by_project_id(self, id_project):
        return self.gitlab_api.projects.get(id_project).http_url_to_repo

    def get_id_project_source_by_id_project_target(self, id_project_target, id_merge_request):
        return self.gitlab_api.projects.get(id_project_target).mergerequests.get(id_merge_request).source_project_id

    def get_changes_by_merge(self, id_merge_request, id_project):
        merge_request = self.gitlab_api.projects.get(id_project).mergerequests.get(id_merge_request)
        return merge_request.changes()['changes']

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
        threads = merge_request.discussions.list()
        return threads

    def resolve_merge_request_thread(self, id_thread, id_project, merge_request_id):
        merge_request = self.gitlab_api.projects.get(id_project).mergerequests.get(merge_request_id)
        discussions = merge_request.discussions
        discussion = discussions.get(id_thread)
        discussion.resolved = True
        discussion.save()

    def create_merge_request_thread(self, comment, id_project, id_merge_request):
        merge_request = self.gitlab_api.projects.get(id_project).mergerequests.get(id_merge_request)
        discussion = merge_request.discussions.create({'body': comment})
        return discussion
