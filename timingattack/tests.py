# coding: utf-8

"""
    Timing Attack DEMO
    ~~~~~~~~~~~~~~~~~~

    :copyleft: 2015 by the secure-js-login team, see AUTHORS for more details.
    :created: by JensDiemer.de
    :license: GNU GPL v3 or above, see LICENSE for more details
"""

from __future__ import unicode_literals, print_function

import time
import sys

from django.contrib.auth import SESSION_KEY, get_user_model
from django.core.urlresolvers import reverse
from django.test import override_settings, SimpleTestCase
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages



# MEASUREING_LOOPS = 10
# MEASUREING_LOOPS = 25
# MEASUREING_LOOPS = 50
# MEASUREING_LOOPS = 75
# MEASUREING_LOOPS = 200
MEASUREING_LOOPS = 300

PDF_FILENAME = 'DjangoTimingAttackMatplot.pdf'


# @override_settings(PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',))
class BaseTestCase(SimpleTestCase):
    SUPER_USER_NAME = "super"
    SUPER_USER_PASS = "super secret"

    @classmethod
    def setUpClass(cls):
        super(BaseTestCase, cls).setUpClass()
        cls.django_login_url = reverse("admin:login")

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.superuser, created = get_user_model().objects.get_or_create(
            username=self.SUPER_USER_NAME
        )
        self.superuser.email = 'unittest@localhost'
        self.superuser.is_active = True
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.set_password(self.SUPER_USER_PASS)
        self.superuser.save()

    def out(self, *args):
        print(*args, file=sys.stderr)


class TestDjangoLoginTimingAttack(BaseTestCase):
    def measured_successful_django_login(self):
        start_time = time.time()
        self.client.post(
            self.django_login_url,
            follow=False,
            data={
                "username": self.SUPER_USER_NAME,
                "password": self.SUPER_USER_PASS,
            }
        )
        duration = time.time() - start_time
        self.assertIn(SESSION_KEY, self.client.session)
        self.client.logout()
        return duration

    def measured_wrong_password_django_login(self):
        start_time = time.time()
        self.client.post(
            self.django_login_url,
            follow=False,
            data={
                "username": self.SUPER_USER_NAME,
                "password": "wrong password",
            }
        )
        duration = time.time() - start_time
        self.assertNotIn(SESSION_KEY, self.client.session)
        return duration

    def measured_wrong_username_django_login(self):
        start_time = time.time()
        self.client.post(
            self.django_login_url,
            follow=False,
            data={
                "username": "NotExistingUser",
                "password": "wrong password",
            }
        )
        duration = time.time() - start_time
        self.assertNotIn(SESSION_KEY, self.client.session)
        return duration

    @override_settings(DEBUG=False)
    def test_django_login(self):
        durations1 = []
        durations2 = []
        durations3 = []

        # MEASUREING_LOOPS = 20

        next_update = time.time() + 1
        for i in range(MEASUREING_LOOPS):
            start_time = time.time()
            self.measured_successful_django_login()
            durations1.append(time.time() - start_time)

            start_time = time.time()
            self.measured_wrong_password_django_login()
            durations2.append(time.time() - start_time)

            start_time = time.time()
            self.measured_wrong_username_django_login()
            durations3.append(time.time() - start_time)
            if time.time() > next_update:
                self.out("%i/%i loops." % (i, MEASUREING_LOOPS))
                next_update = time.time() + 1

        # self.out(durations1)
        # self.out(durations2)
        # self.out(durations3)

        total_durations = durations1 + durations2 + durations3
        fastest = min(total_durations)
        slowest = max(total_durations)
        # print(fastest, slowest)

        with PdfPages(PDF_FILENAME) as pdf:
            # http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.plot
            plt.plot(range(MEASUREING_LOOPS), durations1, 'go', label="success")
            plt.plot(range(MEASUREING_LOOPS), durations2, 'ro', label="wrong password")
            plt.plot(range(MEASUREING_LOOPS), durations3, 'yo', label="wrong username")
            plt.axis([0, MEASUREING_LOOPS, fastest, slowest])
            plt.ylabel('response time')
            plt.xlabel('loop count')
            plt.legend(shadow=True, title="Legend", fancybox=True)

            plt.title('Django Timing Attack Matplot')
            pdf.savefig()
            plt.close()

        self.out("%r written!" % PDF_FILENAME)


