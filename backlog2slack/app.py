# -*- coding: utf-8 -*-
from chalice import Chalice
import slackweb
import json

slack_url = "SLACK_INBOUND_WEBHOOK"
backlog_url = "BACKLOG_PROJECT_URL"
channel = "#CHANNEL_NAME"

# TODO: 環境変数で設定したい
# slack_url = os.environ['SLACK_URL']
# backlog_url = os.environ['BACKLOG_URL']
# channel = os.environ['SLACK_CHANNEL']

slack = slackweb.Slack(url=slack_url)
app = Chalice(app_name='backlog2slack')
app.debug = True


def to_slack(attachments):
    slack.notify(attachments=attachments, channel=channel, username="backlog-bot")


def get_project(body):
    project_key = body['project']['projectKey']
    project_id = body['content']['key_id']
    summary = body['content']['summary']
    task_key = "%s-%d" % (project_key, project_id)
    task = "%s:%s" % (task_key, summary)
    project_url = "%s/view/%s" % (backlog_url, task_key)
    return task, project_url


def create_change_field(change):
    status_dict = {"1": "未対応", "2": "対応中", "3": "処理済み", "4": "完了"}
    resolution_dict = {"0": "対応済み", "1": "対応しない", "2": "無効", "3": "重複", "4": "再現しない", "5": "未設定"}

    field = change['field']
    old_val = change['old_value']
    new_val = change['new_value']

    if field == "status":
        field = "状態"
        old_val = status_dict[old_val]
        new_val = status_dict[new_val]

    if field == "startDate":
        field = "開始日"

    if field == "limitDate":
        field = "終了日"

    if field == "estimatedHours":
        field = "予定"

    if field == "actualHours":
        field = "実績"

    if field == "resolution":
        field = "完了理由"
        if old_val == "":
            old_val = "5"
        if new_val == "":
            new_val = "5"

        old_val = resolution_dict[old_val]
        new_val = resolution_dict[new_val]

    if old_val == "":
        old_val = "未設定"

    if new_val == "":
        new_val = "未設定"

    return {
        "title": field,
        "value": "%s -> %s" % (old_val, new_val)
    }


def get_assignee(body):
    assignee_data = body['content']['assignee']
    if assignee_data == None:
        assignee = "未設定"
    else:
        assignee = assignee_data['name']
    return assignee


def get_color(priority):
    if priority == 2:
        return "#F35A00"
    if priority == 3:
        return "#7CD197"
    if priority == 4:
        return "#3AA3E3"
    return "#a1a2a3"


def add_task(body):
    project, project_url = get_project(body)

    description = body['content']['description']
    assignee = get_assignee(body)

    pretext = "タスクが追加されました。担当:%s" % str(assignee)
    user = body['createdUser']['name']
    priority = body['content']['priority']['id']
    color = get_color(priority)
    attachments = []
    attachment = {
        "author_name": user,
        "title": project,
        "title_link": project_url,
        "pretext": pretext,
        "text": description,
        "color": color}
    attachments.append(attachment)
    to_slack(attachments)
    return


def update_task(body):
    changes_list = body['content']['changes']
    field_list = []
    for change in changes_list:
        field_list.append(create_change_field(change))

    project, project_url = get_project(body)
    comment = body['content']['comment']['content']
    user = body['createdUser']['name']
    attachment_pretext = "タスクのアップデートがありました。"
    if comment != "":
        field_list.append(
            {
                "title": "コメント",
                "value": comment
            }
        )
    attachments = []
    attachment = {
        "author_name": user,
        "title": project,
        "title_link": project_url,
        "pretext": attachment_pretext,
        "fields": field_list}
    print attachment
    attachments.append(attachment)
    to_slack(attachments)
    return


def comment_task(body):
    field_list = []

    project, project_url = get_project(body)
    comment = body['content']['comment']['content']
    user = body['createdUser']['name']
    attachment_pretext = "タスクにコメントがありました。"
    field_list.append(
        {
            "title": "コメント",
            "value": comment
        }
    )
    attachments = []
    attachment = {
        "author_name": user,
        "title": project,
        "title_link": project_url,
        "pretext": attachment_pretext,
        "fields": field_list}
    print attachment
    attachments.append(attachment)
    to_slack(attachments)
    return


def svn_commit(body):
    revision = body['content']['rev']
    comment = body['content']['comment']
    user = body['createdUser']['name']
    attachments = []
    attachment = {
        "pretext": "SVNにコミットがありました",
        "fields": [
            {
                "title": "user",
                "value": user,
                "short": "true"
            },
            {
                "title": "revision",
                "value": revision,
                "short": "true"
            },
            {
                "title": "comment",
                "value": comment
            }
        ],
        "mrkdwn_in": ["text", "pretext"]}
    attachments.append(attachment)
    to_slack(attachments)
    return


@app.route('/', methods=['POST'])
def index():
    body = app.current_request.json_body
    print ("body---> %s" % json.dumps(body))
    message_type = body['type']
    print (message_type)

    if message_type == 1:
        add_task(body)

    if message_type == 2:
        update_task(body)

    if message_type == 3:
        comment_task(body)

    if message_type == 11:
        svn_commit(body)

    return ""
