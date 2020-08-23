# Test suite based on py.test.
# This test suite requires the following to have previously been setup:
# 1. an (external) APIM manager installation, such as the dev.tenants.sandbox.agaveapi.co instance.
# 2. A Test API registered and published in the APIM instance above with attributes given as in the sub_attrs fixture.
# 3. clients service configuration pointing to the above APIM instance in the local_settings.py file (in particular,
#    the tenant_host setting.)
#
#
# To run the test suite:
# Make sure the clients service is running on BASE_URL defined below. In particular, to run the tests against the
# django development server, simply:
# 1. activate a virtualenv with the requirements installed. (Note that to build the virtualenv you may need to
#    sudo apt-get install libmysqlclient-dev in Ubuntu distributions).
# 2. Make sure test_settings.py is configured for the appropriate instance of APIM (see #3 above).
# 3. start the dev server (e.g. python manage.py runserver 0.0.0.0:9000)
# 4. run the tests by entering `py.test` in this directory.
#
# 5*.(optional) if the clients service is running in another location, point the test suite at it by exporting
#     base_url=<location>:<port>
# 6*. (optional). change the account used to authenticated to APIM by exporting username and password.


import os
import json

import base64
import pytest
import requests


BASE_URL = os.environ.get('base_url', 'http://127.0.0.1:9000')
username = os.environ.get('username', 'testuser')
password = os.environ.get('password', 'testuser')

AGAVE_API_VERSION = 'v2'
AGAVE_APIS = [{'name':'Apps', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Files', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Jobs', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Meta', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Monitors', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Notifications', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Postits', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Profiles', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Systems', 'version':AGAVE_API_VERSION, 'provider':'admin'},
            {'name':'Transforms', 'version':AGAVE_API_VERSION, 'provider':'admin'},]


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

@pytest.fixture(scope='session')
def sub_attrs():
    """Return attributes for the test subscription."""
    sub_attrs = {'apiName': 'Test',
                 'apiVersion': 'v0.1',
                 'apiProvider': 'admin',
                 'tier': 'Unlimited'}
    return sub_attrs


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
    print(json.dumps(data, indent=2, sort_keys=False))
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

def validate_subscription(sub):
    assert 'apiName' in sub
    assert 'apiContext' in sub
    assert 'apiProvider' in sub
    assert 'apiStatus' in sub
    assert 'apiVersion' in sub
    assert 'tier' in sub
    assert '_links' in sub

def delete_client(client_attrs):
    """Ensure the test client is deleted in case of a previous failed run."""
    url = '{}/clients/v2/{}'.format(BASE_URL, client_attrs.get('clientName'))
    rsp = requests.delete(url)
    validate_response(rsp)


# -----
# Tests
# -----

def test_list_clients(headers, client_attrs):
    url = '{}/clients/v2?pretty=true'.format(BASE_URL)
    rsp = requests.get(url, headers=headers)
    clients = validate_response(rsp)
    for client in clients:
        validate_client(client, secret_present=False)
        if client.get('name') == client_attrs.get('clientName'):
            delete_client(client_attrs)

def test_create_client(headers, client_attrs):
    url = '{}/clients/v2?pretty=true'.format(BASE_URL)
    rsp = requests.post(url, data=client_attrs, headers=headers)
    client = validate_response(rsp)
    validate_client(client, secret_present=True)

def test_list_client_details(headers, client_attrs):
    url = '{}/clients/v2/{}?pretty=true'.format(BASE_URL, client_attrs.get('clientName'))
    rsp = requests.get(url, headers=headers)
    client = validate_response(rsp)
    validate_client(client)
    assert client.get('name') == client_attrs.get('clientName')
    assert client.get('description') == client_attrs.get('description')
    assert client.get('callbackUrl') == client_attrs.get('callbackUrl')
#
# def test_list_subscriptions(headers, client_attrs):
#     url = '{}/clients/v2/{}/subscriptions?pretty=true'.format(BASE_URL, client_attrs.get('clientName'))
#     rsp = requests.get(url, headers=headers)
#     subs = validate_response(rsp)
#     assert len(subs) >= len(AGAVE_APIS)
#     for sub in subs:
#         validate_subscription(sub)
#         assert sub.get('apiName') in [api.get('name') for api in AGAVE_APIS]
#     for api in AGAVE_APIS:
#         assert api.get('name') in [sub.get('apiName') for sub in subs]
#
# def test_add_subscription(headers, client_attrs, sub_attrs):
#     url = '{}/clients/v2/{}/subscriptions'.format(BASE_URL, client_attrs.get('clientName'))
#     rsp = requests.post(url, data=sub_attrs, headers=headers)
#     validate_response(rsp)
#
# def test_ensure_added_subscription_present(headers, client_attrs, sub_attrs):
#     url = '{}/clients/v2/{}/subscriptions?pretty=true'.format(BASE_URL, client_attrs.get('clientName'))
#     rsp = requests.get(url, headers=headers)
#     subs = validate_response(rsp)
#     for sub in subs:
#         if sub.get('apiName') == sub_attrs.get('apiName'):
#             break
#     else:
#         # didn't find the subscription
#         assert False
#
# def test_delete_subscription(headers, client_attrs, sub_attrs):
#     url = '{}/clients/v2/{}/subscriptions?pretty=true'.format(BASE_URL, client_attrs.get('clientName'))
#     rsp = requests.delete(url, headers=headers, data=sub_attrs)
#     validate_response(rsp)
#
# def test_ensure_deleted_subscription_gone(headers, client_attrs, sub_attrs):
#     url = '{}/clients/v2/{}/subscriptions'.format(BASE_URL, client_attrs.get('clientName'))
#     rsp = requests.get(url, headers=headers)
#     subs = validate_response(rsp)
#     for sub in subs:
#         if sub.get('apiName') == sub_attrs.get('apiName'):
#             # found the test subscription
#             assert False
#
# def test_delete_all_subscriptions(headers, client_attrs):
#     url = '{}/clients/v2/{}/subscriptions'.format(BASE_URL, client_attrs.get('clientName'))
#     data = {'apiName': '*'}
#     rsp = requests.delete(url, headers=headers, data=data)
#     validate_response(rsp)
#
# def test_ensure_all_subscriptions_gone(headers, client_attrs):
#     url = '{}/clients/v2/{}/subscriptions?pretty=true'.format(BASE_URL, client_attrs.get('clientName'))
#     rsp = requests.get(url, headers=headers)
#     subs = validate_response(rsp)
#     assert len(subs) == 0
#
# def test_add_core_api_subscription(headers, client_attrs):
#     url = '{}/clients/v2/{}/subscriptions?pretty=true'.format(BASE_URL, client_attrs.get('clientName'))
#     data = {'apiName': 'Files',
#             'apiVersion': 'v2',
#             'apiProvider': 'admin',
#             'tier': 'Unlimited'}
#     rsp = requests.post(url, data=data, headers=headers)
#     validate_response(rsp)
#
# def test_ensure_added_core_subscription_present(headers, client_attrs):
#     url = '{}/clients/v2/{}/subscriptions?pretty=true'.format(BASE_URL, client_attrs.get('clientName'))
#     rsp = requests.get(url, headers=headers)
#     subs = validate_response(rsp)
#     for sub in subs:
#         if sub.get('apiName') == 'Files':
#             break
#     else:
#         # didn't find the subscription
#         assert False

def test_delete_client(headers, client_attrs):
    url = '{}/clients/v2/{}?pretty=true'.format(BASE_URL, client_attrs.get('clientName'))
    rsp = requests.delete(url, headers=headers)
    client = validate_response(rsp)

def test_ensure_deleted_client_gone(headers, client_attrs):
    url = '{}/clients/v2?pretty=true'.format(BASE_URL)
    rsp = requests.get(url, headers=headers)
    clients = validate_response(rsp)
    for client in clients:
        validate_client(client)
        if client.get('name') == client_attrs.get('clientName'):
            assert False

