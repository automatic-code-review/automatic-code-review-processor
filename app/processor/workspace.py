import os

from infra.git import git_wrapper_factory


def setup(
        git_url,
        git_user,
        git_token,
        id_project_target,
        id_merge_request,
        path_resources,
        git_enum,
):
    git = git_wrapper_factory.create(
        git_enum=git_enum,
        git_url=git_url,
        git_token=git_token,
    )

    merge_request = git.get_merge_request(
        id_merge_request=id_merge_request,
        id_project=id_project_target,
    )

    changes = git.get_changes_by_merge(
        id_merge_request=id_merge_request,
        id_project=id_project_target,
    )

    path = path_resources + "/workspace"
    path_target = path + "/repo_target"
    path_source = path + "/repo_source"

    __setup(
        path=path_target,
        changes=changes,
        field='old_path',
        branch=merge_request.target_branch,
        id_project=id_project_target,
        git_user=git_user,
        git_token=git_token,
        git=git,
    )

    __setup(
        path=path_source,
        changes=changes,
        field='new_path',
        branch=merge_request.source_branch,
        id_project=git.get_id_project_source_by_id_project_target(
            id_project_target=id_project_target,
            id_merge_request=id_merge_request,
        ),
        git_user=git_user,
        git_token=git_token,
        git=git,
    )

    return path_target, path_source


def __setup(
        git,
        path,
        changes,
        field,
        branch,
        id_project,
        git_user,
        git_token,
):
    url = __get_http_with_auth(
        url=git.get_http_url_by_project_id(
            id_project=id_project,
        ),
        user=git_user,
        token=git_token,
    )

    git.clone_repo(
        url=url,
        branch=branch,
        path=path,
    )

    __remove_files_not_in_changes(
        path=path,
        changes=changes,
        field=field,
    )

    __remove_empty_dirs(
        path=path,
    )


def __get_http_with_auth(url, user, token):
    separator = "://"
    index = url.index(separator) + len(separator)

    return url[0:index] + f"{user}:{token}@" + url[index:]


def __remove_files_not_in_changes(path, changes, field):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, path)
            found = False
            for change in changes:
                if relative_path == change[field]:
                    found = True
                    break
            if not found:
                os.remove(file_path)


def __remove_empty_dirs(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for dirr in dirs:
            dir_path = os.path.join(root, dirr)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

    for root, dirs, files in os.walk(path, topdown=False):
        if not dirs and not files:
            os.rmdir(root)
