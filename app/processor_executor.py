import argparse
import json
import os

from app.processor import workspace, review, publish, webhook
from infra.git import git_wrapper_factory
from infra.git.gitenum import GitEnum

exit_code_error = -1
exit_code_success = 0


def execute():
    parser = argparse.ArgumentParser()
    parser.add_argument("--GIT_TYPE", help="Informe ase é GIT_HUB ou GIT_LAB")
    parser.add_argument("--GIT_URL", help="Informe a URL do GIT")
    parser.add_argument("--GIT_USER", help="Informe o usuário")
    parser.add_argument("--GIT_TOKEN", help="Informe o token")
    parser.add_argument("--GIT_PROJECT_ID", help="Informe o id do projeto target")
    parser.add_argument("--GIT_MERGE_REQUEST_ID", help="Informe o id do merge request")
    parser.add_argument("--STAGE", help="Informe o stage da execucao", default="default")
    parser.add_argument("--SOURCE_PATH", help="Informe o source path, caso o mesmo já exista", default="")
    parser.add_argument("--EXTRA_ARGS", help="Extra args", default="")

    args = parser.parse_args()
    git_enum = GitEnum[args.GIT_TYPE]

    extra_args = __get_extra_argus(args.EXTRA_ARGS)
    print(f'automatic-code-review::execute [EXTRA_ARGUS] {extra_args} ')

    project_target_id = __get_project_target_id(args, git_enum, extra_args)
    path_resources = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../resources")

    with open(path_resources + "/config.json", 'r') as content:
        config = json.load(content)

    path_target, path_source, merge, path_source_v2 = workspace.setup(
        git_url=args.GIT_URL,
        git_user=args.GIT_USER,
        git_token=args.GIT_TOKEN,
        id_project_target=project_target_id,
        id_merge_request=args.GIT_MERGE_REQUEST_ID,
        git_enum=git_enum,
        path_resources=path_resources,
        path_source=args.SOURCE_PATH,
    )

    comments, extensions = review.review(
        path_target=path_target,
        path_source=path_source,
        path_source_v2=path_source_v2,
        path_resources=path_resources,
        merge=merge,
        stage=args.STAGE,
        config_global=config,
    )

    qt_pending_comment, comments_added = publish.publish(
        comments=comments,
        id_project=project_target_id,
        id_merge_request=args.GIT_MERGE_REQUEST_ID,
        git_enum=git_enum,
        git_url=args.GIT_URL,
        git_token=args.GIT_TOKEN,
        git_user=args.GIT_USER,
        extensions=extensions,
    )

    webhook_add_comment = webhook.add_comment(
        workspace_name=config['workspaceName'],
        webhooks=config['webhooks'],
        comments=comments_added,
        merge=merge,
    )

    print(f'automatic-code-review::execute - finish '
          f'[QT_PEDING_COMMENT] {qt_pending_comment} '
          f'[WEBHOOK_ADD_COMMENT] {webhook_add_comment}')

    if qt_pending_comment > 0 or not webhook_add_comment:
        exit_code = exit_code_error
    else:
        exit_code = exit_code_success

    return exit_code


def __get_extra_argus(extra_args):
    extra_args = extra_args.split(";")
    extra_args_final = {}

    for extra_arg in extra_args:
        extra_arg = extra_arg.split("=")
        if len(extra_arg) == 2:
            extra_args_final[extra_arg[0]] = extra_arg[1]

    return extra_args_final


def __get_project_target_id(args, git_enum, extra_args):
    project_id = args.GIT_PROJECT_ID
    is_upstream = 'IS_UPSTREAM' not in extra_args or extra_args['IS_UPSTREAM'] == 'true'

    if is_upstream:
        return project_id

    git = git_wrapper_factory.create(
        git_enum=git_enum,
        git_url=args.GIT_URL,
        git_token=args.GIT_TOKEN,
    )

    project = git.get_project_by_id_project(
        id_project=project_id,
    )

    return project.forked_from_project['id']
