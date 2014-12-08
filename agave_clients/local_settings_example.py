# -----------------------------------
# API MANAGER INSTANCE CONFIGURATION
# -----------------------------------

# The host name or domain name for the API Manager instance that this instance of the service should
# communicate with.
TENANT_HOST = 'agave-staging.tacc.utexas.edu'

# The ID of the tenant in the LDAP database. This needs to match the userstore configuration in APIM.
# REMOVE?
# APP_TENANT_ID = '1'

# --------------------
# JWT Header settings
# -------------------
# Whether or not to check the JWT; When this is False, certain features will not be available such as the
# "me" lookup feature since these features rely on profile information in the JWT.
# REMOVE?
# CHECK_JWT = True

# Actual header name that will show up in request.META; value depends on APIM configuration, in particular
# the tenant id specified in api-manager.xml
# REMOVE?
# JWT_HEADER = 'HTTP_JWT_ASSERTION'

# Relative location of the public key of the APIM instance; used for verifying the signature of the JWT.
# REMOVE?
# PUB_KEY = 'usersApp/agave-vdjserver-org_pub.txt'

# APIM Role required to make updates to the LDAP database
# REMOVE?
# USER_ADMIN_ROLE = 'Internal/user-account-manager'

# Whether or not the USER_ADMIN_ROLE before allowing updates to the LDAP db (/users service)
# REMOVE?
# CHECK_USER_ADMIN_ROLE = True

# These settings are currently only used in the account sign up web application:
# Deprecated - this is only used for manual testing of resolving the tenant id from the JWT.
# REMOVE?
# USE_APP_TENANT_ID = True
# Tenantid key in WSO2 JWT Header:
# WSO2_TID_STR = 'enduserTenantId":"'


# ------------------------------
# GENERAL SERVICE CONFIGURATION
# ------------------------------
# DEBUG = True turns up logging and causes Django to generate exception pages with stack traces and
# additional information. Should be False in production.
DEBUG = True

# With this setting activated, Django will not create test databases for any database which has
# the USE_LIVE_FOR_TESTS': True setting.
TEST_RUNNER = 'testrunner.ByPassableDBDjangoTestSuiteRunner'

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
        'HOST': TENANT_HOST,
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

