# -*- coding: utf-8 -*-
'''
Created on 13 Mar 2015

@author: Kimon Tsitsikas

Copyright © 2015 Kimon Tsitsikas, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License version 2 as published by the Free Software Foundation.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Odemis. If not, see http://www.gnu.org/licenses/.
'''
from __future__ import division

import glob
import logging
from odemis.driver import pmtctrl
import unittest
from unittest.case import skip


logging.getLogger().setLevel(logging.DEBUG)

SN = "0E203C44"  # put the serial number written on the component to test

CLASS = pmtctrl.PMTControl
# KWARGS_SIM = dict(name="test", role="pmt_control", port="/dev/fake", axis="r", inverted=["r"])
# KWARGS = KWARGS_SIM
KWARGS = dict(name="test", role="pmt_control", sn=SN)

# @skip("simple")
class TestStatic(unittest.TestCase):
    """
    Tests which don't need a component ready
    """
    # @skip("simple")
    def test_scan(self):
        devices = CLASS.scan()
        self.assertGreater(len(devices), 0)

    # @skip("simple")
    def test_creation(self):
        """
        Doesn't even try to do anything, just create and delete components
        """
        dev = CLASS(**KWARGS)

        self.assertTrue(dev.selfTest(), "self test failed.")
        dev.terminate()

    # @skip("simple")
    def test_wrong_serial(self):
        """
        Check it correctly fails if the device with the given serial number is
        not a PMT Control.
        """
        # Look for a device with a serial number not starting with 37
        paths = glob.glob("/sys/bus/usb/devices/*/serial")
        for p in paths:
            try:
                f = open(p)
                snw = f.read().strip()
            except IOError:
                logging.debug("Failed to read %s, skipping device", p)
        else:
            self.skipTest("Failed to find any USB device with a serial number")

        kwargsw = dict(KWARGS)
        kwargsw["sn"] = snw
        with self.assertRaises(ValueError):
            dev = CLASS(**kwargsw)

class TestPMTControl(unittest.TestCase):
    """
    Tests which need a component ready
    """

    def setUp(self):
        self.dev = CLASS(**KWARGS)

    def tearDown(self):
        self.dev.terminate()

    def test_send_cmd(self):
        ans = self.dev.sendCommand("VOLT 3.2\n")

if __name__ == "__main__":
    unittest.main()
