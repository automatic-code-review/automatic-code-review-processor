from gitlab import GitlabCreateError

from infra.git import git_wrapper_factory


def __verify_resolve_policy(comment, git, id_project, id_merge_request):
    if 'processorArgs' not in comment or 'resolutionPolicy' not in comment['processorArgs']:
        return

    resolved_by = comment['resolvedBy']
    allowed_resolvers = comment['processorArgs']['resolutionPolicy']['allowedResolvers']

    if resolved_by in allowed_resolvers:
        return

    msg_allowed_resolvers = ', '.join(allowed_resolvers)

    print(f'automatic-code-review::publish::verify_resolve_policy '
          f'Comentario foi resolvido por {resolved_by}, porém não é permitido. '
          f'Reabrindo o comentário.'
          f'[ALLOWED_RESOLVERS] {msg_allowed_resolvers} '
          f'[COMENTARIO] {comment["comment"]} ')

    id_thread = comment['idThread']

    msg_warning = f'Comentário foi resolvido por {resolved_by}, porém não é permitido.'

    if len(msg_allowed_resolvers) > 0:
        msg_warning += f' Apenas os usuarios {msg_allowed_resolvers} podem resolver este comentário de forma manual.'

    git.reopen_merge_request_thread(
        id_project=id_project,
        id_merge_request=id_merge_request,
        id_thread=id_thread,
        msg_warning=msg_warning
    )
    comment['resolved'] = False


def publish(comments, id_project, id_merge_request, git_enum, git_url, git_token, git_user, extensions):
    print('automatic-code-review::publish - start')

    git = git_wrapper_factory.create(
        git_enum=git_enum,
        git_url=git_url,
        git_token=git_token,
    )

    print('automatic-code-review::publish - get versions')
    versions = git.get_versions_by_merge_request(
        id_project=id_project,
        id_merge_request=id_merge_request,
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

        if not note['author']['username'] == git_user:
            continue

        if not note['type'] == 'DiscussionNote' and not note['type'] == 'DiffNote':
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
                comment['resolved'] = note['resolved']
                if 'resolved_by' in note and note['resolved_by'] is not None:
                    comment['resolvedBy'] = note['resolved_by']['username']
                comment['idThread'] = thread.id
                found = True
                break

        if not found and not note['resolved']:
            extension = message_id.split(":")[0]
            if extension not in extensions:
                continue

            print(f'automatic-code-review::publish - resolve thread [THREAD_ID] {thread.id} [MESSAGE] {message}')

            git.resolve_merge_request_thread(
                id_thread=thread.id,
                id_project=id_project,
                merge_request_id=id_merge_request,
            )

    qt_pending_comment = 0
    comments_added = []

    for comment in comments:
        if 'resolved' in comment and comment['resolved']:
            __verify_resolve_policy(comment, git, id_project, id_merge_request)

        if 'found' not in comment or not comment['found']:
            qt_pending_comment += 1
            comment_id = comment['id']
            comment_msg = comment['comment']

            comment_final = f"""{comment_msg}

___

AUTOMATIC CODE REVIEW ISSUE ID ({comment_id})"""

            if 'position' in comment:
                position = {
                    "base_sha": versions[0]['base_commit_sha'],
                    "start_sha": versions[0]['start_commit_sha'],
                    "head_sha": versions[0]['head_commit_sha'],
                    "position_type": "text",
                    "new_path": comment['position']['path'],
                    "new_line": comment['position']['startInLine']
                }
            else:
                position = None

            print(f'automatic-code-review::publish add new comment [COMMENT] {comment_final}')

            discussion = __create_discussion(
                comment=comment_final,
                id_project=id_project,
                id_merge_request=id_merge_request,
                position=position,
                git=git,
            )
            comments_added.append({
                'comment': comment_final,
                'type': comment['type'],
                'web_url': "#note_" + str(discussion.attributes['notes'][0]['id']),
                'id': discussion.id
            })
        elif 'resolved' not in comment or not comment['resolved']:
            qt_pending_comment += 1

    # TODO ADICIONAR OU REMOVER UPVOTED AND APPROVED

    print('automatic-code-review::publish - end')

    return qt_pending_comment, comments_added


def __create_discussion(comment, id_project, id_merge_request, position, git):
    try:
        return git.create_merge_request_thread(
            comment=comment,
            id_project=id_project,
            id_merge_request=id_merge_request,
            position=position,
        )

    except GitlabCreateError as e:
        if e.response_code == 400:
            print('automatic-code-review::create_discussion - fail add (error code 400), retry without position')

            return git.create_merge_request_thread(
                comment=comment,
                id_project=id_project,
                id_merge_request=id_merge_request,
                position=None,
            )
        elif e.response_code == 500 and position is not None:
            print('automatic-code-review::create_discussion - fail add (error code 500), retry without position')

            return git.create_merge_request_thread(
                comment=comment,
                id_project=id_project,
                id_merge_request=id_merge_request,
                position=None,
            )
        else:
            raise e
