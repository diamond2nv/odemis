# -*- coding: utf-8 -*-
'''
Created on 20 Jul 2012

@author: Éric Piel

Copyright © 2012 Éric Piel, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 2 of the License, or (at your option) any later version.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Odemis. If not, see http://www.gnu.org/licenses/.
'''
from odemis.gui.util.img import DataArray2wxImage
import numpy
import wx

class VideoDisplayer(object):
    '''
    Very simple display for a continuous flow of images as a window
    It should be pretty much platform independent.
    '''


    def __init__(self, title="Live image", size=(640,480)):
        '''
        Displays the window on the screen
        size (2-tuple int,int): X and Y size of the window at initialisation
        Note that the size of the window automatically adapts afterwards to the
        coming pictures
        '''
        self.app = ImageWindowApp(title, size)
    
    def new_image(self, data):
        """
        Update the window with the new image (the window is resize to have the image
        at ratio 1:1)
        data (numpy.ndarray): an 2D array containing the image (can be 3D if in RGB)
        """
        self.app.img = DataArray2wxImage(data) # auto brightness/contrast
        wx.CallAfter(self.app.update_view)
    
    def waitQuit(self):
        """
        returns when the window is closed (or the user pressed Q)
        """
        self.app.MainLoop() # TODO we could use a Event if multiple accesses must be supported
    
    
class ImageWindowApp(wx.App):
    def __init__(self, title="Image", size=(640,480)):
        wx.App.__init__(self, redirect=False)
        self.AppName = "Odemis CLI"
        self.frame = wx.Frame(None, title=title, size=size)
 
        self.frame.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.frame.Bind(wx.EVT_KEY_UP, self.OnKey) # EVT_CHAR and EVT_KEY_DOWN seems to not work in Ubuntu
        self.panel = wx.Panel(self.frame)
        
        self.img = wx.EmptyImage(*size, clear=True)
        self.imageCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.BitmapFromImage(self.img))
 
        self.panel.SetFocus()
        self.frame.Show()
    
    def update_view(self):
        self.frame.Size = self.img.GetSize()
        self.imageCtrl.SetBitmap(wx.BitmapFromImage(self.img))
    
    def OnKey(self, event):
        key = event.GetKeyCode()
        if key in [ord("q"), ord("Q")]:
            self.frame.Destroy()
            
        # everything else we don't process
        event.Skip()
