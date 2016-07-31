"""
Ludolph: Monitoring Jabber Bot
Copyright (C) 2012-2016 Erigones, s. r. o.
This file is part of Ludolph.

See the LICENSE file for copying permission.
"""

import unittest
from ludolph.tests.fake_bot import FakeLudolphBot
from ludolph.plugins.base import Base


class LudolphCommandsTest(unittest.TestCase):

    base = None

    def setUp(self):
        xmpp = FakeLudolphBot()  # Reference to LudolphBot object
        config = {
            'dummy': 'test'
        }
        self.base = Base(xmpp, config)

    def test__roster_list(self):
        self.assertEqual(self.base._roster_list(), 'friend2@test.com\tboth\nfriend1@test.com\tboth\nludolph@test.com\tboth')


if __name__ == '__main__':
    unittest.main()