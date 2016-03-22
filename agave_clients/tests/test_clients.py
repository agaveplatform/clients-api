# new test suite based on py.test.
# Make sure the clients service is running on BASE_URL defined below. In particular, to run the tests against the
# django development server, simply:
# 1. activate a virtualenv with the requirements installed.
# 2. start the dev server (e.g. python manage.py runserver 0.0.0.0:9000)
# 3. point the test suite at the instance by updating BASE_URL=127.0.0.1:9000 or exporting base_url=127.0.0.1:9000
# 4. run the tests by entering `py.test` in this directory.

import os
import json

import base64
import pytest
import requests

BASE_URL = os.environ.get('base_url', 'http://127.0.0.1:9000')
username = os.environ.get('username', 'jdoe')
password = os.environ.get('password', 'abcde')


# --------
# Fixtures
# --------
@pytest.fixture(scope='session')
def headers():
    """Return headers valid for a test request."""
    return {'AUTHORIZATION': http_auth(username, password)}

@pytest.fixture(scope='session')
def client_attrs():
    """Return attributes for the test client."""
    client_attrs = {'clientName': 'agave_clients_testsuite_test_client',
                    'callbackUrl': 'http://localhost:9000/oauth/token',
                    'description': 'agave_clients testsuite client.'}
    return client_attrs


# ----------------
# Helper functions
# ----------------

def http_auth(username, password):
    credentials = base64.encodestring('{}:{}'.format(username, password)).strip()
    auth_string = 'Basic {}'.format(credentials)
    return auth_string

def validate_response(rsp):
    """Basic validation of a response."""
    assert rsp.status_code in [200, 201]
    assert 'application/json' in rsp.headers['content-type']
    data = json.loads(rsp.content)
    assert 'message' in data.keys()
    assert 'status' in data.keys()
    assert 'result' in data.keys()
    assert 'version' in data.keys()
    return data['result']

def validate_client(client, secret_present=False):
    """Basic validation of a client object."""
    assert 'consumerKey' in client
    if secret_present:
        assert 'consumerSecret' in client
    else:
        assert not 'consumerSecret' in client
    assert 'name' in client
    assert 'description' in client
    assert 'tier' in client
    assert 'callbackUrl' in client
    assert '_links' in client

def delete_client(client_attrs):
    """Ensure the test client is deleted in case of a previous failed run."""
    url = '{}/clients/v2/{}'.format(BASE_URL, client_attrs.get('clientName'))
    rsp = requests.delete(url)
    validate_response(rsp)


# -----
# Tests
# -----

def test_list_clients(headers, client_attrs):
    url = '{}/clients/v2'.format(BASE_URL)
    rsp = requests.get(url, headers=headers)
    clients = validate_response(rsp)
    for client in clients:
        validate_client(client)
        if client.get('name') == client_attrs.get('clientName'):
            delete_client(client_attrs)

def test_create_client(headers, client_attrs):
    url = '{}/clients/v2'.format(BASE_URL)
    rsp = requests.post(url, data=client_attrs, headers=headers)
    client = validate_response(rsp)
    validate_client(client, secret_present=True)

def test_list_client_details(headers, client_attrs):
    url = '{}/clients/v2/{}'.format(BASE_URL, client_attrs.get('clientName'))
    rsp = requests.get(url, headers=headers)
    client = validate_response(rsp)
    validate_client(client)
    assert client.get('name') == client_attrs.get('clientName')
    assert client.get('description') == client_attrs.get('description')
    assert client.get('callbackUrl') == client_attrs.get('callbackUrl')

def test_delete_client(headers, client_attrs):
    url = '{}/clients/v2/{}'.format(BASE_URL, client_attrs.get('clientName'))
    rsp = requests.delete(url, headers=headers)
    client = validate_response(rsp)

def test_ensure_deleted_client_gone(headers, client_attrs):
    url = '{}/clients/v2'.format(BASE_URL)
    rsp = requests.get(url, headers=headers)
    clients = validate_response(rsp)
    for client in clients:
        validate_client(client)
        if client.get('name') == client_attrs.get('clientName'):
            assert False
