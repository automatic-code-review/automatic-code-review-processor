import json
import os
import subprocess


class UniqueException(Exception):
    pass


def __verify_unique_id(extension_name, comments):
    ids = []

    for comment in comments:
        current_id = comment['id']

        if current_id in ids:
            print('automatic-code-review::review - ' + comment['comment'])
            raise UniqueException(
                f"The extension '{extension_name}' returned 2 comments with the same id: '{current_id}'"
            )

        ids.append(current_id)


def __get_or_default(obj, name, default):
    if name in obj:
        return obj[name]

    return default


def __comment_and_snipset(comment, path):
    comment_str = comment['comment']

    if 'position' in comment and __get_or_default(comment['position'], 'snipset', True):
        position = comment['position']
        path = path + "/" + position['path']

        lines = []

        with open(path, 'r') as file:
            for line in file:
                lines.append(line)

        start = position['startInLine']
        end = position['endInLine']
        type_snipset = ''

        if 'language' in position:
            type_snipset = position['language']

        snipset = ''.join(lines[start - 1:end])
        comment_str = f"""{comment_str}

```{type_snipset}
{snipset}
```
"""

    return comment_str


def review(path_source, path_target, path_resources, merge, stage):
    print('automatic-code-review::review - start')

    path_output = path_resources + "/output"
    path_extensions = path_resources + "/extensions"

    comments = []

    for extension_name in os.listdir(path_extensions):
        path_extension = os.path.join(path_extensions, extension_name)

        if os.path.isdir(path_extension):
            if not __verify_stage(path_resources, extension_name, stage):
                continue

            print(f'automatic-code-review::review - {extension_name} start')

            if not __can_review_current_merge(extension=extension_name, path_resources=path_resources, merge=merge):
                continue

            path_output_data = path_output + "/" + extension_name + "_data.json"
            print(f'automatic-code-review::review - {extension_name} write config [OUTPUT] {path_output_data}')

            __write_config(
                extension=extension_name,
                path_resources=path_resources,
                path_extensions=path_extensions,
                path_target=path_target,
                path_source=path_source,
                path_output=path_output_data,
                merge=merge,
            )

            path_python_app = path_extension + "/app.py"
            print(f'automatic-code-review::review - {extension_name} run start [APP] {path_python_app}')

            subprocess.run(['python3.10', path_python_app])

            print(f'automatic-code-review::review - {extension_name} run end, start read output')

            with open(path_output_data, 'r') as arquivo:
                comments_by_extension = json.load(arquivo)
                qt_comments = len(comments_by_extension)

                print(f'automatic-code-review::review - {extension_name} [QT_COMMENTS] {qt_comments}')

                __verify_unique_id(extension_name, comments_by_extension)

                for comment in comments_by_extension:
                    comment_id = comment['id']

                    comment['type'] = extension_name
                    comment['id'] = f"{extension_name}:{comment_id}"
                    comment['comment'] = __comment_and_snipset(comment, path_source)

                    comments.append(comment)

            print(f'automatic-code-review::review - {extension_name} end')

    print('automatic-code-review::review - end')

    return comments


def __verify_stage(path_resources, extension, stage):
    path_config = path_resources + "/configs/" + extension + "/config.json"

    with open(path_config, 'r') as arquivo:
        config = json.load(arquivo)

    if 'stage' in config:
        extension_stage = config['stage']
    else:
        extension_stage = 'default'

    if stage != extension_stage:
        print(
            f'automatic-code-review::review - Skipando extensao {extension} porque nao pertence ao stage atual. '
            f'Stage atual: {stage}. Stage da extensao: {extension_stage}')
        return False

    return True


def __can_review_current_merge(extension, path_resources, merge):
    path_config = path_resources + "/configs/" + extension + "/config.json"

    with open(path_config, 'r') as arquivo:
        config = json.load(arquivo)

        if 'createdBy' in config:
            author = merge['author']
            created_by = config['createdBy']

            if author not in created_by:
                authors_required = ', '.join(created_by)
                print(f'automatic-code-review::review - Skipando extensao {extension} porque merge não atende o filtro '
                      f'de createdBy. Author atual: {author}. Author requerido: {authors_required}')
                return False

    return True


def __write_config(
        extension,
        path_resources,
        path_extensions,
        path_target,
        path_source,
        path_output,
        merge,
):
    path_config = path_resources + "/configs/" + extension + "/config.json"
    path_config_final = path_extensions + '/' + extension + "/config.json"

    with open(path_config, 'r') as arquivo:
        config = json.load(arquivo)
        config['path_target'] = path_target
        config['path_source'] = path_source
        config['path_output'] = path_output
        config['merge'] = merge

    with open(path_config_final, 'w') as arquivo:
        json.dump(config, arquivo, indent=True)
