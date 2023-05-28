import argparse
import os
import sys

from app.processor import workspace, review, publish
from infra.git.gitenum import GitEnum

exit_code_error = -1
exit_code_success = 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--GIT_TYPE", help="Informe ase é GIT_HUB ou GIT_LAB")
    parser.add_argument("--GIT_URL", help="Informe a URL do GIT")
    parser.add_argument("--GIT_USER", help="Informe o usuário")
    parser.add_argument("--GIT_TOKEN", help="Informe o token")
    parser.add_argument("--GIT_PROJECT_ID", help="Informe o id do projeto")
    parser.add_argument("--GIT_MERGE_REQUEST_ID", help="Informe o id do merge request")

    args = parser.parse_args()
    git_enum = GitEnum[args.GIT_TYPE]

    path_resources = os.path.dirname(os.path.abspath(__file__)) + "/../resources"

    path_target, path_source, merge = workspace.setup(
        git_url=args.GIT_URL,
        git_user=args.GIT_USER,
        git_token=args.GIT_TOKEN,
        id_project_target=args.GIT_PROJECT_ID,
        id_merge_request=args.GIT_MERGE_REQUEST_ID,
        git_enum=git_enum,
        path_resources=path_resources,
    )

    comments = review.review(
        path_target=path_target,
        path_source=path_source,
        path_resources=path_resources,
        merge={
            'title': merge.title,
            "project_id": args.GIT_PROJECT_ID,
            "merge_request_id": args.GIT_MERGE_REQUEST_ID,
        }
    )

    publish.publish(
        comments=comments,
        id_project=args.GIT_PROJECT_ID,
        id_merge_request=args.GIT_MERGE_REQUEST_ID,
        git_enum=git_enum,
        git_url=args.GIT_URL,
        git_token=args.GIT_TOKEN,
        git_user=args.GIT_USER,
    )

    if len(comments) > 0:
        exit_code = exit_code_error
    else:
        exit_code = exit_code_success

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
