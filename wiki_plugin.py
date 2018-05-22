# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from urllib.parse import quote

import irc3
from irc3.plugins.command import command

from utils import WebhookPlugin

__all__ = ['Plugin']


@irc3.plugin
class Plugin(WebhookPlugin):

    def __init__(self, bot):
        super().__init__(bot)
        self.silent_pages = {}
        self.last_page = None

    async def POST(self, request):
        result = await request.json()
        template = "Wiki {type}: Page: \x0311{title}\017 by \x0310{user}\017"
        if result.get('comment'):
            template += " Comment: \x0310{comment}\017"
        template += " http://{server_name}/{slug}"
        title = result.get('title', '')
        result['slug'] = quote(title.replace(' ', '_'), safe='/:')

        if result.get('minor') or 'Translations:' in title:
            return self.web.Response(status=200)

        self.clean_silent_pages()
        if title in self.silent_pages:
            self.silent_pages[title] = datetime.now() + timedelta(minutes=5)
            return self.web.Response(status=200)
        self.last_page = title
        self.silent_pages[title] = datetime.now() + timedelta(minutes=5)
        message = template.format(**result)
        self.bot.notice('#funtoo', message)
        return self.web.Response(status=200)

    def clean_silent_pages(self):
        for k, v in list(self.silent_pages.items()):
            if v < datetime.now():
                del self.silent_pages[k]

    @command(permission='view')
    def silence_page(self, mask, target, *args, **kwargs):
        """Silence given page or last page if no page given. Pages are silenced
           for 24h.

            %%silence_page [page title]
        """
        if not target.startswith('#'):
            target = mask.nick
        page = self.last_page
        if page not in self.silent_pages:
            self.bot.privmsg(target, "No such page seen recently.")
        else:
            self.silent_pages[page] = datetime.now() + timedelta(hours=24)
            self.bot.privmsg(target, "\"{}\" silenced for 24h".format(page))
