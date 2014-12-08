from django.test.simple import DjangoTestSuiteRunner

class ByPassableDBDjangoTestSuiteRunner(DjangoTestSuiteRunner):

    def setup_databases(self, **kwargs):
        from django.db import connections
        old_names = []
        mirrors = []
        for alias in connections:
            connection = connections[alias]
            # If the database has a test mirror
            # use it instead of creating a test database.
            # mirror_alias = connection.settings_dict['TEST_MIRROR']
            #
            # if mirror_alias:
            #     mirrors.append((alias,
            #                     connections[alias].settings_dict['NAME']))
            #     connections[alias].settings_dict['NAME'] = (
            #             connections[mirror_alias].settings_dict['NAME'])
            if not connection.settings_dict.get('USE_LIVE_FOR_TESTS', False):
                old_names.append((connection,
                                  connection.settings_dict['NAME']))
                connection.creation.create_test_db(self.verbosity)

        return old_names, mirrors

    # def run_tests(self, test_labels, extra_tests=None, **kwargs):
    #     # This test runner tried to run test on everything,
    #     # even on the django itself, this is a hacky workaround ;)
    #     super(ByPassableDBDjangoTestSuiteRunner, self).run_tests(
    #         settings.TESTED_APPS, extra_tests, **kwargs)