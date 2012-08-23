# -*- coding: utf-8 -*-
'''
Created on 23 Aug 2012

@author: Éric Piel

Copyright © 2012 Éric Piel, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 2 of the License, or (at your option)
any later version.

Odemis is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
Odemis. If not, see http://www.gnu.org/licenses/.
'''
import numpy
import scipy
import wx

# various functions to convert and modify images (DataArray and wxImage)

def DataArray2wxImage(data, depth=None, brightness=None, contrast=None):
    """
    data (DataArray): 2D image greyscale
    depth (None or 1<int): maximum value possibly encoded (12 bits => 4096)
        None => brightness and contrast auto
    brightness (None or -1<=float<=1): brightness change.
        None => auto. 0 => no change. -1 => fully black
    contrast  (None or -1<=float<=1): contrast change.
        None => auto. 0 => no change. -1 => fully grey, 1 => white/black only
    Note: if auto, both contrast and brightness must be None
    returns (wxImage): rgb (888) converted image with the same dimension
    """
    assert(len(data.shape) == 2) # => 2D with greyscale
    size = data.shape[0:2]
    
    # fit it to 8 bits and update brightness and contrast at the same time 
    if brightness is None and contrast is None:
        # This is still quite inefficient as it turns the 16 bits into floats
        # in a new array and then convert it to 8 bit and then duplicate it 3 times.
        # TODO: http://wxpython-users.1045709.n5.nabble.com/BitmapFromBuffer-speed-and-proposal-for-wx-Bitmap-CopyFromBuffer-td2333356.html
#        minmax = [numpy.amin(data), numpy.amax(data)] 
#        drescaled = numpy.interp(data, minmax, [0, 256])
        drescaled = scipy.misc.bytescale(data)
    elif brightness == 0 and contrast == 0:
        assert(depth is not None)
        if depth == 256:
            drescaled = data
        else:
            drescaled = scipy.misc.bytescale(data, cmin=0, cmax=depth)
    else:
        # manual brightness and contrast
        assert(depth is not None)
        assert(contrast is not None)
        assert(brightness is not None)
        # see http://docs.opencv.org/doc/tutorials/core/basic_linear_transform/basic_linear_transform.html
        # brightness: newpixel = origpix + brightness*depth
        # contrast: newpixel = (origix - depth/2) * contrast + depth/2
        # truncate
        # (could be possible to use lookup table to speed up)
        corrected = (data + (brightness * depth - depth/2.0)) * contrast + depth/2.0 
        # XXX need to truncate
        # TODO: check more bytescale
        drescaled = scipy.misc.bytescale(corrected, cmin=0, cmax=depth)
        #raise NotImplementedError("No brightness and contrast change supported")

    # TODO: shall we also handle colouration here?
        
    # Now duplicate it 3 times to make it rgb (as a simple approximation of greyscale)
    # dstack doesn't work because it doesn't generate in C order (uses strides)
    # apparently this is as fast (or even a bit better):
    rgb = numpy.empty(size + (3,), dtype="uint8") # 0 copy (1 malloc)
    rgb[:,:,0] = drescaled # 1 copy
    rgb[:,:,1] = drescaled # 1 copy
    rgb[:,:,2] = drescaled # 1 copy
    return wx.ImageFromBuffer(*size, dataBuffer=rgb) # 0 copy
