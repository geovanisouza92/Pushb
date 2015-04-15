#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=E0611,C0325

import os
import json
import sublime
import sublime_plugin

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen


API_ENDPOINT = 'https://api.pushbullet.com/v2'
SETTINGS = sublime.load_settings('Pushb.sublime-settings')

def get_setting(name, default=None):
    val = SETTINGS.get(name)
    if val == None:
        try:
            sublime.active_window().active_view().settings.get(name, default)
        except:
            return default
    else:
        return val


class PushbCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
        super(PushbCommand, self).__init__(*args, **kwargs)
        self.headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + get_setting('token'),
            'Content-Type': 'application/json',
            'User-Agent': 'Sublime Text/%(version)s (%(platform)s/%(arch)s)' % {
                'version': sublime.version(),
                'platform': sublime.platform(),
                'arch': sublime.arch(),
            },
        }

    def run(self, edit):
        targets = self.list_devices() + self.list_contacts()

        def on_done(index):
            if index == -1:
                return

            target = targets[index]
            self.push_to(target)

        sublime.active_window().show_quick_panel(targets, on_done)

    def req(self, path, method='GET'):
        return Request(API_ENDPOINT + path, headers=self.headers, method=method)

    def list_devices(self):
        req = self.req('/devices')
        status, res = submit(req)
        print ('list_devices: ' + str(status))
        obj = json.loads(res.decode('utf-8'))
        return [
            [dev['nickname'], dev['iden']]
            for dev in obj['devices']
            if dev['active']
        ]

    def list_contacts(self):
        req = self.req('/contacts')
        status, res = submit(req)
        print ('list_contacts: ' + str(status))
        obj = json.loads(res.decode('utf-8'))
        return [
            [cont['name'], cont['email']]
            for cont in obj['contacts']
            if cont['active']
        ]

    def push_to(self, target):
        obj = {
            'type': 'note',
            'title': os.path.basename(self.view.file_name() or 'Untitled'),
            'body': self.view.substr(sublime.Region(0, self.view.size())),
        }

        if target[1].find('@'):
            obj['email'] = target[1]
        else:
            obj['device_iden'] = target[1]

        req = self.req('/pushes', method='POST')
        data = json.dumps(obj).encode('utf-8')
        status, body = submit(req, data=data)
        if status != 200:
            sublime.error_message(body)


def submit(req, data=None):
    # pylint: disable=W0703
    try:
        res = urlopen(req, data=data, timeout=5)
        return res.status, res.read()

    except Exception as exc:
        sublime.error_message(str(exc))

    return 0, None
