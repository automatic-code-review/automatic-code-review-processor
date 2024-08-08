import json

import requests


def add_comment(webhooks, comments, merge, workspace_name):
    comments_format = []

    web_url = merge['web_url']

    for comment in comments:
        comments_format.append({
            "idComment": comment['id'],
            "lkComment": web_url + comment['web_url'],
            "dsType": comment['type'],
            "txComment": comment['comment']
        })

    json_data = json.dumps({
        "merge": {
            "idMerge": merge['merge_request_id'],
            "idProject": merge['project_id'],
            "idGroup": 0,
            "dsAuthorUsername": merge['author'],
            "dhMerge": merge['created_at']
        },
        "workspaceName": workspace_name,
        "comments": comments_format
    })

    success = True

    for webhook in webhooks:
        if 'ADD_COMMENT' in webhook['events']:
            print('automatic-code-review::webhook::add_comment - start webhook ', webhook['name'])

            response = requests.post(webhook['host'], data=json_data, headers={
                "Content-Type": "application/json"
            })

            if response.status_code == 200:
                print('automatic-code-review::webhook::add_comment - webhook success')
            else:
                success = False
                print('automatic-code-review::webhook::add_comment - webhook failed [CODIGO_STATUS]',
                      response.status_code)

    return success
