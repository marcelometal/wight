#!/usr/bin/env python
# -*- coding: utf-8 -*-

# wight load testing
# https://github.com/heynemann/wight

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2013 Bernardo Heynemann heynemann@gmail.com

from preggy import expect

from wight.models import LoadTest
from tests.acceptance.base import AcceptanceTest
from tests.factories import TeamFactory


class TestSchedule(AcceptanceTest):

    def test_can_schedule(self):
        team = TeamFactory.create(owner=self.user)
        TeamFactory.add_projects(team, 2)
        project_name = team.projects[0].name

        result = self.execute("schedule", team=team.name, project=project_name, url="http://www.globo.com")
        expect(result).to_be_like(
            "Scheduled a new load test for project '%s' in team '%s' at '%s' target." % (
                project_name, team.name, self.target
            )
        )

        load_test = LoadTest.objects.filter(team=team, project_name=project_name).first()
        expect(load_test).not_to_be_null()

        expect(load_test.team.id).to_equal(team.id)
        expect(load_test.project_name).to_equal(project_name)
        expect(load_test.created_by.id).to_equal(self.user.id)

    def test_can_schedule_simple(self):
        team = TeamFactory.create(owner=self.user)
        TeamFactory.add_projects(team, 2)
        project_name = team.projects[0].name

        result = self.execute("schedule", team=team.name, project=project_name, url="http://www.globo.com", simple=True)
        expect(result).to_be_like(
            "Scheduled a new load test for project '%s' in team '%s' at '%s' target." % (
                project_name, team.name, self.target
            )
        )

        load_test = LoadTest.objects.filter(team=team, project_name=project_name).first()
        expect(load_test).not_to_be_null()

        expect(load_test.team.id).to_equal(team.id)
        expect(load_test.project_name).to_equal(project_name)
        expect(load_test.created_by.id).to_equal(self.user.id)

    def test_can_schedule_in_specific_branch(self):
        team = TeamFactory.create(owner=self.user)
        TeamFactory.add_projects(team, 2)
        project_name = team.projects[0].name

        result = self.execute("schedule", team=team.name, project=project_name, url="http://www.globo.com", branch="test-branch")
        expect(result).to_be_like(
            "Scheduled a new load test for project '%s' (branch '%s') in team '%s' at '%s' target." % (
                project_name, "test-branch", team.name, self.target
            )
        )

        load_test = LoadTest.objects.filter(team=team, project_name=project_name).first()
        expect(load_test).not_to_be_null()
        expect(load_test.git_branch).to_equal("test-branch")

    def test_can_schedule_with_default_team(self):
        team = TeamFactory.create(owner=self.user)
        TeamFactory.add_projects(team, 2)
        project_name = team.projects[0].name
        self.execute("default-set", team=team.name)
        result = self.execute("schedule", project=project_name, url="http://www.globo.com")
        expect(result).to_be_like(
            "Scheduled a new load test for project '%s' in team '%s' at '%s' target." % (
                project_name, team.name, self.target
            )
        )

        load_test = LoadTest.objects.filter(team=team, project_name=project_name).first()
        expect(load_test).not_to_be_null()

        expect(load_test.team.id).to_equal(team.id)
        expect(load_test.project_name).to_equal(project_name)
        expect(load_test.created_by.id).to_equal(self.user.id)

    def test_can_schedule_with_default_project(self):
        team = TeamFactory.create(owner=self.user)
        TeamFactory.add_projects(team, 2)
        project_name = team.projects[0].name
        self.execute("default-set", project=project_name)
        result = self.execute("schedule", team=team.name, url="http://www.globo.com")
        expect(result).to_be_like(
            "Scheduled a new load test for project '%s' in team '%s' at '%s' target." % (
                project_name, team.name, self.target
            )
        )

        load_test = LoadTest.objects.filter(team=team, project_name=project_name).first()
        expect(load_test).not_to_be_null()

        expect(load_test.team.id).to_equal(team.id)
        expect(load_test.project_name).to_equal(project_name)
        expect(load_test.created_by.id).to_equal(self.user.id)

    def test_can_schedule_with_default_team_and_project(self):
        team = TeamFactory.create(owner=self.user)
        TeamFactory.add_projects(team, 2)
        project_name = team.projects[0].name
        self.execute("default-set", project=project_name, team=team.name)
        result = self.execute("schedule", url="http://www.globo.com")
        expect(result).to_be_like(
            "Scheduled a new load test for project '%s' in team '%s' at '%s' target." % (
                project_name, team.name, self.target
            )
        )

        load_test = LoadTest.objects.filter(team=team, project_name=project_name).first()
        expect(load_test).not_to_be_null()

        expect(load_test.team.id).to_equal(team.id)
        expect(load_test.project_name).to_equal(project_name)
        expect(load_test.created_by.id).to_equal(self.user.id)
