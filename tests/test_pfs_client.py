#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the `PfsClient` class of the `pypachy` package."""


from collections import namedtuple
import os
import pytest
import pypachy


@pytest.fixture(scope='function')
def pfs_client():
    """Connect to Pachyderm before tests and reset to initial state after tests."""
    # Setup : create a PfsClient instance
    client = pypachy.PfsClient()

    yield client  # this is where the testing happens

    # Teardown : Delete all repos, commits, files, pipelines and jobs.  This resets the cluster to its initial state.
    client.delete_all()


# Repository types : [name: str, description: str]
Repo = namedtuple('Repo', ['name', 'description'])

# Repository test examples
repos_to_test = (Repo(name='test', description='This is a test repository'),
                 Repo(name='test2', description=''))


@pytest.fixture(scope='function', params=repos_to_test)
def pfs_client_with_repo(request):
    """Connect to Pachyderm before tests and reset to initial state after tests."""
    # Setup : create a PfsClient instance and create a repository
    client = pypachy.PfsClient()
    client.create_repo(request.param.name, request.param.description)

    yield client, request.param  # this is where the testing happens

    # Teardown : Delete all repos, commits, files, pipelines and jobs.  This resets the cluster to its initial state.
    client.delete_all()


def test_pfs_client_init_with_default_host_port():
    # GIVEN a Pachyderm deployment
    # WHEN a client is created without specifying a host or port
    client = pypachy.PfsClient()
    # THEN the GRPC channel should reflect the default of localhost and port 30650
    assert client.channel._channel.target() == b'localhost:30650'


def test_pfs_client_init_with_env_vars(monkeypatch):
    # GIVEN a Pachyderm deployment
    # WHEN environment variables are set for Pachyderm host and port
    monkeypatch.setenv('PACHD_SERVICE_HOST', 'pachd.example.com')
    monkeypatch.setenv('PACHD_SERVICE_PORT_API_GRPC_PORT', '12345')
    #   AND a client is created without specifying a host or port
    client = pypachy.PfsClient()
    # THEN the GRPC channel should reflect the host and port specified in the environment variables
    assert client.channel._channel.target() == b'pachd.example.com:12345'


def test_pfs_client_init_with_args():
    # GIVEN a Pachyderm deployment
    # WHEN a client is created with host and port arguments
    client = pypachy.PfsClient(host='pachd.example.com', port=54321)
    # THEN the GRPC channel should reflect the host and port specified in the arguments
    assert client.channel._channel.target() == b'pachd.example.com:54321'


def test_pfs_list_repo(pfs_client):
    # GIVEN a Pachyderm deployment in its initial state
    #   AND a connected PFS client
    client = pfs_client
    # WHEN calling list_repo()
    repo_info = client.list_repo()
    # THEN an empty list should be returned
    assert list(repo_info) == []


def test_pfs_create_repo(pfs_client):
    # GIVEN a Pachyderm deployment in its initial state
    #   AND a connected PFS client
    client = pfs_client
    # WHEN calling create_repo() with a name but no description
    repo_name = 'test'
    client.create_repo(repo_name)
    #   AND calling list_repo()
    repo_info = client.list_repo()
    # THEN only one repository should exist
    assert len(repo_info) == 1
    #   AND the repo name should match the specified value
    assert repo_info[0].repo.name == repo_name
    #   AND the description should be empty
    assert repo_info[0].description == ''
    #   AND the size in Bytes should be 0
    assert repo_info[0].size_bytes == 0
    #   AND provenance should be empty
    assert len(repo_info[0].provenance) == 0


def test_pfs_create_repo_with_description(pfs_client):
    # GIVEN a Pachyderm deployment in its initial state
    #   AND a connected PFS client
    client = pfs_client
    # WHEN calling create_repo() with a name and description
    repo_name = 'test'
    repo_description = 'This is a test repository'
    client.create_repo(repo_name, repo_description)
    #   AND calling list_repo()
    repo_info = client.list_repo()
    # THEN only one repository should exist
    assert len(repo_info) == 1
    #   AND the repo name should match the specified value
    assert repo_info[0].repo.name == repo_name
    #   AND the description should match the specified value
    assert repo_info[0].description == repo_description
    #   AND the size in Bytes should be 0
    assert repo_info[0].size_bytes == 0
    #   AND provenance should be empty
    assert len(repo_info[0].provenance) == 0


def test_pfs_inspect_repo(pfs_client_with_repo):
    # GIVEN a Pachyderm deployment with one existing repo
    #   AND a connected PFS client
    client, test_repo = pfs_client_with_repo
    # WHEN calling inspect_repo() with a name but no description
    client.inspect_repo(test_repo.name)
    #   AND calling list_repo()
    repo_info = client.list_repo()
    # THEN only one repository should exist
    assert len(repo_info) == 1
    #   AND the repo name should match the specified value
    assert repo_info[0].repo.name == test_repo.name
    #   AND the description should be empty
    assert repo_info[0].description == test_repo.description
    #   AND the size in Bytes should be 0
    assert repo_info[0].size_bytes == 0
    #   AND provenance should be empty
    assert len(repo_info[0].provenance) == 0


def test_pfs_delete_repo(pfs_client_with_repo):
    # GIVEN a Pachyderm deployment
    #   AND a connected PFS client
    client, test_repo = pfs_client_with_repo
    #   AND one existing repo
    assert len(client.list_repo()) == 1
    # WHEN calling delete_repo() with the repo_name of the existing repo
    client.delete_repo(test_repo.name)
    # THEN no repositories should remain
    assert len(client.list_repo()) == 0


def test_pfs_delete_repo_raises(pfs_client_with_repo):
    # GIVEN a Pachyderm deployment
    #   AND a connected PFS client
    client, test_repo = pfs_client_with_repo
    #   AND one existing repo
    assert len(client.list_repo()) == 1
    # WHEN calling delete_repo() without specifying a repo_name
    with pytest.raises(ValueError) as excinfo:
        client.delete_repo()
    exception_msg = excinfo.value.args[0]
    # THEN the error message should indicate that a repo_name cannot be specified when calling with all=True
    assert exception_msg == 'Either a repo_name or all=True needs to be provided'


def test_pfs_delete_non_existant_repo_raises(pfs_client_with_repo):
    # GIVEN a Pachyderm deployment
    #   AND a connected PFS client
    client, test_repo = pfs_client_with_repo
    #   AND one existing repo
    assert len(client.list_repo()) == 1
    # WHEN calling delete_repo() with a non-existant repo_name
    with pytest.raises(Exception) as excinfo:
        client.delete_repo('BOGUS_NAME')
    # THEN a grpc._channel._Rendezvous exception should be raised
    assert excinfo.typename == '_Rendezvous'
    #   AND the error message should indicate that the repo does not exist
    assert excinfo.match('cannot delete "BOGUS_NAME" as it does not exist')


def test_pfs_delete_all_repos(pfs_client):
    # GIVEN a Pachyderm deployment in its initial state
    #   AND a connected PFS client
    client = pfs_client
    #   AND two existing repos
    client.create_repo('test-repo-1')
    client.create_repo('test-repo-2')
    assert len(client.list_repo()) == 2
    # WHEN calling delete_repo() with all=True
    client.delete_repo(all=True)
    # THEN no repositories should remain
    assert len(client.list_repo()) == 0


def test_pfs_delete_all_repos_with_name_raises(pfs_client):
    # GIVEN a Pachyderm deployment in its initial state
    #   AND a connected PFS client
    client = pfs_client
    #   AND two existing repos
    client.create_repo('test-repo-1')
    client.create_repo('test-repo-2')
    assert len(client.list_repo()) == 2
    # WHEN calling delete_repo() with a repo_name and all=True
    with pytest.raises(ValueError) as excinfo:
        client.delete_repo('test-repo-1', all=True)
    exception_msg = excinfo.value.args[0]
    # THEN the error message should indicate that a repo_name cannot be specified when calling with all=True
    assert exception_msg == 'Cannot specify a repo_name if all=True'
    #   AND both repositories should remain
    assert len(client.list_repo()) == 2