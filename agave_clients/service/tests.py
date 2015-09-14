import sys
import os
APP_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..')
print APP_DIR
for idx, p in enumerate(sys.path):
    if p == APP_DIR:
        sys.path.pop(idx)

sys.path.append(os.path.abspath(os.path.join(APP_DIR,'..')))
# print sys.path

import base64
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase
import requests

from common.error import Error
from agave_clients.service import views

# ------------------------
# INSTRUCTIONS AND WARNING
# ------------------------
# These tests run against the APIM instance and database included in the local_settings.py file. 
# That database MIGHT BE CHANGED as a result of running these tests.
#
# Run the tests with:
# python manage.py test service
#
# Make sure to have installed all requirements in a virtualenv and activate the virtualenv before running the tests.
# On ubuntu, you will need the libmysqlclient-dev package (sudo apt-get install libmysqlclient-dev) before you can
# pip install the MySQL-python library.
#
# --------------
# Configuration:
# -------------
# User credentials to run the tests against. This account must be valid in some user store configured for
# the API Manager instance located at settings.APIM_STORE_SERVICES_BASE_URL.
USERNAME = 'jdoe'
PASSWORD = 'abcde'

logger = logging.getLogger(__name__)

def http_auth(username, password):
    credentials = base64.encodestring('%s:%s' % (username, password)).strip()
    auth_string = 'Basic %s' % credentials
    return auth_string


class ClientsTests(APITestCase):
    """
    Tests for the /clients endpoints.
    """
    def setUp(self):
        # set up auth for the user account first:
        self.extra = {
            'HTTP_AUTHORIZATION': http_auth(USERNAME, PASSWORD)
        }
        # set up the clients -- login:
        url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_AUTH_URL
        data = {'action': 'login',
                'username': USERNAME,
                'password': PASSWORD}
        try:
            r = requests.post(url, data, verify=False)
        except Exception as e:
            raise Error("Unable to authn to store; " + str(e))
        if not r.status_code == 200:
            raise Error("Unable to authenticate user; status code: "
                        + str(r.status_code) + "msg:" + str(r.content))
        if r.json().get("error"):
            raise Error("Unable to create clients - could not login: " + str(r.json()))

        self.cookies = r.cookies
        # create client:
        url = settings.APP_BASE + "/clients/v2/"
        data = {'clientName': 'testerapp123',
                'description': 'App created by testing suite.',
                'callbackUrl': 'http://localhost:8000/testerapp123/oauth/'}
        r = self.client.post(url, data, format="json", **self.extra)
        self.application_id = views.get_application_id(self.cookies, username=USERNAME,
                                                       application_name="testerapp123")
        # add a subscription:
        url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_SUBSCRIPTION_URL
        data = {'action': 'addSubscription',
                'name': 'Apps',
                'version': 'v2',
                'provider': 'admin',
                'tier': 'Unlimited',
                'applicationId': self.application_id}
        try:
            r = requests.post(url, cookies=self.cookies, data=data, verify=False)
        except Exception as e:
            raise Error("Unable to add subscription in created application; " + str(e))

    def tearDown(self):
        url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_REMOVE_APP_URL
        params = {'action': 'removeApplication',
                  'application': 'testerapp123',}
        try:
            r = requests.post(url, cookies=self.cookies, params=params, verify=False)
        except:
            pass

        # delete the client created in the tests:
        url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_REMOVE_APP_URL
        params = {'action': 'removeApplication',
                  'application': 'test_client_12345'}
        try:
            r = requests.post(url, cookies=self.cookies, params=params, verify=False)
        except:
            pass

    # ------------------
    # TESTS
    # ------------------
    # def test_list_clients(self):
    #     url = settings.APP_BASE + "/clients/v2"
    #     r = self.client.get(url, format="json", **self.extra)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)
    #     self.assertEqual(r.data.get("status"), "success")
    #     result = r.data.get("result")
    #     found = False
    #     for client in result:
    #         assert not 'consumerSecret' in client
    #         logger.info('found client: ' + str(client.get('name')))
    #         if client.get("name") == "testerapp123":
    #             found = True
    #     self.assertEqual(found, True)

    def test_retrieve_client_details(self):
        url = settings.APP_BASE + "/clients/v2/testerapp123"
        r = self.client.get(url, format="json", **self.extra)
        self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
                                             + " response: " + r.content)
        self.assertEqual(r.data.get("status"), "success")
        client = r.data.get("result")
        self.assertEqual(client.get("name"), "testerapp123")
        self.assertEqual(client.get("description"), "App created by testing suite.")
        self.assertEqual(client.get("tier"), "Unlimited")
        self.assertEqual(client.get("callbackUrl"), "http://localhost:8000/testerapp123/oauth/")
        self.assertEqual(client.get("_links").get('self').get('href'), settings.APP_BASE + '/clients/v2/testerapp123')
        self.assertEqual(client.get("_links").get('subscriber').get('href'), settings.APP_BASE + '/profiles/v2/' + USERNAME)
        self.assertEqual(client.get("_links").get('subscriptions').get('href'),
                         settings.APP_BASE + '/clients/v2/testerapp123/subscriptions/')
        assert client.get("consumerKey")
        assert not 'consumerSecret' in client
        assert not 'validityTime' in client
        assert not 'enableRegenarate' in client
        assert not 'accessToken' in client
        assert not 'accessallowdomains' in client
        assert not 'validityTime' in client
        assert not 'id' in client

    # def test_list_subscriptions(self):
    #     url = settings.APP_BASE + "/clients/v2/testerapp123/subscriptions"
    #     r = self.client.get(url, format="json", **self.extra)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)
    #     self.assertEqual(r.data.get("status"), "success")
    #     subs = r.data.get("result")
    #     self.assertEqual(len(subs), 10)
    #     found = False
    #     for sub in subs:
    #         if sub.get("apiName") == "Apps":
    #             found = True
    #             self.assertEqual(sub.get("apiProvider"), "admin")
    #             self.assertEqual(sub.get("apiStatus"), "PUBLISHED")
    #             self.assertEqual(sub.get("apiContext"), "/apps")
    #             self.assertEqual(sub.get("apiName"), "Apps")
    #             self.assertEqual(sub.get("tier"), "Unlimited")
    #             self.assertEqual(sub.get("apiVersion"), "v2")
    #             self.assertEqual(sub.get("_links").get('self').get('href'), settings.APP_BASE + '/clients/v2/testerapp123/subscriptions/')
    #             self.assertEqual(sub.get("_links").get('api').get('href'), settings.APP_BASE + '/apps/v2/')
    #             self.assertEqual(sub.get("_links").get('client').get('href'), settings.APP_BASE + '/clients/v2/testerapp123')
    #     assert found
    #     assert not 'prodConsumerKey' in sub
    #     assert not 'prodConsumerSecret' in sub
    #     assert not 'prodKey' in sub
    #     assert not 'sandboxConsumerKey' in sub
    #     assert not 'sandboxConsumerSecret' in sub

    # def test_create_client(self):
    #     url = settings.APP_BASE + "/clients/v2/"
    #     data = {'clientName': 'test_client_12345',
    #             'description': 'Test client created by test suite.',
    #             'callbackUrl': 'http://localhost:8000/testclient/oauth/'}
    #     rsp = self.client.post(url, data, format="json", **self.extra)
    #     self.assertEqual(rsp.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(rsp.data.get("status"), "success")
    #     self.assertEqual(rsp.data.get("result").get("name"), "test_client_12345")
    #     self.assertEqual(rsp.data.get("result").get("callbackUrl"), "http://localhost:8000/testclient/oauth/")
    #     self.assertEqual(rsp.data.get("result").get("description"), "Test client created by test suite.")
    #     self.consumerKey = rsp.data.get("result").get("consumerKey")
    #     self.consumerSecret = rsp.data.get("result").get("consumerSecret")
    #     self.encoded_keys = http_auth(self.consumerKey, self.consumerSecret)
    #
    #     # get an access token with the newly generated keys:
    #     url = 'https://' + settings.TENANT_HOST + '/token'
    #     data = {"grant_type": "password",
    #             "username": USERNAME,
    #             "password": PASSWORD,
    #             "scope": "PRODUCTION",}
    #
    #     r = requests.post(url,
    #                       data,
    #                       headers={'Authorization': 'Basic' + self.encoded_keys,
    #                                'Content-Type': 'application/x-www-form-urlencoded'},
    #                       verify=False)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)
    #     self.access_token = r.json().get("access_token")
    #     # make a call to an API with the access token to make sure everything works:
    #     url = 'https://' + settings.TENANT_HOST + '/apps/v2/'
    #     r = requests.get(url,
    #                      headers={'Authorization': 'Bearer ' + self.access_token},
    #                      verify=False)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)

    # def test_update_client(self):
    #     url = settings.APP_BASE + '/clients/v2/testerapp123/subscriptions/'
    #     data = {'apiName': '*'}
    #     r = self.client.post(url, data, format="json", **self.extra)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)
    #     self.assertEqual(r.data.get("status"), "success")

    # def test_add_one_subscription(self):
    #     url = settings.APP_BASE + '/clients/v2/testerapp123/subscriptions'
    #     data = {'apiName': 'Files',
    #             'apiVersion': 'v2',
    #             'apiProvider': 'admin'}
    #     r = self.client.post(url, data, format="json", **self.extra)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)
    #     self.assertEqual(r.data.get("status"), "success")
    #
    #
    # def test_delete_client(self):
    #     url = settings.APP_BASE + '/clients/v2/testerapp123'
    #     r = self.client.delete(url, format="json", **self.extra)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)
    #     self.assertEqual(r.data.get("status"), "success")
    #
    #
    # def test_delete_subscription(self):
    #     url = settings.APP_BASE + '/clients/v2/testerapp123/subscriptions'
    #     data = {'apiName': 'Apps',
    #             'apiVersion': 'v2',
    #             'apiProvider': 'admin'}
    #     r = self.client.delete(url, data, format="json", **self.extra)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)
    #     self.assertEqual(r.data.get("status"), "success")
    #
    # def test_delete_all_subscriptions(self):
    #     url = settings.APP_BASE + '/clients/v2/testerapp123/subscriptions'
    #     data = {'apiName': '*'}
    #     r = self.client.delete(url, data, format="json", **self.extra)
    #     self.assertEqual(r.status_code, 200, "Wrong status code: " + str(r.status_code)
    #                                          + " response: " + r.content)
    #     self.assertEqual(r.data.get("status"), "success")
