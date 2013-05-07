#!/usr/bin/env python
# -*- coding: utf-8 -*-

# wight load testing
# https://github.com/heynemann/wight

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2013 Bernardo Heynemann heynemann@gmail.com

import os

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from preggy import expect
from mock import patch

from wight.cli.base import WightDefaultController, WightBaseController
from wight.models import UserData
from wight.errors import TargetNotSetError
import wight.cli.base as base

from tests.base import TestCase


class TestBaseController(TestCase):
    @patch.object(base.requests, 'post')
    def test_make_a_post(self, post_mock):
        ctrl = self.make_controller(WightBaseController, conf=self.fixture_for('test.conf'))
        ctrl.app.user_data = UserData(target="Target")
        ctrl.post("/post-url", data={"some": "data"})
        expect(post_mock.called).to_be_true()

    @patch.object(base.requests, 'post')
    def test_make_a_post_with_correct_values(self, post_mock):
        ctrl = self.make_controller(WightBaseController, conf=self.fixture_for('test.conf'))
        ctrl.app.user_data = UserData(target="Target")
        ctrl.app.user_data.token = "token-value"
        ctrl.post("/post-url", data={"some": "data"})
        post_mock.assert_called_with(
            "Target/post-url",
            data={"some": "data", "target": "Target"},
            headers={"X-Wight-Auth": "token-value"}
        )

    def test_authenticated_decorator(self):
        class TestAuthController(WightBaseController):
            @WightBaseController.authenticated
            def default(self):
                pass

        ctrl = self.make_controller(TestAuthController)
        try:
            ctrl.default()
        except TargetNotSetError:
            assert True
            return

        assert False, "Should not have gotten this far"


class TestDefaultHandler(TestCase):

    def test_meta_label(self):
        expect(WightDefaultController.Meta.label).to_equal('base')

    def test_meta_desc(self):
        expect(WightDefaultController.Meta.description).to_equal('wight load testing scheduler and tracker.')

    @patch('sys.stdout', new_callable=StringIO)
    def test_default_action(self, mock_stdout):
        expected = """
        usage: nosetests [-h] [--debug] [--quiet]

        optional arguments:
        -h, --help  show this help message and exit
        --debug     toggle debug output
        --quiet     suppress all output"""

        ctrl = self.make_controller(WightDefaultController)
        ctrl.default()

        expect(mock_stdout.getvalue()).to_be_like(expected)

    def test_load_conf(self):
        ctrl = self.make_controller(WightDefaultController, conf=self.fixture_for('test.conf'))
        ctrl.load_conf()

        expect(ctrl.config).not_to_be_null()

    def test_load_conf_that_does_not_exist(self):
        ctrl = self.make_controller(WightDefaultController, conf=self.fixture_for('invalid.conf'))
        ctrl.load_conf()

        expect(ctrl.config).not_to_be_null()

    def test_default_path_load_conf(self):
        ctrl = self.make_controller(WightDefaultController, conf=None)

        with open(UserData.DEFAULT_PATH, 'w') as f:
            f.write('')

        try:
            ctrl.load_conf()

            expect(ctrl.config).not_to_be_null()
            expect(ctrl.config.config_file).to_equal(UserData.DEFAULT_PATH)
        finally:
            os.remove(UserData.DEFAULT_PATH)
