from infra.git import git_wrapper_factory


def publish(comments, id_project, id_merge_request, git_enum, git_url, git_token, git_user):
    print('automatic-code-review::publish - start')

    git = git_wrapper_factory.create(
        git_enum=git_enum,
        git_url=git_url,
        git_token=git_token,
    )

    print('automatic-code-review::publish - get threads')
    threads = git.get_threads_by_merge_request(
        id_project=id_project,
        id_merge_request=id_merge_request,
    )
    qt_thread = len(threads)

    print(f'automatic-code-review::publish - [QT_THREADS] {qt_thread}')

    for thread in threads:
        message_id = None
        note = thread.attributes['notes'][0]

        if not note['author']['username'] == git_user or not note['type'] == 'DiscussionNote':
            continue

        message = note['body']

        parts = message.split('\n')

        if len(parts) > 0:
            part = parts[len(parts) - 1]
            string = "AUTOMATIC CODE REVIEW ISSUE ID ("

            if string not in part:
                continue

            index = part.index(string)
            message_id = part[index + len(string):len(part) - 1]

        if message_id is None:
            continue

        found = False
        for comment in comments:
            if comment['id'] == message_id:
                print(
                    f'automatic-code-review::publish - comment already added '
                    f'[THREAD_ID] {thread.id} '
                    f'[MESSAGE] {message}'
                )
                comment['found'] = True
                found = True
                break

        if not found:
            print(f'automatic-code-review::publish - resolve thread [THREAD_ID] {thread.id} [MESSAGE] {message}')

            git.resolve_merge_request_thread(
                id_thread=thread.id,
                id_project=id_project,
                merge_request_id=id_merge_request,
            )

    for comment in comments:
        if 'found' not in comment or not comment['found']:
            comment_id = comment['id']
            comment_msg = comment['comment']

            comment_final = f"""{comment_msg}

___

AUTOMATIC CODE REVIEW ISSUE ID ({comment_id})"""

            print(f'automatic-code-review::publish add new comment [COMMENT] {comment_final}')

            git.create_merge_request_thread(
                comment=comment_final,
                id_project=id_project,
                id_merge_request=id_merge_request,
            )

    # TODO ADICIONAR OU REMOVER UPVOTED AND APPROVED

    print('automatic-code-review::publish - end')
