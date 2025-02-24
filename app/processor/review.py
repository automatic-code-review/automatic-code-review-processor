import hashlib
import json
import os
import re
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
        snipset = snipset[0:10000] # TODO JOGAR ISSO PARA UMA CONFIGURAÇÃO OU ENTENDER COMO MELHORAR ISSO. A API DO GITLAB NAO SUPORTA TEXTO TÃO GRANDE
        comment_str = f"""{comment_str}

```{type_snipset}
{snipset}
```
"""

    return comment_str


def __get_extensions_to_run(path_extensions, path_resources, stage, merge):
    extensions = []

    for extension_name in os.listdir(path_extensions):
        extension_patb = os.path.join(path_extensions, extension_name)

        if os.path.isdir(extension_patb):
            if not __verify_stage(path_resources, extension_name, stage):
                continue

            if not __can_review_current_merge(extension=extension_name, path_resources=path_resources, merge=merge):
                continue

            path_config = path_resources + "/configs/" + extension_name + "/config.json"

            with open(path_config, 'r') as arquivo:
                config = json.load(arquivo)

            extension_order = None

            if 'order' in config:
                extension_order = config['order']

            extensions.append({
                "extension_name": extension_name,
                "extension_path": extension_patb,
                "extension_order": extension_order
            })

    return sorted(extensions, key=lambda obj: (obj["extension_order"] is None, obj["extension_order"]))


def _get_type_by_scope(scope, scopes):
    for scope_obj in scopes:
        if scope_obj['scope'] == scope:
            return scope_obj['type']

    return ""


def __verify_can_add_comment(comment, config_global, changes):
    comment_scope = config_global.get('commentScope', None)

    if comment_scope is None:
        return True

    position = comment.get('position', None)

    if position is None:
        return True

    start_in_line = position.get("startInLine", None)
    end_in_line = position.get("endInLine", None)

    if start_in_line is None or end_in_line is None:
        return True

    added_lines = []
    position_path = position['path']

    for change in changes:
        if change['new_path'] == position_path:
            added_lines = change['addedLines']
            break

    for i in (start_in_line, end_in_line):
        if i in added_lines:
            return _get_type_by_scope("CHANGED", comment_scope) == "THREAD"

    return _get_type_by_scope("UNCHANGED", comment_scope) == "THREAD"


def review(path_source, path_target, path_resources, merge, stage, config_global, path_source_v2):
    print('automatic-code-review::review - start')

    if 'regexToSkip' in config_global and re.search(config_global['regexToSkip'], merge['title']):
        print('automatic-code-review::review - merge skip')
        return [], []

    path_output = path_resources + "/output"
    path_extensions = path_resources + "/extensions"

    comments = []
    extensions = []
    extensions_to_run = __get_extensions_to_run(path_extensions, path_resources, stage, merge)

    for extension_to_run in extensions_to_run:
        extension_name = extension_to_run['extension_name']
        print(f'automatic-code-review::review - {extension_name} start')

        path_output_data = path_output + "/" + extension_name + "_data.json"
        print(f'automatic-code-review::review - {extension_name} write config [OUTPUT] {path_output_data}')

        extensions.append(extension_name)

        config = __write_config(
            extension=extension_name,
            path_resources=path_resources,
            path_extensions=path_extensions,
            path_target=path_target,
            path_source=path_source,
            path_output=path_output_data,
            path_source_v2=path_source_v2,
            merge=merge,
        )

        path_extension = extension_to_run['extension_path']
        retorno = __exec_extension(extension_name, path_extension, config["language"], config["path"])

        if retorno != 0:
            print(f'automatic-code-review::review - {extension_name} fail')
            comment_id = __generate_md5(f"automatic-code-review::review::{extension_name}::fail")
            comments.append({
                'id': f"{extension_name}:{comment_id}",
                'comment': f"Failed to run {extension_name} extension, contact administrator",
                'type': extension_name
            })
            continue

        print(f'automatic-code-review::review - {extension_name} run end, start read output')

        with open(path_output_data, 'r') as arquivo:
            comments_by_extension = json.load(arquivo)
            qt_comments = len(comments_by_extension)

            print(f'automatic-code-review::review - {extension_name} [QT_COMMENTS] {qt_comments}')

            # TODO CRIAR UM COMENTARIO EM VEZ DE LANÇAR EXCEPTION, E NAO ADICIONAR O COMENTARIO NO MERGE
            __verify_unique_id(extension_name, comments_by_extension)

            for comment in comments_by_extension:
                comment_id = comment['id']

                comment['type'] = extension_name
                comment['id'] = f"{extension_name}:{comment_id}"
                comment['comment'] = __comment_and_snipset(comment, path_source)

                if __verify_can_add_comment(comment, config_global, merge['changes']):
                    comments.append(comment)
                else:
                    qt_comments -= 1
                    print(f'automatic-code-review::review - Ignorando comentario. {json.dumps(comment)}')

        print(f'automatic-code-review::review - {extension_name} end')

        if qt_comments > 0 and "abortOnFail" in config and config["abortOnFail"]:
            print(f'automatic-code-review::review - {extension_name} Abortando por ter retornado comentario')
            break

    print('automatic-code-review::review - end')

    return comments, extensions


def __exec_extension(extension_name, extension_path, extension_language, path_config):
    if "JAVA" == extension_language:
        java_jar = f"{extension_path}/{extension_name}.jar"
        print(f'automatic-code-review::review - {extension_name} run start [APP_JAVA] {java_jar}')
        retorno = subprocess.run(["java", "-jar", java_jar, f"--CONFIG_PATH={path_config}"])

    elif "JAVASCRIPT" == extension_language:
        path_javascript_app = f"{extension_path}/app.js"
        print(f'automatic-code-review::review - {extension_name} run start [APP_JAVASCRIPT] {path_javascript_app}')
        retorno = subprocess.run(["node", path_javascript_app])

    else:
        path_python_app = f"{extension_path}/app.py"
        print(f'automatic-code-review::review - {extension_name} run start [APP_PYTHON] {path_python_app}')
        retorno = subprocess.run(['python', path_python_app])

    return retorno.returncode


def __generate_md5(string):
    md5_hash = hashlib.md5()
    md5_hash.update(string.encode('utf-8'))

    return md5_hash.hexdigest()


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

        if 'projects' in config:
            project_name = merge['project_name']
            projects = config['projects']

            if project_name not in projects:
                projects_required = ', '.join(projects)
                print(f'automatic-code-review::review - Skipando extensao {extension} porque merge não atende o filtro '
                      f'de projects. Project atual: {project_name}. Projeto requerido: {projects_required}')
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
        path_source_v2,
):
    path_config = path_resources + "/configs/" + extension + "/config.json"
    path_config_final = path_extensions + '/' + extension + "/config.json"

    with open(path_config, 'r') as arquivo:
        config = json.load(arquivo)
        extension_language = __get_or_default(config, 'language', 'python')
        config['path_target'] = path_target
        config['path_source'] = path_source
        config['path_source_v2'] = path_source_v2
        config['path_output'] = path_output
        config['merge'] = merge

    with open(path_config_final, 'w') as arquivo:
        json.dump(config, arquivo, indent=True)

    return {
        "path": path_config_final,
        "language": extension_language
    }
