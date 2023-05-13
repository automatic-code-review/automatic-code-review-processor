import json
import os
import subprocess


def review(path_source, path_target, path_resources):
    path_output = path_resources + "/output"
    path_extensions = path_resources + "/extensions"

    comments = []

    for extension_name in os.listdir(path_extensions):
        path_extension = os.path.join(path_extensions, extension_name)

        if os.path.isdir(path_extension):
            path_output_data = path_output + "/" + extension_name + "_data.json"

            __write_config(
                extension=extension_name,
                path_resources=path_resources,
                path_extensions=path_extensions,
                path_target=path_target,
                path_source=path_source,
                path_output=path_output_data,
            )

            path_python_app = path_extension + "/app.py"
            subprocess.run(['python3.10', path_python_app])

            with open(path_output_data, 'r') as arquivo:
                for comment in json.load(arquivo):
                    comment_id = comment['id']
                    comment['id'] = f"{extension_name}:{comment_id}"
                    comments.append(comment)

    return comments


def __write_config(
        extension,
        path_resources,
        path_extensions,
        path_target,
        path_source,
        path_output,
):
    path_config = path_resources + "/configs/" + extension + "/config.json"
    path_config_final = path_extensions + '/' + extension + "/config.json"

    with open(path_config, 'r') as arquivo:
        config = json.load(arquivo)
        config['path_target'] = path_target
        config['path_source'] = path_source
        config['path_output'] = path_output

    with open(path_config_final, 'w') as arquivo:
        json.dump(config, arquivo, indent=True)
