import argparse
import json
import os

from app.processor import workspace, review, publish, webhook
from infra.git.gitenum import GitEnum

exit_code_error = -1
exit_code_success = 0


def execute():
    parser = argparse.ArgumentParser()
    parser.add_argument("--GIT_TYPE", help="Informe ase é GIT_HUB ou GIT_LAB")
    parser.add_argument("--GIT_URL", help="Informe a URL do GIT")
    parser.add_argument("--GIT_USER", help="Informe o usuário")
    parser.add_argument("--GIT_TOKEN", help="Informe o token")
    parser.add_argument("--GIT_PROJECT_ID", help="Informe o id do projeto")
    parser.add_argument("--GIT_MERGE_REQUEST_ID", help="Informe o id do merge request")
    parser.add_argument("--STAGE", help="Informe o stage da execucao", default="default")
    parser.add_argument("--SOURCE_PATH", help="Informe o source path, caso o mesmo já exista", default="")

    args = parser.parse_args()
    git_enum = GitEnum[args.GIT_TYPE]

    path_resources = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../resources")

    with open(path_resources + "/config.json", 'r') as content:
        config = json.load(content)

    path_target, path_source, merge = workspace.setup(
        git_url=args.GIT_URL,
        git_user=args.GIT_USER,
        git_token=args.GIT_TOKEN,
        id_project_target=args.GIT_PROJECT_ID,
        id_merge_request=args.GIT_MERGE_REQUEST_ID,
        git_enum=git_enum,
        path_resources=path_resources,
        path_source=args.SOURCE_PATH,
    )

    comments = review.review(
        path_target=path_target,
        path_source=path_source,
        path_resources=path_resources,
        merge=merge,
        stage=args.STAGE,
        config_global=config,
    )

    qt_pending_comment, comments_added = publish.publish(
        comments=comments,
        id_project=args.GIT_PROJECT_ID,
        id_merge_request=args.GIT_MERGE_REQUEST_ID,
        git_enum=git_enum,
        git_url=args.GIT_URL,
        git_token=args.GIT_TOKEN,
        git_user=args.GIT_USER,
    )

    webhook_add_comment = webhook.add_comment(webhooks=config['webhooks'], comments=comments_added, merge=merge)

    print(f'automatic-code-review::execute - finish '
          f'[QT_PEDING_COMMENT] {qt_pending_comment} '
          f'[WEBHOOK_ADD_COMMENT] {webhook_add_comment}')

    if qt_pending_comment > 0 or not webhook_add_comment:
        exit_code = exit_code_error
    else:
        exit_code = exit_code_success

    return exit_code
