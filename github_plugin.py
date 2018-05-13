# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
import irc3
from irc3.plugins.command import command
import requests


@irc3.plugin
class Plugin:

    KIT_UPDATES = [time(1, 30), time(7, 30), time(13, 30), time(19, 30)]

    def __init__(self, bot):
        self.bot = bot

    @command(permission='view')
    def kit_updates(self, mask, target, *args, **kwargs):
        """Kit Updates

            %%kit_updates
        """
        if not target.startswith('#'):
            target = mask.nick
        now = datetime.utcnow()

        r = requests.get(
            'https://api.github.com/repos/funtoo/meta-repo/branches/master')
        result = r.json()
        last_update = datetime.strptime(
            result['commit']['commit']['committer']['date'],
            "%Y-%m-%dT%H:%M:%SZ")
        relative_last_update = now - last_update
        hours = int(relative_last_update.seconds / 3600)
        if hours < 1:
            minutes = int((relative_last_update.seconds / 60) // 5 * 5)
            if minutes == 0:
                message = "Kits were just updated."
            else:
                message = (
                    "Last kit updates were about {} minutes ago."
                ).format(minutes)
        elif hours == 1:
            message = "Last kit updates were about an hour ago."
        else:
            message = (
                "Last kit updates were about {} hours ago."
            ).format(hours)
        self.bot.privmsg(target, message)

        cur_time = now.time()
        if cur_time >= self.KIT_UPDATES[-1]:
            next_update = datetime.combine(
                now.date() + timedelta(days=1), self.KIT_UPDATES[0])
        else:
            for t in self.KIT_UPDATES:
                if t > cur_time:
                    next_update = datetime.combine(now.date(), t)
        relative_next_update = next_update - now
        hours = int(relative_next_update.seconds / 3600)
        if hours < 1:
            minutes = int((relative_next_update.seconds / 60) // 10 * 10) + 10
            message = (
                "Next kit updates expected in about {} minutes."
            ).format(minutes)
        elif hours == 1:
            message = "Next kit updates expected in about an hour."
        else:
            message = (
                "Next kit updates expected in about {} hours."
            ).format(hours)
        self.bot.privmsg(target, message)
