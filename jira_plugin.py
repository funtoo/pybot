# -*- coding: utf-8 -*-
import irc3
import requests


def privmsg(rule):
    p = r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :'
    return irc3.event(p + rule)


@irc3.plugin
class Plugin:

    def __init__(self, bot):
        self.bot = bot

    @privmsg(r'.*\b(?P<issue>(FL|QA)-\d+)\b')
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
