from django.db import models


class IdnOauthConsumerApps(models.Model):
    consumer_key = models.CharField(max_length=255L, primary_key=True, db_column='CONSUMER_KEY') # Field name made lowercase.
    consumer_secret = models.CharField(max_length=512L, db_column='CONSUMER_SECRET', blank=True) # Field name made lowercase.
    username = models.CharField(max_length=255L, db_column='USERNAME', blank=True) # Field name made lowercase.
    tenant_id = models.IntegerField(null=True, db_column='TENANT_ID', blank=True) # Field name made lowercase.
    app_name = models.CharField(max_length=255L, db_column='APP_NAME', blank=True) # Field name made lowercase.
    oauth_version = models.CharField(max_length=128L, db_column='OAUTH_VERSION', blank=True) # Field name made lowercase.
    callback_url = models.CharField(max_length=1024L, db_column='CALLBACK_URL', blank=True) # Field name made lowercase.
    login_page_url = models.CharField(max_length=1024L, db_column='LOGIN_PAGE_URL', blank=True) # Field name made lowercase.
    error_page_url = models.CharField(max_length=1024L, db_column='ERROR_PAGE_URL', blank=True) # Field name made lowercase.
    consent_page_url = models.CharField(max_length=1024L, db_column='CONSENT_PAGE_URL', blank=True) # Field name made lowercase.
    grant_types = models.CharField(max_length=1024L, db_column='GRANT_TYPES', blank=True) # Field name made lowercase.
    class Meta:
        db_table = 'IDN_OAUTH_CONSUMER_APPS'
        # managed = False

class AmApplicationKeyMapping(models.Model):
    # application = models.ForeignKey(AmApplication, db_column='APPLICATION_ID', primary_key=True) # Field name made lowercase.
    application_id = models.IntegerField(primary_key=True, db_column='APPLICATION_ID') # Field name made lowercase.
    consumer_key = models.CharField(max_length=255L, db_column='CONSUMER_KEY') # Field name made lowercase.
    key_type = models.CharField(max_length=512L, db_column='KEY_TYPE') # Field name made lowercase.
    # state = models.CharField(max_length=30L, db_column='STATE', blank=True) # Field name made lowercase.
    class Meta:
        db_table = 'AM_APPLICATION_KEY_MAPPING'
        # managed = False
