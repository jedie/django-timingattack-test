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


# MEASUREING_LOOPS = 10
# MEASUREING_LOOPS = 25
# MEASUREING_LOOPS = 50
# MEASUREING_LOOPS = 75
MEASUREING_LOOPS = 200

MIN_MAX_AVG_PERCENT = 15


def average(l):
    try:
        return sum(l) / len(l)
    except ZeroDivisionError:
        return 0


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
        self.superuser.email='unittest@localhost'
        self.superuser.is_active = True
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.set_password(self.SUPER_USER_PASS)
        self.superuser.save()

    def out(self, *args):
        print(*args, file=sys.stderr)


class BaseTestTimingAttack(BaseTestCase):
    VERBOSE = False

    def _measure_loop(self, callback):
        start_time = time.time()
        durations = [callback() for _ in range(MEASUREING_LOOPS)]
        duration = time.time() - start_time

        durations.sort()
        avg = average(durations)
        count = int(round(MEASUREING_LOOPS/100*MIN_MAX_AVG_PERCENT,0))
        if count<1:
            count=1
        self.out("\tMin/max avg with %i items." % count)
        avg_min = average(durations[:count])
        avg_max = average(durations[-count:])

        quick_percent = 100 - (100/avg_min*avg)
        long_percent = 100 - (100/avg_max*avg)
        self.out("\tavg.min: %.1fms (%i%%) - average: %.1fms - avg.max: %.1fms (%i%%) (takes %.2f sec.)" % (
            avg_min*1000, quick_percent,
            avg*1000,
            avg_max*1000, long_percent,
            duration
        ))
        return avg


class TestDjangoLoginTimingAttack(BaseTestTimingAttack):
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
        self.out("\nMeasuring successful django login (%i loops)..." % MEASUREING_LOOPS)
        average1 = self._measure_loop(self.measured_successful_django_login)

        self.out("Measuring 'wrong password' django login (%i loops)..." % MEASUREING_LOOPS)
        average2 = self._measure_loop(self.measured_wrong_password_django_login)

        self.out("Measuring 'wrong username' django login (%i loops)..." % MEASUREING_LOOPS)
        average3 = self._measure_loop(self.measured_wrong_username_django_login)

        averages = [average1, average2, average3]
        min_avg = min(averages)
        max_avg = max(averages)

        diff = max_avg - min_avg
        percent = 100 - (100/max_avg*min_avg)
        self.out(" *** max.average django diff: %.2fms (%.1f%%)" % (diff*1000, percent))