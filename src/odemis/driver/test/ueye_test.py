#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 31 Jun 2016

@author: Éric Piel
Testing class for driver.ueye .

Copyright © 2012 Éric Piel, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms 
of the GNU General Public License version 2 as published by the Free Software 
Foundation.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
Odemis. If not, see http://www.gnu.org/licenses/.
'''
from __future__ import division

import logging
from odemis.driver import ueye
import unittest
from unittest.case import skip

from cam_test_abs import VirtualTestCam, VirtualStaticTestCam

logging.getLogger().setLevel(logging.DEBUG)

CLASS = ueye.Camera
KWARGS = dict(name="camera", role="ccd", device=None, transp=[2, -1])


class StaticTestUEye(VirtualStaticTestCam, unittest.TestCase):
    camera_type = CLASS
    camera_kwargs = KWARGS


# Inheritance order is important for setUp, tearDown
#@skip("simple")
class TestUEye(VirtualTestCam, unittest.TestCase):
    """
    Test directly the UEye class.
    """
    camera_type = CLASS
    camera_kwargs = KWARGS


if __name__ == '__main__':
    unittest.main()

