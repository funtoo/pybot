# -*- coding: utf-8 -*-
import irc3
import requests

from utils import privmsg, WebhookPlugin, C

__all__ = ['Plugin']


@irc3.plugin
class Plugin(WebhookPlugin):

    def __init__(self, bot):
        self.web = irc3.utils.maybedotted('aiohttp.web')
        self.bot = bot
        self.config = bot.config.get(__name__, {})
        self.webhook_key = self.config.get('webhook_key')
        if not self.webhook_key:
            self.bot.log.warning(
                'No webhook_key is set. Your webhook is insecure')
        self.server = None

    def get_channel(self, project):
        if project in ['FL', 'QA', 'KEYC']:
            return '#funtoo-dev'
        if project == 'BRZ':
            return '#breezyops'

    async def POST(self, request):
        result = await request.json()
        hook_name = result['webhookEvent'].replace(':', '_')
        hook = getattr(self, 'wh_{}'.format(hook_name), None)
        if hook:
            hook(result)
        return self.web.Response(status=200)

    def wh_jira_issue_created(self, result):
        channel = self.get_channel(result['issue']['fields']['project']['key'])
        if not channel:
            return
        template = (
            C.cyan("{user}") + " reported an issue: " +
            C.light_green("{summary}") + " " + C.teal("[{type}]") + " {link}"
        )
        message = template.format(
            user=result['user']['name'],
            summary=result['issue']['fields']['summary'],
            type=result['issue']['fields']['issuetype']['name'],
            link='https://bugs.funtoo.org/browse/' + result['issue']['key'],
        )
        self.bot.notice(channel, message)

    def wh_jira_issue_updated(self, result):
        channel = self.get_channel(result['issue']['fields']['project']['key'])
        if not channel:
            return
        msg_data = dict(
            id=result['issue']['key'],
            user=result['user']['name'],
            summary=result['issue']['fields']['summary'],
            link='https://bugs.funtoo.org/browse/' + result['issue']['key'],
        )
        template = None
        event = result['issue_event_type_name']
        if event == 'issue_commented':
            template = (
                C.cyan("{user}") + " commented on " + C.cyan("{id}") + ": " +
                C.light_green("{summary}") + " {link}"
            )
            msg_data['summary'] = \
                result['comment']['body'].splitlines()[0][:100]
            msg_data['link'] += '#comment-' + result['comment']['id']
        elif event in ['issue_generic', 'issue_updated']:
            old_status, new_status = None, None
            old_assignee, new_assignee = None, None
            for change in result['changelog']['items']:
                if change['field'] == 'status':
                    old_status = change['fromString']
                    new_status = change['toString']
                elif change['field'] == 'assignee':
                    old_assignee = change['from']
                    new_assignee = change['to']
            changes = []
            if old_assignee != new_assignee:
                if new_assignee == msg_data['user']:
                    message = "assigned himself"
                elif not new_assignee:
                    if old_assignee == msg_data['user']:
                        message = "unassigned himself"
                    else:
                        message = "unassigned " + C.pink("{old}")
                else:
                    message = "assigned " + C.pink("{new}")
                if old_assignee and new_assignee:
                    if old_assignee == msg_data['user']:
                        message += " (instead of himself)"
                    else:
                        message += " (instead of " + C.pink("{old}") + ")"
                changes.append(
                    message.format(old=old_assignee, new=new_assignee))
            if old_status != new_status:
                message = (
                    "set status " + C.pink("{new}") +
                    " (was: " + C.pink("{old}") + ")"
                )
                changes.append(
                    message.format(old=old_status, new=new_status))
            if changes:
                template = (
                    C.cyan("{user}") + " {changes} on " + C.cyan("{id}") +
                    " (" + C.light_green("{summary}") + ") {link}"
                )
                msg_data['changes'] = ' and '.join(changes)
        if not template:
            return
        message = template.format(**msg_data)
        self.bot.notice(channel, message)

    @privmsg(r'.*\b(?P<issue>(FL|QA|KEYC|BRZ)-\d+)\b')
    def show_issue(self, mask, target, issue):
        if not target.startswith('#'):
            target = mask.split('!')[0]
        url = 'https://bugs.funtoo.org/rest/api/2/issue/' + issue
        r = requests.get(url)
        result = r.json()
        if 'errorMessages' in result:
            self.bot.privmsg(target, ' ; '.join(result['errorMessages']))
            return
        template = (
            C.cyan("{id}") + " " + C.light_green("{summary}") + " " +
            C.teal("[{type}]") + " " +
            C.pink("Status: {status_name} ({status_cat})") + " {link}"
        )
        message = template.format(
            id=result['key'],
            summary=result['fields']['summary'],
            type=result['fields']['issuetype']['name'],
            status_name=result['fields']['status']['name'],
            status_cat=result['fields']['status']['statusCategory']['name'],
            link='https://bugs.funtoo.org/browse/' + result['key'],
        )
        self.bot.privmsg(target, message)
