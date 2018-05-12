# -*- coding: utf-8 -*-
from irc3.plugins.command import command
import irc3
import requests


@irc3.plugin
class Plugin:

    def __init__(self, bot):
        self.bot = bot

    # @irc3.event(irc3.rfc.JOIN)
    # def say_hi(self, mask, channel, **kw):
    #     """Say hi when someone join a channel"""
    #     if mask.nick != self.bot.nick:
    #         self.bot.privmsg(channel, 'Hi %s!' % mask.nick)
    #     else:
    #         self.bot.privmsg(channel, 'Hi!')

    @command(permission='view')
    def echo(self, mask, target, args):
        """Echo

            %%echo <message>...
        """
        yield ' '.join(args['<message>'])

    @irc3.event(r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) (?P<event>(PRIVMSG|NOTICE)) (?P<target>\S+) :.*(?P<issue>(FL|QA)-\d+).*$')
    def show_issue(self, mask, event, target, issue):
        print(issue, target, mask, event)
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
            id=issue,
            summary=result['fields']['summary'],
            type=result['fields']['issuetype']['name'],
            status_name=result['fields']['status']['name'],
            status_cat=result['fields']['status']['statusCategory']['name'],
            link='https://bugs.funtoo.org/browse/' + issue,
        )
        self.bot.privmsg(target, message)
