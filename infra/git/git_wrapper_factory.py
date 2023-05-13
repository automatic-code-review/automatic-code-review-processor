from infra.git.git_wrapper import GitWrapper
from infra.git.gitenum import GitEnum
from infra.git.github.github_wrapper import GitHubWrapper
from infra.git.gitlab.gitlab_wrapper import GitLabWrapper


def create(git_enum, git_url, git_token) -> GitWrapper:
    if git_enum == GitEnum.GIT_LAB:
        return GitLabWrapper(
            git_url=git_url,
            git_token=git_token,
        )

    if git_enum == GitEnum.GIT_HUB:
        return GitHubWrapper(
            git_url=git_url,
            git_token=git_token,
        )
