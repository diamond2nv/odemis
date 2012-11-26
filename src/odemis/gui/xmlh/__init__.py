#-*- coding: utf-8 -*-
"""
@author: Rinze de Laat

Copyright © 2012 Rinze de Laat, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 2 of the License, or (at your option) any later version.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Odemis. If not, see http://www.gnu.org/licenses/.
"""

# By default, not all XmlResourceHandlers are present in the XML resource
# generated by the XRCED program (the main_xrc.py module, in Odemis' case).
# To handle custom and the more exotic controls, the approriate handlers should
# be added to the resource. We do this by replacing the default `get_resources`
# function in the main_xrc.py module with the function in this module. The
# replacement should take place before any references are made to the frames,
# dialog and controls defined within the main_xrc.py module.

def odemis_get_resources():
    """ This function provides access to the XML handlers needed for
        non-standard controls defined in the XRC file.
    """

    import odemis.gui.main_xrc

    if odemis.gui.main_xrc.__res == None:
        from odemis.gui.xmlh.xh_delmic import HANDLER_CLASS_LIST
        odemis.gui.main_xrc.__init_resources()
        for handler_klass in HANDLER_CLASS_LIST:
            odemis.gui.main_xrc.__res.InsertHandler(handler_klass())
    return odemis.gui.main_xrc.__res

def odemis_get_firststep_resources():

    import odemis.firststep.main_xrc

    if odemis.firststep.main_xrc.__res == None:
        from odemis.gui.xmlh.xh_delmic import HANDLER_CLASS_LIST
        odemis.firststep.main_xrc.__init_resources()
        for handler_klass in HANDLER_CLASS_LIST:
            odemis.firststep.main_xrc.__res.InsertHandler(handler_klass())
    return odemis.firststep.main_xrc.__res

def odemis_get_test_resources():
    """ This function provides access to the XML handlers needed by
        the test  GUI.
    """
    import odemis.gui.test.test_gui

    if odemis.gui.test.test_gui.__res == None:
        from odemis.gui.xmlh.xh_delmic import HANDLER_CLASS_LIST
        odemis.gui.test.test_gui.__init_resources()
        for handler_klass in HANDLER_CLASS_LIST:
            odemis.gui.test.test_gui.__res.InsertHandler(handler_klass())
    return odemis.gui.test.test_gui.__res
