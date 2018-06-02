# -*- coding: utf-8 -*-
import irc3
from irc3.plugins.command import command

__all__ = ['Plugin']


@irc3.plugin
class Plugin:

    def __init__(self, bot):
        self.bot = bot

    @command(permission='admin')
    def privmsg(self, mask, target, args):
        """Send a message as lobot. This can be used to send NickServ commands
        or such.

            %%privmsg <recipient> <message>...
        """
        self.bot.privmsg(args['<recipient>'], ' '.join(args['<message>']))
