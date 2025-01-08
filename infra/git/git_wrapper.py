from abc import ABC, abstractmethod


class GitWrapper(ABC):

    @abstractmethod
    def get_http_url_by_project_id(self, id_project):
        pass

    @abstractmethod
    def get_id_project_source_by_id_project_target(self, id_project_target, id_merge_request):
        pass

    @abstractmethod
    def get_changes_by_merge(self, id_merge_request, id_project):
        pass

    @abstractmethod
    def get_merge_request(self, id_merge_request, id_project):
        pass

    @abstractmethod
    def get_commits(self, merge_request):
        pass

    @abstractmethod
    def clone_repo(self, url, branch, path):
        pass

    @abstractmethod
    def get_threads_by_merge_request(self, id_project, id_merge_request):
        pass

    @abstractmethod
    def resolve_merge_request_thread(self, id_thread, id_project, merge_request_id):
        pass

    @abstractmethod
    def create_merge_request_thread(self, comment, id_project, id_merge_request, position):
        pass

    @abstractmethod
    def get_versions_by_merge_request(self, id_project, id_merge_request):
        pass

    @abstractmethod
    def get_project_by_id_project(self, id_project):
        pass

    @abstractmethod
    def reopen_merge_request_thread(self, id_project, id_merge_request, id_thread, msg_warning):
        pass

    @abstractmethod
    def get_commits_behind(self, id_project_target, branch_target, id_project_source, branch_source):
        pass
