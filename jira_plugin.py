# -*- coding: utf-8 -*-
import irc3
import requests


def privmsg(rule):
    p = r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :'
    return irc3.event(p + rule)


@irc3.plugin
class Plugin:

    def __init__(self, bot):
        self.web = irc3.utils.maybedotted('aiohttp.web')
        self.bot = bot
        self.config = bot.config.get(__name__, {})
        self.webhook_key = self.config.get('webhook_key')
        if not self.webhook_key:
            self.bot.log.warning(
                'No webhook_key is set. Your webhook is insecure')
        self.server = None

    def server_ready(self):
        if self.server is not None:
            return
        server = self.web.Server(self.handler, loop=self.bot.loop)
        host = self.config.get('host', '127.0.0.1')
        port = int(self.config.get('port', 8080))
        self.bot.log.info('Starting web interface on %s:%s...', host, port)
        self.server = self.bot.create_task(
            self.bot.loop.create_server(server, host, port))

    async def handler(self, request):
        if request.method == 'POST':
            if self.webhook_key:
                if request.headers.get('X-Api-Key') != self.webhook_key:
                    return self.web.Response(status=403)
            result = await request.json()
            hook_name = result['webhookEvent'].replace(':', '_')
            hook = getattr(self, 'wh_{}'.format(hook_name), None)
            if hook:
                hook(result)
            return self.web.Response(status=200)
        return self.web.Response(body="It works!", status=200)

    def wh_jira_issue_created(self, result):
        template = (
            "\x0311{user}\017 reported an issue: \x039{summary} "
            "\x0310[{type}]\017 {link}"
        )
        message = template.format(
            user=result['user']['name'],
            summary=result['issue']['fields']['summary'],
            type=result['issue']['fields']['issuetype']['name'],
            link='https://bugs.funtoo.org/browse/' + result['issue']['key'],
        )
        self.bot.notice('#funtoo-dev', message)

    def wh_jira_issue_updated(self, result):
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
                "\x0311{user}\017 commented on \x0311{id}\017: "
                "\x039{summary}\017 {link}"
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
                        message = "unassigned \x0313{old}\017"
                else:
                    message = "assigned \x0313{new}\017"
                if old_assignee and new_assignee:
                    if old_assignee == msg_data['user']:
                        message += " (instead of himself)"
                    else:
                        message += " (instead of \x0313{old}\017)"
                changes.append(
                    message.format(old=old_assignee, new=new_assignee))
            if old_status != new_status:
                message = "set status \x0313{new}\017 (was: \x0313{old}\017)"
                changes.append(
                    message.format(old=old_status, new=new_status))
            if changes:
                template = (
                    "\x0311{user}\017 {changes} on \x0311{id}\017 ("
                    "\x039{summary}\017) {link}"
                )
                msg_data['changes'] = ' and '.join(changes)
        if not template:
            return
        message = template.format(**msg_data)
        self.bot.notice('#funtoo-dev', message)

    @privmsg(r'.*\b(?P<issue>(FL|QA|KEYC)-\d+)\b')
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
            "\x0311{id}\x039 {summary} \x0310[{type}]\x0313 "
            "Status: {status_name} ({status_cat})\017 {link}"
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
