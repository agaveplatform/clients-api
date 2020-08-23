import os

# -----------------------------------
# API MANAGER INSTANCE CONFIGURATION
# -----------------------------------

# The host name or domain name for the API Manager instance to connect to
tenant_host = os.environ.get('agave_apim_host', 'apim:9443')

# The Agave tenant to use
tenant_id = os.environ.get('tenant_id', 'sandbox')

# Any additional APIs that should be registered by default
ADDITIONAL_APIS = os.environ.get('agave_clients_additional_apis', 'tenants,uuids,tags')

# ------------------------------
# GENERAL SERVICE CONFIGURATION
# ------------------------------
# Base URL of this instance of the service. Used to populate the hyperlinks in the responses.
APP_BASE = os.environ.get('agave_id_app_base', 'https://localhost')

# DEBUG = True turns up logging and causes Django to generate exception pages with stack traces and
# additional information. Should be False in production.
DEBUG = os.environ.get('agave_id_debug', 'True').lower() == 'true'

# With this setting activated, Django will not create test databases for any database which has
# the USE_LIVE_FOR_TESTS': True setting.
TEST_RUNNER = 'agave_clients.testrunner.ByPassableDBDjangoTestSuiteRunner'


# ------------------
# BEANSTALK INSTANCE
# ------------------
BEANSTALK_SERVER = os.environ.get('beanstalk_server', "beanstalkd")
BEANSTALK_PORT = int(os.environ.get('beanstalk_port','11300'))
BEANSTALK_TUBE = os.environ.get('beanstalk_tube', 'sandbox.notifications.queue')
BEANSTALK_SRV_CODE = os.environ.get('beanstalk_srv_code', '0001-001')
TENANT_UUID = os.environ.get('tenant_uuid', '0001411570898814')

mysql_host = os.environ.get('MYSQL_HOST', os.environ.get('mysql_host', 'auth-mysql'))
mysql_port = os.environ.get('MYSQL_PORT', os.environ.get('mysql_port', '3306'))
mysql_pass = os.environ.get('MYSQL_PASSWORD', os.environ.get('mysql_pass', 'p@ssword'))
mysql_user = os.environ.get('MYSQL_USERNAME', os.environ.get('mysql_user', 'root'))
default_db_name = 'apimgtdb_' + tenant_id
mysql_database_name = os.environ.get('MYSQL_DATABASE', os.environ.get('mysql_database', default_db_name))
print "Using mysql_db: ", mysql_host
print "Using apim host: ", tenant_host

# ----------------------
# DATABASE CONNECTIVITY
# ----------------------
DATABASES = {
    # The 'default' db is the MySQL database. Use this setting to connect to the APIM db.
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': mysql_database_name,
        'USER': mysql_user,
        'PASSWORD': mysql_pass,
        'HOST': mysql_host,
        'PORT': mysql_port,
        # When running the test suite, when this setting is True, the test runner will not create a
        # test database. This is required for the clients service tests, since they rely on
        # interactions with the APIM instance itself. If the clients service is writing data to a
        # test db then APIM will not see those data and the tests will fail.
        'USE_LIVE_FOR_TESTS': True,
    },
}
