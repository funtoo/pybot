# -*- coding: utf-8 -*-
import irc3

__all__ = [
    'privmsg', 'WebhookPlugin', 'C',
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


class C:

    BOLD = '\x02'
    COLOR = '\x03'
    ITALIC = '\x1D'
    UNDERLINE = '\x1F'
    REVERSE = '\x16'
    RESET = '\x0F'

    WHITE = '00'
    BLACK = '01'
    BLUE = '02'
    GREEN = '03'
    RED = '04'
    BROWN = '05'
    PURPLE = '06'
    ORANGE = '07'
    YELLOW = '08'
    LIGHT_GREEN = '09'
    TEAL = '10'
    CYAN = '11'
    LIGHT_BLUE = '12'
    PINK = '13'
    GREY = '14'
    LIGHT_GREY = '15'

    @classmethod
    def _format(cls, fmt, text):
        return fmt + text + (cls.RESET if text[-1] != cls.RESET else '')

    @classmethod
    def bold(cls, text):
        return cls._format(cls.BOLD, text)

    @classmethod
    def color(cls, text, color):
        return cls._format(cls.COLOR + color, text)

    @classmethod
    def italic(cls, text):
        return cls._format(cls.ITALIC, text)

    @classmethod
    def underline(cls, text):
        return cls._format(cls.UNDERLINE, text)

    @classmethod
    def reverse(cls, text):
        return cls._fomat(cls.REVERSE, text)

    @classmethod
    def white(cls, text):
        return cls.color(text, cls.WHITE)

    @classmethod
    def black(cls, text):
        return cls.color(text, cls.BLACK)

    @classmethod
    def blue(cls, text):
        return cls.color(text, cls.BLUE)

    @classmethod
    def green(cls, text):
        return cls.color(text, cls.GREEN)

    @classmethod
    def red(cls, text):
        return cls.color(text, cls.red)

    @classmethod
    def brown(cls, text):
        return cls.color(text, cls.BROWN)

    @classmethod
    def purple(cls, text):
        return cls.color(text, cls.PURPLE)

    @classmethod
    def orange(cls, text):
        return cls.color(text, cls.ORANGE)

    @classmethod
    def yellow(cls, text):
        return cls.color(text, cls.YELLOW)

    @classmethod
    def light_green(cls, text):
        return cls.color(text, cls.LIGHT_GREEN)

    @classmethod
    def teal(cls, text):
        return cls.color(text, cls.TEAL)

    @classmethod
    def cyan(cls, text):
        return cls.color(text, cls.CYAN)

    @classmethod
    def light_blue(cls, text):
        return cls.color(text, cls.LIGHT_GLUE)

    @classmethod
    def pink(cls, text):
        return cls.color(text, cls.PINK)

    @classmethod
    def grey(cls, text):
        return cls.color(text, cls.GREY)

    @classmethod
    def light_grey(cls, text):
        return cls.color(text, cls.LIGHT_GREY)
