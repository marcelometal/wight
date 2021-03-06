#!/usr/bin/env python
# -*- coding: utf-8 -*-

# wight load testing
# https://github.com/heynemann/wight

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2013 Bernardo Heynemann heynemann@gmail.com
from contextlib import contextmanager

import sys
from os.path import exists, join
import getpass

from cement.core import controller
import requests
from six.moves import input
from colorama import Style, Fore

from wight import __version__
from wight.cli.config import Config
from wight.errors import TargetNotSetError, UnauthenticatedError


class WightBaseController(controller.CementBaseController):
    def __init__(self, *args, **kw):
        self.arguments = None
        if 'pargs' in kw:
            pargs = kw['pargs']
            del kw['pargs']
            self.arguments = pargs

        super(WightBaseController, self).__init__(*args, **kw)
        self.ignored += ['api']

        bright_yellow = "%s%s" % (Fore.YELLOW, Style.BRIGHT)
        bright_cyan = "%s%s" % (Fore.CYAN, Style.BRIGHT)
        bright_green = "%s%s" % (Fore.GREEN, Style.BRIGHT)
        bright_magenta = "%s%s" % (Fore.MAGENTA, Style.BRIGHT)

        dim_white = "%s%s" % (Fore.WHITE, Style.DIM)
        dim_red = "%s%s" % (Fore.RED, Style.DIM)

        self.title_color = bright_cyan
        self.text_color = dim_white
        self.success_text_color = bright_green
        self.error_text_color = dim_red
        self.commands_color = bright_yellow
        self.keyword_color = bright_magenta
        self.comment_color = dim_white

        self.reset = "%s%s" % (Style.RESET_ALL, self.text_color)
        self.reset_success = "%s%s" % (Style.RESET_ALL, self.success_text_color)
        self.reset_error = "%s%s" % (Style.RESET_ALL, self.error_text_color)

    def _get_parameter(self, parameter, default_name):
        result = parameter
        if not parameter and hasattr(self.app.user_data, default_name):
            result = getattr(self.app.user_data, default_name)
        if not result:
            self.puterror(
                """
A default %(parameter_name)s was not set and you do not pass one. You can:
    pass a %(parameter_name)s using %(keyword_color)s--%(parameter_name)s%(reset_error)s parameter
    or set a default %(parameter_name)s with %(commands_color)swight default-set %(keyword_color)s--%(parameter_name)s <%(parameter_name)s-name>%(reset_error)s command
                """ %
                {
                    "parameter_name": default_name,
                    "keyword_color": self.keyword_color,
                    "commands_color": self.commands_color,
                    "reset_error": self.reset_error
                }
            )
        return result

    def abort(self, message="Aborting..."):
        self.line_break()
        self.puterror(message)
        self.line_break()

    def puts(self, message):
        self.write("%s%s%s" % (self.reset, message, self.reset))

    def putsuccess(self, message):
        self.write("%s%s%s" % (self.reset_success, message, self.reset_success))

    def puterror(self, message):
        self.write("%s%s%s" % (self.reset_error, message, self.reset_error))

    def line_break(self):
        self.write("")

    def align_right(self, message, length):
        spacer = (length - len(message)) * ' '
        return "%s%s" % (spacer, message)

    def _parse_args(self):
        super(WightBaseController, self)._parse_args()

        if self.arguments is None:
            self.arguments = self.app.pargs

    def load_conf(self):
        conf_path = self.arguments and self.arguments.conf or None

        self.log.info('Using configuration file in %s.' % conf_path)
        if conf_path and exists(conf_path):
            self.config = Config.load(conf_path)
        else:
            self.config = Config()

    def write(self, msg):
        sys.stdout.write('%s\n' % msg)

    def get_pass(self, msg):
        return getpass.getpass(prompt="%s " % msg)

    def ask_for(self, msg):
        return input("%s " % msg)

    def get(self, path, headers={}):
        if self.app.user_data.token:
            headers.update({"X-Wight-Auth": self.app.user_data.token})
        url = join(self.app.user_data.target.rstrip('/'), path.lstrip('/'))
        return requests.get(url, headers=headers)

    def post(self, path, data={}, headers={}):
        return self.send_request("POST", path, data, headers)

    def put(self, path, data={}, headers={}):
        return self.send_request("PUT", path, data, headers)

    def delete(self, path, data={}, headers={}):
        return self.send_request("DELETE", path, data, headers)

    def patch(self, path, data={}, headers={}):
        return self.send_request("PATCH", path, data, headers)

    def send_request(self, method, path, data={}, headers={}):
        headers.update({"X-Wight-Auth": self.app.user_data.token})
        target = self.app.user_data.target.rstrip('/')
        data.update({"target": target})
        url = join(target, path.lstrip('/'))

        func = getattr(requests, method.lower())
        return func(url, data=data, headers=headers)

    @staticmethod
    def authenticated(fn):
        def handle(decorated_self, *args, **kw):
            user = None
            if hasattr(decorated_self, 'app') and hasattr(decorated_self.app, 'user_data'):
                user = decorated_self.app.user_data

            if user is None or not user.target:
                raise TargetNotSetError()

            if not user.token:
                raise UnauthenticatedError()

            fn(decorated_self, *args, **kw)

        handle.__name__ = fn.__name__
        handle.__doc__ = fn.__doc__

        return handle


class WightDefaultController(WightBaseController):
    class Meta:
        label = 'base'
        description = 'wight load testing scheduler and tracker.'
        epilog = '''Wight version %s. For more info refer to the documentation at https://wight.readthedocs.org.
        ''' % __version__

    @controller.expose(hide=True)
    def default(self):
        self.app.args.print_help()


@contextmanager
def connected_controller(controller):
    if not controller.app.user_data or not controller.app.user_data.target:
        controller.line_break()
        controller.puterror("You need to set the target to use wight. Use '%swight target-set %s<url of target>%s' to login." % (
            controller.commands_color, controller.keyword_color, controller.reset_error
        ))
        controller.line_break()
        sys.exit(0)
    try:
        yield
    except requests.exceptions.ConnectionError:
        target = controller.app.user_data.target
        controller.line_break()
        controller.puterror("The server did not respond. Check your connection with the target '%s%s%s'." % (
            controller.keyword_color, target, controller.reset_error
        ))
        controller.line_break()
