'''
Views for the Agave clients service. Allows creation and
management of APIM clients through a RESTful web interface.
'''

import logging
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from pycommon import auth
from pycommon.error import Error
from pycommon.responses import error_dict, success_dict, format_response, error_response, success_response

from agave_clients.service.models import IdnOauthConsumerApps, AmApplicationKeyMapping


# Get an instance of a logger
logger = logging.getLogger(__name__)

AGAVE_APIS = [{'name':'Apps',          'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Files',         'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Jobs',          'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Meta',          'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Monitors',      'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Notifications', 'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Postits',       'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Profiles',      'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Systems',       'version':settings.AGAVE_API_VERSION, 'provider':'admin'},
              {'name':'Transforms',    'version':settings.AGAVE_API_VERSION, 'provider':'admin'},]

AGAVE_APIS.extend(settings.ADDITIONAL_APIS)

class Clients(APIView):

    def perform_authentication(self, request):
        pass

    @auth.authenticated
    def get(self, request, format=None):
        """
        List all client applications for a user.
        username -- (REQUIRED)
        password -- (REQUIRED)
        """

        try:
            applications = get_applications(request.wso2_cookies, request.wso2_username,)
        except Error as e:
            return error_response(msg=e.message)
        except Exception as e:
            logger.error("Uncaught exception trying to retrieve clients: " + str(e))
            return error_response(msg=e.message)
        return HttpResponse(format_response(response_data=applications, msg="Clients retrieved successfully.",
                                        query_dict=request.query_params), content_type='application/json')

    @auth.authenticated
    def post(self, request, format=None):
        """
        Create a new client that is subscribed to the Agave APIs.

        client_name -- (REQUIRED) The name of the application to create
        tier -- subscription tier
        description -- Description of the application
        callbackUrl -- Callback URL for OAuth authorization grant flow.
        """
        parms = ['clientName']
        try:
            parm_values = get_parms_from_request(request.data, parms)
            application = create_client_application(request.wso2_cookies,
                                                    request.wso2_username,
                                                    parm_values['clientName'],
                                                    tier=request.data.get('tier', settings.DEFAULT_TIER),
                                                    description=request.data.get('description',''),
                                                    callbackUrl=request.data.get('callbackUrl', ''))
            logger.info(application)
            logger.info("Application created, id:" + str(application.get('application_id')))
            # add_apis(request.wso2_cookies, application.get('id'))
        except Error as e:
            return error_response(msg=e.message)
        except Exception as e:
            logger.error("Uncaught exception trying to create a new client: " + e.message)
            return error_response(msg=e.message)

        # we need to sanitize the application, but sanitize will remove the consumerSecret, which in
        # this one case we actually want to send back to the user:
        secret = application.pop("consumerSecret", None)
        sanitize_app(application)
        application['consumerSecret'] = secret
        return HttpResponse(format_response(msg="Client created successfully.",
                                     response_data=application, query_dict=request.query_params),
                        status=status.HTTP_201_CREATED, content_type='application/json')

class ClientDetails(APIView):
    def perform_authentication(self, request):
        pass

    @auth.authenticated
    def delete(self, request, client_name, format=None):
        """
        Remove a client.
        """
        try:
            delete_client(request.wso2_cookies, client_name)
        except Error as e:
            logger.error("Exception trying to remove client: " + str(e))
            return error_response(msg=e.message)
        except Exception as e:
            logger.error("Uncaught exception trying to remove client: " + str(e))
            return error_response(msg=e.message)

        return HttpResponse(format_response(response_data=None, msg="Client removed successfully.",
                                        query_dict=request.query_params),
                                        content_type='application/json')

    @auth.authenticated
    def get(self, request, client_name, format=None):
        """
        Retrieve details for a client.
        """
        try:
            app = get_application(request.wso2_cookies, request.wso2_username, client_name)
        except Error as e:
            return error_response(msg=e.message)
        except Exception as e:
            logger.error("Uncaught exception trying to retrieve client details: " + str(e))

            return error_response(msg=e.message)
        return HttpResponse(format_response(msg="Client details retrieved successfully.",
                                        response_data=app, query_dict=request.query_params), content_type='application/json')

class ClientSubscriptions(APIView):
    def perform_authentication(self, request):
        pass

    @auth.authenticated
    def get(self, request, client_name, format=None):
        """
        Retrieve subscriptions for a client.
        """
        try:
            subscriptions = get_subscriptions(request.wso2_cookies, client_name)
        except Error as e:
            return error_response(msg=e.message)
        except Exception as e:
            logger.error("Unhandled exception in ClientSubscription: " + str(e))
            return error_response(msg="Unable to retrieve subscriptions.")
        return HttpResponse(format_response(msg="Client subscriptions retrieved successfully.",
                                     response_data=subscriptions, query_dict=request.query_params),
                        content_type='application/json')

    @auth.authenticated
    def post(self, request, client_name, format=None):
        """
        Add subscriptions to the client provided.
        apiNme -- (REQUIRED) The name of the API to subscribe to; Send api_name=* to subscribe to all APIs.
        apiVersion -- Version of the API to be added.
        apiProvider -- Provider of the API to be added.
        tier -- tier level for subscriptions, default is unlimited.
        """
        # We want these endpoints to work even when the backend userstore is not our LDAP. Therefore,
        # we cannot use the LdapUserSerializer class.
        parms = ['apiName']
        try:
            parm_values = get_parms_from_request(request.data, parms)
            if parm_values['apiName'] == '*':
                add_apis(request.wso2_cookies, client_name, tier=request.data.get('tier', settings.DEFAULT_TIER))
            else:
                add_api(request.wso2_cookies,
                        client_name,
                        parm_values['apiName'],
                        request.data.get('apiVersion'),
                        request.data.get('apiProvider'),
                        request.data.get('tier', settings.DEFAULT_TIER))
        except Error as e:
            return error_response(msg=e.message)
        except Exception as e:
            logger.error("Unhandled exception in ClientSubscription: " + str(e))
            return error_response(msg="Unable to subscribe client to Agave APIs.")
        if parm_values['apiName'] == '*':
            return HttpResponse(format_response(msg="Client " + client_name + " has been subscribed to Agave APIs.",
                                            response_data=None, query_dict=request.query_params), content_type='application/json')
        else:
            return HttpResponse(format_response(msg="Client " + client_name + " has been subscribed to "
                                             + parm_values['apiName'] + ".",
                                            response_data=None, query_dict=request.query_params), content_type='application/json')

    @auth.authenticated
    def delete(self, request, client_name, format=None):
        """
        Remove subscriptions from the client provided.
        api_name -- (REQUIRED) The name of the API to remove; Send api_name=* to remove all APIs.
        api_version -- Version of the API to be added.
        api_provider -- Provider of the API to be added.
        """
        parms = ['apiName']
        try:
            parm_values = get_parms_from_request(request.data, parms)
            if parm_values['apiName'] == '*':
                remove_apis(request.wso2_cookies, client_name)
            else:
                remove_api(request.wso2_cookies,
                        client_name,
                        parm_values['apiName'],
                        request.data.get('apiVersion'),
                        request.data.get('apiProvider'))
        except Error as e:
            return error_response(msg=e.message)
        except Exception as e:
            logger.error("Unhandled exception in ClientSubscription: " + str(e))
            return error_response(msg="Unable to remove API from client.")
        if parm_values['apiName'] == '*':
            return HttpResponse(format_response(msg="All APIs have been removed from the client "
                                             + client_name + ".",
                                            response_data=None, query_dict=request.query_params), content_type='application/json')
        else:
            return HttpResponse(format_response(msg=parm_values['apiName'] + " has been removed from the client " +
                                             client_name + ".",
                                            response_data=None, query_dict=request.query_params), content_type='application/json')


def get_parms_from_request(request_dict, parms):
    """
    Helper method to pull required parameters out of a request.
    """
    parm_values = {}
    for parm in parms:
        value = request_dict.get(parm)
        if not value:
            raise Error(message=parm + " is required")
        parm_values[parm] = value
    return parm_values

def create_client_application(cookies, username, application_name, tier=settings.DEFAULT_TIER,
                              description=None, callbackUrl=None):
    """
    Create a client application with the given name, throttling tier, description and callbackUrl.
    """
    url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_ADD_APP_URL
    VALID_TIERS = ['Bronze', 'Gold', 'Unlimited', 'Silver']
    found = False
    for t in VALID_TIERS:
        if t.lower() == tier.lower():
            tier = t
            found = True
    if not found:
        raise Error(message="tier value must be one of: [Bronze, Gold, Unlimited, Silver].")

    params = {'action': 'addApplication',
              'application': application_name,
              'tier': tier,
              'description': '',
              'callbackUrl': ''}
    if description:
        params['description'] = description
    if callbackUrl:
        params['callbackUrl'] = callbackUrl
    try:
        rsp = requests.post(url, cookies=cookies, params=params, verify=False)
    except Exception as e:
        raise Error("Unable to create application; " + str(e))
    if not rsp.status_code == 200:
        raise Error("Unable to create application; status code:" +
                    str(rsp.status_code))
    if rsp.json().get('error'):
        raise Error("Unable to create application: " +
                    str(rsp.json().get('message')))
    logger.info("Response from WSO2 ADD_APP: " + str(rsp.json()) + " Status code: " + str(rsp.status_code))

    # nothing returned in the wso2 response and the client credentials are not generated,
    # so we need to get the client just created and generate credentials for it.
    # Need to generate credentials FIRST -- otherwise, get_application will end up generating them which
    # will cause the consumerSecret to be lost.

    credentials = generate_credentials(cookies, application_name, callbackUrl)
    app = get_application(cookies, username, application_name, sanitize=False)
    add_apis(cookies, application_name)
    app.update(credentials)
    logger.info("Inside create_client_application after updating with credentials; app: " + str(app)
                + "credentials: " + str(credentials))

    # we now fix the record on the IDN_OAUTH_CONSUMER_APPS table in WSO2 db so that the Auth grant
    # flow will work.
    if callbackUrl:
        try:
            wso2_app = IdnOauthConsumerApps.objects.get(consumer_key=app.get("consumerKey"))
            wso2_app.callback_url = callbackUrl
            wso2_app.save()
        except Exception as e:
            logger.info("Got an exception trying to update the callback URL. Exception type: "
                        + str(type(e)) + " Exception: " + str(e))

    # TODO: assuming everything worked as expected, we write a CLIENT_CREATED event to the notification queue

    return app

def add_api(cookies, client_name, api_name, api_version, api_provider, tier=settings.DEFAULT_TIER):
    url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_SUBSCRIPTION_URL
    data = {'action': 'addAPISubscription',
            'name': api_name,
            'version': api_version,
            'provider': api_provider,
            'tier': tier,
            'applicationName': client_name}
    try:
        r = requests.post(url, cookies=cookies, data=data, verify=False)
        logger.info("add_api response:" + str(r.json()))
        logger.info("data:" + str(data))
    except Exception as e:
        raise Error("Unable to subscribe to API " + api_name +
                    "; message: " + str(e.message))
    try:
        json_rsp = r.json()
    except Exception as e:
        raise Error("Unable to subscribe to API " + api_name + "; no JSON received.")
    # APIM now throws an error if the API is subscribed to already.
    if json_rsp.get('message') and 'Subscription already exists' in json_rsp.get('message'):
        return
    if not r.status_code == 200:
        raise Error("Unable to subscribe to API " + api_name +
                    "; status code: " + str(r.status_code))
    if r.json().get('error'):
        raise Error("Unable to subscribe to API " + api_name + " error: " + str(r.json().get('error')))

    # TODO: assuming everything worked as expected, we write a CLIENT_SUBSCRIBE_API event to the notification queue


def add_apis(cookies, client_name, tier=settings.DEFAULT_TIER):
    """
    Subscribes to Agave APIs for an application at level 'tier'.
    """
    for api in AGAVE_APIS:
        add_api(cookies, client_name, api.get('name'), api.get('version'), api.get('provider'))

def generate_credentials(cookies, application_name, callbackUrl=None):
    """
    Generates credentials for a given application. Application must be subscribed to at least one API.
    """
    url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_SUBSCRIPTION_URL
    data = {'action' :'generateApplicationKey',
            'application' : application_name,
            'keytype' : 'PRODUCTION',
            'authorizedDomains' : 'ALL',
            'validityTime' : '14400',}
    logger.info("application name: " + application_name)
    if callbackUrl:
        data['callbackUrl'] = callbackUrl
    try:
        rsp = requests.post(url, cookies=cookies, data=data, verify=False)
        logger.info("Status code:" + str(rsp.status_code) + "content: " + str(rsp.content))
    except Exception as e:
        raise Error("Unable to generate credentials for " + str(application_name) + "; message: " + str(e))
    if not rsp.status_code == 200:
        raise Error("Unable to generate credentials for " + application_name +"; status code: " + str(rsp.status_code))
    if not rsp.json().get("data"):
        raise Error("Unable to generate credentials for " + application_name)
    return rsp.json().get('data').get('key')

def retrieve_application_key(cookies, application_id, application_name):
    """
    Retrieves application key directly from the AmApplicationKeyMapping table since APIM does not return
    it in their API.
    """
    # app_key_mapping = AmApplicationKeyMapping.objects.filter(application=application_id)
    app_key_mapping = AmApplicationKeyMapping.objects.filter(application_id=application_id)

    # todo - Need a better solution here.
    # This is to handle the fact that the DefaultApplication generated by WSO2 does not have a clientKey
    # and that will break things unless we generate one. However, this is not a great solution because
    # without the consumerSecret the DefaultApplication will be useless to the user, and once the secret is
    # generated it cannot be obtained through the API again.
    if app_key_mapping.count() < 1:
        generate_credentials(cookies, application_name)
        # we need to flush the read transaction on the db here to get a new one
        transaction.enter_transaction_management()
        transaction.commit()
        app_key_mapping = AmApplicationKeyMapping.objects.filter(application_id=application_id)

    return app_key_mapping.values()[0].get('consumer_key')


def delete_client(cookies, application_name):
    url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_REMOVE_APP_URL
    params = {'action': 'removeApplication',
              'application': application_name,}
    try:
        r = requests.post(url, cookies=cookies, params=params, verify=False)
    except Exception as e:
        raise Error("Unable to create application; " + str(e))
    if not r.status_code == 200:
        raise Error("Unable to create application; status code:" +
                    str(r.status_code))
    # TODO: assuming everything worked as expected, we write a CLIENT_DELETED event to the notification queue
    #else:

    logger.info("response: " + str(r) + "json: " + str(r.json()))

def remove_api(cookies, client_name, api_name, api_version, api_provider):
    url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_REMOVE_SUB_URL
    data = {'action': 'removeSubscription',
            'name': api_name,
            'version': api_version,
            'provider': api_provider,
            'applicationName': client_name}
    try:
        r = requests.post(url, cookies=cookies, data=data, verify=False)
        logger.info("remove_api response:" + str(r.json()))
        logger.info("data:" + str(data))
    except Exception as e:
        raise Error("Unable to remove API " + api_name +
                    "; message: " + str(e))
    if not r.status_code == 200:
        raise Error("Unable to remove API " + api_name +
                    "; status code: " + str(r.status_code))
    if r.json().get('error'):
        raise Error("Unable to remove API " + + api_name)

    # TODO: assuming everything worked as expected, we write a CLIENT_UNSUBSCRIBE_API event to the notification queue



def remove_apis(cookies, application_name):
    """
    Subscribes to Agave APIs for an application at level 'tier'.
    """
    subscriptions = get_subscriptions(cookies, application_name, sanitize=False)
    for api in subscriptions:
        remove_api(cookies, application_name, api.get('name'), api.get('version'), api.get('provider'))


def get_applications(cookies, username, sanitize=True):
    """
    Retrieve the list of applications for the user of a session.
    """
    url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_APPS_URL
    params = {'action': 'getApplications'}
    try:
        r = requests.get(url, cookies=cookies, params=params, verify=False)
    except Exception as e:
        raise Error("Unable to retrieve clients; " + str(e))
    if not r.status_code == 200:
        raise Error("Unable to retrieve clients; status code:" +
                    str(r.status_code))
    if not r.json().get("applications"):
        raise Error("Unable to retrieve clients; content: " + str(r.content))
    apps = r.json().get("applications")
    for app in apps:
        application_name = app.get("name")
        try:
            application_key = retrieve_application_key(cookies, app.get("id"), application_name)
            app['consumerKey'] = application_key
        except Exception as e:
            # It is valid for applications to not have credentials;
            logger.error("Unable to retrieve credentials for " + application_name + " in get_applications: " + str(e))
            # raise Error("Unable to retrieve credentials for " + application_name)
        # app.update(credentials)
        add_hyperlinks(app, username)
        if sanitize:
            sanitize_app(app)
    return apps

def add_hyperlinks(app, username):
    """
    Add references to self, subscriber and subscriptions.
    """
    app['_links'] = {'self':          {'href': settings.APP_BASE + reverse('clients') + urllib.quote(app.get('name'))},
                     'subscriber':    {'href': settings.APP_BASE + '/profiles/' + settings.AGAVE_API_VERSION + '/' + username},
                     'subscriptions': {'href': settings.APP_BASE + reverse('client_subscriptions', args=[app.get('name')])}
                    }


def sanitize_app(app):
    """
    Removes fields returned from WSO2 that should not be shown to the user.
    """
    app.pop("id", None)
    app.pop("enableRegenarate", None)
    app.pop("consumerSecret", None)
    app.pop("accessToken", None)
    app.pop("accessallowdomains", None)
    app.pop("validityTime", None)
    app.pop("status", None)
    app.pop("keyState", None)
    app.pop("tokenDetails", None)
    app.pop("apiCount", None)
    app.pop("tokenScope", None)
    app.pop("appDetails", None)
    app.pop("groupId", None)



def get_application(cookies, username, application_name="DefaultApplication", sanitize=True):
    """
    Gets the application in WSO2 with name application_name
    """
    logger.info("application name: " + application_name)
    applications = get_applications(cookies, username, sanitize)
    for app in applications:
        if app.get("name") == application_name:
            logger.info(str(app))
            return app
    raise Error("Application not found")


def get_application_id(cookies, username, application_name="DefaultApplication"):
    """
    Gets the application id in WSO2 for the application with name application_name
    """
    applications = get_applications(cookies, username, sanitize=False)
    for app in applications:
        if app.get("name") == application_name:
            return app.get("id")
    raise Error("Application not found")

def get_subscriptions(cookies, application_name, sanitize=True):
    """
    Returns the subscriptions for an application.
    """
    url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_LIST_SUBS_URL
    params = {'action': 'getAllSubscriptions', 'selectedApp': application_name}
    try:
        r = requests.get(url, cookies=cookies, params=params, verify=False)
    except Exception as e:
        raise Error("Unable to retrieve subscriptions; " + str(e))
    if not r.status_code == 200:
        raise Error("Unable to retrieve subscriptions; status code:" +
                    str(r.status_code))
    if r.json().get("error"):
        raise Error("Unable to retrieve subscriptions; error:" +
                    str(r.json().get("message")))
    if not r.json().get("subscriptions"):
        raise Error("Unable to retrieve subscriptions; content: " + str(r.content))
    # WSO2 actually returns a list of applications, so we need to filter by the application_name
    apps = r.json().get("subscriptions").get('applications')
    for app in apps:
        logger.info("app:" + app.get("name"))
        if app.get('name') == application_name:
            subscriptions = app.get("subscriptions")
            for sub in subscriptions:
                add_sub_hyperlinks(sub, application_name)
                if sanitize:
                    sanitize_subscription(sub)
            return subscriptions

def add_sub_hyperlinks(sub, client_name):
    """
    Add references to self, api and client.
    """
    sub['_links'] = {'self':   {'href': settings.APP_BASE + reverse('client_subscriptions', args=[client_name])},
                     'api':    {'href': settings.APP_BASE + sub.get('context') + '/'},
                     'client': {'href': settings.APP_BASE + reverse('client_details', args=[client_name])},
                     }


def sanitize_subscription(subscription):
    """
    Removes fields returned from WSO2 that should not be shown to the user.
    """
    subscription.pop("subStatus", None)
    subscription.pop("thumburl", None)
    subscription.pop("prodKey", None)
    subscription.pop("prodConsumerKey", None)
    subscription.pop("prodConsumerSecret", None)
    subscription.pop("prodAuthorizedDomains", None)
    subscription.pop("prodValidityTime", None)
    subscription.pop("prodValidityRemainingTime", None)
    subscription.pop("sandboxKey", None)
    subscription.pop("sandboxConsumerKey", None)
    subscription.pop("sandboxConsumerSecret", None)
    subscription.pop("sandAuthorizedDomains", None)
    subscription.pop("sandValidityTime", None)
    subscription.pop("sandValidityRemainingTime", None)
    subscription.pop("hasMultipleEndpoints", None)

    subscription['apiName'] = subscription.pop('name')
    subscription['apiStatus'] = subscription.pop('status')
    subscription['apiVersion'] = subscription.pop('version')
    subscription['apiContext'] = subscription.pop('context')
    subscription['apiProvider'] = subscription.pop('provider')




# ------------
# Multi-tenant
# ------------

# def get_tenant_id(request):
#     """
#     Return the tenant id from the request. Currently looks for the tenant_id
#     in the X-JWT-Assertion header set by WSO2 server.  In debug mode, will also
#     look for tenant_id in the request payload.
#     """
#     if settings.USE_APP_TENANT_ID:
#         return settings.APP_TENANT_ID
#     profile_header = request.META.get(settings.JWT_HEADER)
#     if not profile_header:
#         if not settings.DEBUG:
#             raise Error("Profile header missing.")
#         else:
#             # for testing purposes, pull tenant_id out of payload:
#             return get_tenant_id_from_payload(request)
#     # JWT is three base 64 encoded strings separated by a ".":
#     strs = profile_header.split(".")
#     if not len(strs) == 3:
#         raise Error("Invalid profile header format: " + profile_header)
#     # profile data with tenant id is in the second string:
#     raw_profile = strs[1]
#     profile = base64.b64decode(raw_profile)
#     # pull out string starting with tenant id:
#     temp = profile[profile.find(settings.WSO2_TID_STR) + len(settings.WSO2_TID_STR):]
#     # return the id, i.e. portion up to first occurrence of quote (")
#     return temp[:temp.find('"')]
#
# def get_tenant_id_from_payload(request):
#     """
#     Pulls tenant_id from payload. For testing purposes only.
#     """
#     tenant_id = None
#     if request.method == 'GET':
#         tenant_id = request.GET.get("tenant_id")
#     else:
#         try:
#             data = json.loads(request.raw_post_data)
#             tenant_id = data.get("tenant_id")
#         except Exception as e:
# 	           logger.info("Could not get tenant_id from json.loads, exception:" + str(e))
#         if not tenant_id:
#             attrs = {}
#             try:
#                 attrs = QueryDict(request.raw_post_data)
#             except Exception as e:
#                 logger.info("Could not build QueryDict; " + str(e))
#             tenant_id = attrs.get('tenant_id')
#     if not tenant_id:
#         raise Error("tenant_id required.")
#     return tenant_id