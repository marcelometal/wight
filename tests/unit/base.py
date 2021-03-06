#!/usr/bin/env python
# -*- coding: utf-8 -*-

# wight load testing
# https://github.com/heynemann/wight

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2013 Bernardo Heynemann heynemann@gmail.com

from os.path import dirname, abspath, join
from unittest import TestCase as PythonTestCase
import socket

from mock import Mock
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase, get_unused_port
from tornado.httpclient import HTTPRequest
from tornado import netutil
from cement.utils import test
from mongoengine import connect

from wight.api.app import WightApp
from wight.api.config import Config
from wight.models import User, Team
from wight.web.app import WightWebApp

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode


ROOT_PATH = abspath(join(dirname(__file__), '..'))


def focus(*args, **kwargs):
    def wrap_ob(ob):
        setattr(ob, 'focus', 1)
        return ob
    return wrap_ob


class TestCase(test.CementTestCase):
    def clean_calls(self):
        self.calls_made = []

    def record_calls(self, *args, **kw):
        self.calls_made.append((args, kw))

    def make_controller(self, cls, app=None, *args, **kw):
        if app is None:
            app = self.make_app(argv=args)
            app.setup()

        pargs = Mock(**kw)
        controller = cls(pargs=pargs)
        controller.app = app
        controller.log = Mock()

        return controller

    def fixture_for(self, filename):
        return join(ROOT_PATH, 'tests', 'fixtures', filename)


class ApiTestCase(AsyncHTTPTestCase):
    def get_app(self):
        return self.create_api_app()

    def create_api_app(self, config=None):
        if not config:
            config = Config()
        config.MONGO_PORT = 7778
        return WightApp(config=config)

    def fetch_with_headers(self, path, **kw):
        url = self.get_url(path)

        headers = kw

        if hasattr(self, 'user') and self.user and self.user.token:
            headers['X-Wight-Auth'] = self.user.token

        req = HTTPRequest(url=url, headers=headers)

        self.http_client.fetch(req, self.stop)
        return self.wait()

    def post(self, path, **kw):
        return self.send_request("POST", path, **kw)

    def put(self, path, **kw):
        return self.send_request("PUT", path, **kw)

    def delete(self, path, **kw):
        return self.send_request("DELETE", path, **kw)

    def patch(self, path, **kw):
        return self.send_request("PATCH", path, **kw)

    def send_request(self, method, path, **kw):
        headers = {}

        if hasattr(self, 'user') and self.user and self.user.token:
            headers['X-Wight-Auth'] = self.user.token

        if 'headers' in kw:
            headers.update(kw['headers'])
            del kw['headers']

        body = ""
        if kw:
            body = urlencode(kw)

        req = HTTPRequest(self.get_url(path), method=method, headers=headers, body=body, allow_nonstandard_methods=True)
        self.http_client.fetch(req, self.stop)
        return self.wait()

    def reverse_url(self, url, *args):
        return self._app.reverse_url(url, *args)

    def setUp(self):
        AsyncTestCase.setUp(self)
        port = get_unused_port()
        sock = netutil.bind_sockets(port, 'localhost', family=socket.AF_INET)[0]
        setattr(self, '_AsyncHTTPTestCase__port', port)
        self.__port = port

        self.http_client = self.get_http_client()
        self._app = self.get_app()
        self.http_server = self.get_http_server()
        self.http_server.add_sockets([sock])


class ModelTestCase(PythonTestCase):
    @classmethod
    def setUpClass(cls):
        connect(
            "mongo-test",
            host="localhost",
            port=7778
        )

        User.objects.delete()
        Team.objects.delete()


class FullTestCase(ApiTestCase, TestCase, ModelTestCase):
    pass


class WorkerTestCase(PythonTestCase):
    pass


class WebTestCase(AsyncHTTPTestCase):
    def get_app(self):
        return self.create_web_app()

    def create_web_app(self, config=None):
        if not config:
            config = Config()

        return WightWebApp(config=config)

    def fetch_with_headers(self, path, **kw):
        url = self.get_url(path)
        headers = kw
        req = HTTPRequest(url=url, headers=headers)
        self.http_client.fetch(req, self.stop)
        return self.wait()

    def reverse_url(self, url, *args):
        return self._app.reverse_url(url, *args)

    def setUp(self):
        AsyncTestCase.setUp(self)
        port = get_unused_port()
        sock = netutil.bind_sockets(port, 'localhost', family=socket.AF_INET)[0]
        setattr(self, '_AsyncHTTPTestCase__port', port)
        self.__port = port

        self.http_client = self.get_http_client()
        self._app = self.get_app()
        self.http_server = self.get_http_server()
        self.http_server.add_sockets([sock])