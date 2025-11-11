# -*- coding: utf-8 -*-

import subprocess
from collections import namedtuple
from albert import *

md_iid = "5.0"
md_version = "0.7.1"
md_name = "X Window Switcher"
md_description = "Switch X11 Windows"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/albert-plugin-python-x-window-switcher"
md_bin_dependencies = ["wmctrl"]
md_authors = ["@edjoperez", "@ManuelSchneid3r", "@dshoreman", "@nopsqi"]

Window = namedtuple("Window", ["wid", "desktop", "wm_class", "host", "wm_name"])


class Plugin(PluginInstance, RankedQueryHandler):
    def __init__(self):
        PluginInstance.__init__(self)
        RankedQueryHandler.__init__(self)

        # Check for X session and wmctrl availability
        try:
            subprocess.check_call(["wmctrl", "-m"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            raise Exception("wmctrl not found. Please install wmctrl.")
        except subprocess.CalledProcessError:
            raise Exception("Unable to communicate with X11 window manager. This plugin requires a running X session.")

    def defaultTrigger(self):
        return 'w '

    def rankItems(self, ctx):
        rank_items = []

        try:
            for line in subprocess.check_output(['wmctrl', '-l', '-x']).splitlines():
                win = Window(*parseWindow(line))

                if win.desktop == "-1":
                    continue

                win_instance, win_class = win.wm_class.replace(' ', '-').split('.', 1)

                matcher = Matcher(ctx.query)
                if m := matcher.match(win_instance + ' ' + win_class + ' ' + win.wm_name):
                    rank_items.append(
                        RankItem(
                            StandardItem(
                                id="%s%s" % (md_name, win.wm_class),
                                icon_factory=lambda w_inst=win_instance: makeThemeIcon(w_inst),
                                text="%s  - Desktop %s" % (win_class.replace('-', ' '), win.desktop),
                                subtext=win.wm_name,
                                actions=[Action("switch",
                                                "Switch Window",
                                                lambda w=win: runDetachedProcess(["wmctrl", '-i', '-a', w.wid])),
                                         Action("move",
                                                "Move window to this desktop",
                                                lambda w=win: runDetachedProcess(["wmctrl", '-i', '-R', w.wid])),
                                         Action("close",
                                                "Close the window gracefully.",
                                                lambda w=win: runDetachedProcess(["wmctrl", '-c', w.wid]))]
                            ),
                            m
                        )
                    )

        except subprocess.CalledProcessError as e:
            warning(f"Error executing wmctrl: {str(e)}")

        return rank_items


def parseWindow(line):
    win_id, desktop, rest = line.decode().split(None, 2)
    win_class, rest = rest.split('  ', 1)
    host, title = rest.strip().split(None, 1)

    return [win_id, desktop, win_class, host, title]
