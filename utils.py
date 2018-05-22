# -*- coding: utf-8 -*-
import irc3

__all__ = [
    'privmsg', 'WebhookPlugin',
]


def privmsg(rule):
    p = r'^(@(?P<tags>\S+) )?:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :'
    return irc3.event(p + rule)


class WebhookPlugin:

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
        if self.webhook_key:
            if request.headers.get('X-Api-Key') != self.webhook_key:
                return self.web.Response(body="Wrong API key", status=403)
        handler = getattr(self, request.method, None)
        if handler:
            return await handler(request)
        return self.web.Response(status=405)

    async def GET(self, request):
        return self.web.Response(body="It works!", status=200)
