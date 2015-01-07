# -----------------------------------
# API MANAGER INSTANCE CONFIGURATION
# -----------------------------------

# The host name or domain name for the API Manager instance that this instance of the service should
# communicate with. NOTE: Only used when NOT running in docker
TENANT_HOST = 'agave-staging.tacc.utexas.edu'

# ------------------------------
# GENERAL SERVICE CONFIGURATION
# ------------------------------
# Base URL of this instance of the service. Used to populate the hyperlinks in the responses.
APP_BASE = 'http://localhost:8000'

# DEBUG = True turns up logging and causes Django to generate exception pages with stack traces and
# additional information. Should be False in production.
DEBUG = True

# With this setting activated, Django will not create test databases for any database which has
# the USE_LIVE_FOR_TESTS': True setting.
TEST_RUNNER = 'agave_clients.testrunner.ByPassableDBDjangoTestSuiteRunner'

import os
HERE = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(os.path.join(HERE, 'running_in_docker')):
    # first, check to see if links are available (either from fig or directly from docker):
    if os.environ.get('HOST_IP') and os.environ.get('MYSQL_PORT_3306_TCP_ADDR'):
        tenant_host = os.environ.get('HOST_IP')
        mysql_db = os.environ.get('MYSQL_PORT_3306_TCP_ADDR')
    # otherwise, use service discovery:
    else:
        # if tenant_id has been defined in the environment used that, otherwise, default to 'dev':
        tenant_id = os.environ.get('tenant_id', 'dev')
        tenant_host = 'apim.' + tenant_id + '.agave.tacc.utexas.edu:9443'
        mysql_db = 'mysql.' + tenant_id + '.agave.tacc.utexas.edu'

else:
    mysql_db = TENANT_HOST
    tenant_host = TENANT_HOST

print "Using mysql_db: ", mysql_db
print "Using tenant_host: ", tenant_host

# ----------------------
# DATABASE CONNECTIVITY
# ----------------------
DATABASES = {
    # The 'default' db is the MySQL database. Use this setting to connect to the APIM db.
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'apimgtdb',
        'USER': 'superadmin',
        'PASSWORD': 'foo', # UPDATED FROM STACHE ENTRY
        'HOST': mysql_db,
        'PORT': '3306',
        # When running the test suite, when this setting is True, the test runner will not create a
        # test database. This is required for the clients service tests, since they rely on
        # interactions with the APIM instance itself. If the clients service is writing data to a
        # test db then APIM will not see those data and the tests will fail.
        'USE_LIVE_FOR_TESTS': True,
    },
}

# ------------------
# BEANSTALK INSTANCE
# ------------------
BEANSTALK_SERVER = "iplant-qa.tacc.utexas.edu"
BEANSTALK_PORT = 11300
# BEANSTALK_TUBE = 'default'
BEANSTALK_TUBE = 'test.jfs'
BEANSTALK_SRV_CODE = '0001-001'
TENANT_UUID = '0001411570898814'

