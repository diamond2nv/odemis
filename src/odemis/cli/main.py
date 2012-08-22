#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 12 Jul 2012

@author: Éric Piel

Copyright © 2012 Éric Piel, Delmic

This file is part of Open Delmic Microscope Software.

Delmic Acquisition Software is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 2 of the License, or (at your option) any later version.

Delmic Acquisition Software is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Delmic Acquisition Software. If not, see http://www.gnu.org/licenses/.
'''
# This is a basic command line interface to the odemis back-end

from odemis.cli.video_displayer import VideoDisplayer
from odemis.dataio import tiff
from odemis import model
from odemis import __version__
import argparse
import collections
import inspect
import logging
import os
import sys

BACKEND_RUNNING = "RUNNING"
BACKEND_DEAD = "DEAD"
BACKEND_STOPPED = "STOPPED"
def get_backend_status():
    try:
        microscope = model.getMicroscope()
        if len(microscope.name) > 0:
            return BACKEND_RUNNING
    except:
        logging.info("Failed to find microscope")
        if os.path.exists(model.BACKEND_FILE):
            return BACKEND_DEAD
        else:
            logging.info("Back-end %s file doesn't exists", model.BACKEND_FILE)
            return BACKEND_STOPPED
    return BACKEND_DEAD

status_to_xtcode = {BACKEND_RUNNING: 0,
                    BACKEND_DEAD: 1,
                    BACKEND_STOPPED: 2
                    }

# small object that can be remotely executed for scanning
class Scanner(model.Component):
    def __init__(self, cls, **kwargs):
        assert(inspect.isclass(cls))
        model.Component.__init__(self, "scanner for %s" % cls.__name__, **kwargs)
        self.cls = cls
    def scan(self):
        logging.info("Scanning for '%s' devices", self.cls.__name__)
        return self.cls.scan()

def scan():
    """
    Scan for connected devices and list them
    Output like:
    Classname: 'Name of Device' init={arg: value, arg2: value2}
    """
    # only here, to avoid importing everything for other commands
    from odemis import driver
    num = 0
    # we scan by using every HwComponent class which has a .scan() method
    for module_name in driver.__all__:
        module = __import__("odemis.driver."+module_name, fromlist=[module_name])
        for cls_name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, model.HwComponent) and hasattr(cls, "scan"):
                # do it in a separate container so that we don't have to load
                # all drivers in the same process (andor cams don't like it)
                container_name = "scanner%d"%num
                num += 1
                scanner = model.createInNewContainer(container_name, Scanner, {"cls": cls})
                devices = scanner.scan()
                scanner.terminate()
                model.getContainer(container_name).terminate()
                for name, args in devices:
                    print "%s.%s: '%s' init=%s" % (module_name, cls_name, name, str(args))
    return 0

def kill_backend():
    try:
        backend = model.getContainer(model.BACKEND_NAME)
        backend.terminate()
    except:
        logging.error("Failed to stop the back-end")
        return 127
    return 0

def print_component(comp, level):
    """
    Pretty print on one line a component
    comp (Component): the component to print
    level (int > 0): hierarchy level (for indentation)
    """
    if level == 0:
        indent = ""
    else:
        indent = u" ↳"*level + " "
    print indent + comp.name + "\trole:" + comp.role
    # TODO would be nice to display which class is the component
    # TODO:
    # * if emitter, display .shape
    # * if detector, display .shape
    # * if actuator, display .axes

def print_component_tree(root, level=0):
    """
    Print all the components starting from the root. 
    root (Component): the component at the root of the tree
    level (int > 0): hierarchy level (for pretty printing)
    """
    # first print the root component
    print_component(root, level)

    # display all the children
    for comp in root.children:
            print_component_tree(comp, level + 1)

def print_microscope_tree(mic):
    """
    Print all the components starting from the microscope. 
    root (Microscope): a microscope
    """
    # first print the microscope
    print_component(mic, 0)
    # Microscope is a special case
    for comp in mic.detectors:
        print_component_tree(comp, 1)
    for comp in mic.emitters:
        print_component_tree(comp, 1)
    for comp in mic.actuators:
        print_component_tree(comp, 1)
    # no children

def list_components():
    # We actually just browse as a tree the microscope 
    try:
        microscope = model.getMicroscope()
    except:
        logging.error("Failed to contact the back-end")
        return 127
    print_microscope_tree(microscope)
    return 0

def print_roattribute(name, value):
    print "\t" + name + " (RO Attribute)\t value: %s" % str(value)

non_roattributes_names = ("name", "role", "parent", "children", "affects", 
                          "actuators", "detectors", "emitters")
def print_roattributes(component):
    for name, value in model.getROAttributes(component).items():
        # some are handled specifically
        if name in non_roattributes_names:
            continue
        print_roattribute(name, value)
        
def print_data_flow(name, df):
    print "\t" + name + " (Data-flow)"

def print_data_flows(component):
    # find all dataflows
    for name, value in model.getDataFlows(component).items():
        print_data_flow(name, value)

def print_vattribute(name, va):
    if va.unit:
        unit = " (unit: %s)" % va.unit
    else:
        unit = ""
    
    if va.readonly:
        readonly = "RO "
    else:
        readonly = ""
    
    # we cannot discover if it continuous or enumerated, just try and see if it fails
    try:
        varange = va.range
        str_range = " (range: %s -> %s)" % (str(varange[0]), str(varange[1]))
    except (AttributeError, model.NotApplicableError):
        str_range = ""
        
    try:
        vachoices = va.choices
        str_choices = " (choices: %s)" % ", ".join([str(c) for c in vachoices])
    except (AttributeError, model.NotApplicableError):
        str_choices = ""
    
    print("\t" + name + " (%sVigilant Attribute)\t value: %s%s%s%s" %
          (readonly, str(va.value), unit, str_range, str_choices))

def print_vattributes(component):
    for name, value in model.getVAs(component).items():   
        print_vattribute(name, value)
    
def print_attributes(component):
    print "Component '%s':" % component.name
    print "\trole: %s" % component.role
    print "\taffects: " + ", ".join(["'"+c.name+"'" for c in component.affects]) 
    print_roattributes(component)
    print_vattributes(component)
    print_data_flows(component)

def get_component_from_set(comp_name, components):
    """
    return the component with the given name from a set of components
    comp_name (string): name of the component to find
    components (iterable Components): the set of components to look into
    raises
        LookupError if the component doesn't exist
        other exception if there is an error while contacting the backend
    """
    component = None
    for c in components:
        if c.name == comp_name:
            component = c
            break
   
    if component is None:
        raise LookupError("Failed to find component '%s'", comp_name)
    
    return component

def get_component(comp_name):
    """
    return the component with the given name
    comp_name (string): name of the component to find
    raises
        LookupError if the component doesn't exist
        other exception if there is an error while contacting the backend
    """
    return get_component_from_set(comp_name, model.getComponents())
    

def get_actuator(comp_name):
    """
    return the actuator component with the given name
    comp_name (string): name of the component to find
    raises
        LookupError if the component doesn't exist
        other exception if there is an error while contacting the backend
    """
    # isinstance() doesn't work, so we just list every component in microscope.actuators
    microscope = model.getMicroscope()
    return get_component_from_set(comp_name, microscope.actuators)

def get_detector(comp_name):
    """
    return the actuator component with the given name
    comp_name (string): name of the component to find
    raises
        LookupError if the component doesn't exist
        other exception if there is an error while contacting the backend
    """
    # isinstance() doesn't work, so we just list every component in microscope.detectors
    microscope = model.getMicroscope()
    return get_component_from_set(comp_name, microscope.detectors)

def list_properties(comp_name):
    """
    print the data-flows and vattributes of a component
    comp_name (string): name of the component
    """
    try:
        component = get_component(comp_name)
    except LookupError:
        logging.error("Failed to find component '%s'", comp_name)
        return 127
    except:
        logging.error("Failed to contact the back-end")
        return 127
   
    print_attributes(component)
    return 0
    
def boolify(s):
    if s == 'True' or s == 'true':
        return True
    if s == 'False' or s == 'false':
        return False
    raise ValueError('Not a boolean value: %s' % s)

def reproduceTypedValue(real_val, str_val):
    """
    Tries to convert a string to the type of the given value
    real_val (object): value with the type that must be converted to
    str_val (string): string that will be converted
    return the value contained in the string with the type of the real value
    raises 
      ValueError() if not possible to convert
      TypeError() if type of real value is not supported
    """
    if isinstance(real_val, bool):
        return boolify(str_val)
    elif isinstance(real_val, int):
        return int(str_val)
    elif isinstance(real_val, float):
        return float(str_val)
    elif isinstance(real_val, basestring):
        return str_val
    elif isinstance(real_val, dict): # must be before iterable
        if len(real_val) > 0:
            key_real_val = real_val.keys()[0]
            value_real_val = real_val[key_real_val]
        else:
            logging.warning("Type of attribute is unknown, using string")
            sub_real_val = ""
            value_real_val = ""
            
        dict_val = {}
        for sub_str in str_val.split(','):
            item = sub_str.split(':')
            assert(len(item) == 2)
            key =  reproduceTypedValue(key_real_val, item[0]) # TODO Should warn if len(item) != 2
            value = reproduceTypedValue(value_real_val, item[1])
            dict_val[key] = value
        return dict_val
    elif isinstance(real_val, collections.Iterable):
        if len(real_val) > 0:
            sub_real_val = real_val[0]
        else:
            logging.warning("Type of attribute is unknown, using string")
            sub_real_val = ""

        iter_val = [] # the most preserving iterable
        for sub_str in str_val.split(','):
            iter_val.append(reproduceTypedValue(sub_real_val, sub_str))
        final_val = type(real_val)(iter_val) # cast to real type
        return final_val
    
    raise TypeError("Type %r is not supported to convert %s" % (type(real_val), str_val))

def set_attr(comp_name, attr_name, str_val):
    """
    set the value of vigilant attribute of the given component using the type
    of the current value of the attribute.
    """
    try:
        component = get_component(comp_name)
    except LookupError:
        logging.error("Failed to find component '%s'", comp_name)
        return 127
    except:
        logging.error("Failed to contact the back-end")
        return 127

    try:
        attr = getattr(component, attr_name)
    except:
        logging.error("Failed to find attribute '%s' on component '%s'", attr_name, comp_name)
        return 129
    
    if not isinstance(attr, model.VigilantAttributeBase):
        logging.error("'%s' is not a vigilant attribute of component '%s'", attr_name, comp_name)
        return 129
    
    try:
        new_val = reproduceTypedValue(attr.value, str_val)
    except TypeError:
        logging.error("'%s' is of unsupported type %r", attr_name, type(attr.value))
        return 127
    except ValueError:
        logging.error("Impossible to convert '%s' to a %r", str_val, type(attr.value))
        return 127
    
    try:
        attr.value = new_val
    except:
        logging.exception("Failed to set %s.%s = '%s'", comp_name, attr_name, str_val)
        return 127
    return 0

MAX_DISTANCE = 0.1 #m
def move(comp_name, axis_name, str_distance):
    """
    move (relatively) the axis of the given component by the specified about of µm
    """
    # for safety reason, we use µm instead of meters, as it's harder to type a
    # huge distance
    try:
        component = get_actuator(comp_name)
    except LookupError:
        logging.error("Failed to find actuator '%s'", comp_name)
        return 127
    except:
        logging.error("Failed to contact the back-end")
        return 127

    if axis_name not in component.axes:
        logging.error("Actuator %s has not axis '%s'", comp_name, axis_name)
        return 129
    
    try:
        distance = float(str_distance) * 1e-6 # µm -> m
    except ValueError:
        logging.error("Distance '%s' cannot be converted to a number", str_distance)
        return 127
    
    if abs(distance) > MAX_DISTANCE:
        logging.error("Distance of %f m is too big (> %f m)", distance, MAX_DISTANCE)
        return 129
    
    try:
#        for i in range(1000): # FIXME seems to fail (all sent, but only 10 applied, then blocking in futures?)
#            print i 
#            component.moveRel({axis_name: distance})
        move = component.moveRel({axis_name: distance})
        move.result() # TODO: flag for sync? FIXME: it seems to fail sometimes if quiting before the end
    except:
        logging.error("Failed to move axis %s of component %s", axis_name, comp_name)
        return 127
    
    return 0

def stop_move():
    """
    stop the move of every axis of every actuators
    """
    # We actually just browse as a tree the microscope 
    try:
        microscope = model.getMicroscope()
        actuators = microscope.actuators
    except:
        logging.error("Failed to contact the back-end")
        return 127
    
    ret = 0
    for actuator in actuators:
        try:
            actuator.stop()
        except:
            logging.error("Failed to stop actuator %s", actuator.name)
            ret = 127
    
    return ret

def acquire(comp_name, dataflow_names, filename):
    """
    Acquire an image from one (or more) dataflow
    comp_name (string): name of the detector to find
    dataflow_names (list of string): name of each dataflow to access
    filename (string): name of the output file (will be TIFF with one page per dataflow)
    """
    try:
        component = get_detector(comp_name)
    except LookupError:
        logging.error("Failed to find detector '%s'", comp_name)
        return 127
    except:
        logging.error("Failed to contact the back-end")
        return 127
    
    # check the dataflow exists
    dataflows = []
    for df_name in dataflow_names:
        try:
            df = getattr(component, df_name)
        except:
            logging.error("Failed to find data-flow '%s' on component '%s'", df_name, comp_name)
            return 129
        
        if not isinstance(df, model.DataFlowBase):
            logging.error("'%s' is not a data-flow of component '%s'", df_name, comp_name)
            return 129
        dataflows.append(df)
    
    # TODO support multiple dataflows with multiple pages in the file
    images = []
    for df in dataflows:
        try:
            image = df.get()
            images.append(image)
            logging.info("Acquired an image of dimension %r.", image.shape)
        except:
            logging.error("Failed to acquire image from component '%s'", comp_name)
            return 127
    
    tiff.export(images[0], filename)
    return 0

def live_display(comp_name, df_name):
    """
    Acquire an image from one (or more) dataflow
    comp_name (string): name of the detector to find
    df_name (string): name of the dataflow to access
    """
    try:
        component = get_detector(comp_name)
    except LookupError:
        logging.error("Failed to find detector '%s'", comp_name)
        return 127
    except:
        logging.error("Failed to contact the back-end")
        return 127
    
    # check the dataflow exists
    try:
        df = getattr(component, df_name)
    except:
        logging.error("Failed to find data-flow '%s' on component '%s'", df_name, comp_name)
        return 129
    
    if not isinstance(df, model.DataFlowBase):
        logging.error("'%s' is not a data-flow of component '%s'", df_name, comp_name)
        return 129
    
    print "Press 'Q' to quit"
    # create a window
    size = component.resolution.value
    window = VideoDisplayer("Live from %s.%s" % (comp_name, df_name), size)
    
        # update the picture and wait
    def new_image_wrapper(df, image):
        window.new_image(image)
    try:
        df.subscribe(new_image_wrapper)
        
        # wait until the window is closed
        window.waitQuit()
    finally:
        df.unsubscribe(new_image_wrapper)

def main(args):
    """
    Handles the command line arguments 
    args is the list of arguments passed
    return (int): value to return to the OS as program exit code
    """

    # arguments handling 
    parser = argparse.ArgumentParser(description=__version__.name)

    parser.add_argument('--version', dest="version", action='store_true',
                        help="show program's version number and exit")
    opt_grp = parser.add_argument_group('Options')
    opt_grp.add_argument("--log-level", dest="loglev", metavar="<level>", type=int,
                        default=0, help="Set verbosity level (0-2, default = 0)")
    dm_grp = parser.add_argument_group('Microscope management')
    dm_grpe = dm_grp.add_mutually_exclusive_group()
    dm_grpe.add_argument("--kill", "-k", dest="kill", action="store_true", default=False,
                         help="Kill the running back-end")
    dm_grpe.add_argument("--check", dest="check", action="store_true", default=False,
                         help="Check for a running back-end (only returns exit code)")
    dm_grpe.add_argument("--scan", dest="scan", action="store_true", default=False,
                         help="Scan for possible devices to connect (the back-end must be stopped)")
    dm_grpe.add_argument("--list", "-l", dest="list", action="store_true", default=False,
                         help="List the components of the microscope")
    dm_grpe.add_argument("--list-prop", "-L", dest="listprop", metavar="<component>",
                         help="List the properties of a component")
    dm_grpe.add_argument("--set-attr", "-s", dest="setattr", nargs=3, action='append',
                         metavar=("<component>", "<attribute>", "<value>"),
                         help="Set the attribute of a component (lists are delimited by commas)")
    dm_grpe.add_argument("--move", "-m", dest="move", nargs=3, action='append',
                         metavar=("<component>", "<axis>", "<distance>"),
                         help=u"move the axis by the amount of µm.")
    dm_grpe.add_argument("--stop", "-S", dest="stop", action="store_true", default=False,
                         help="Immediately stop all the actuators in all directions.")
    dm_grpe.add_argument("--acquire", "-a", dest="acquire", nargs="+", 
                         metavar=("<component>", "data-flow"),
                         help="Acquire an image (default data-flow is \"data\")")
    dm_grp.add_argument("--output", "-o", dest="output",
                        help="name of the file where the image should be saved after acquisition. It is saved in TIFF format.")
    dm_grpe.add_argument("--live", dest="live", nargs="+", 
                         metavar=("<component>", "data-flow"),
                         help="Display and update an image on the screen (default data-flow is \"data\")")
    
    options = parser.parse_args(args[1:])
    
    # Cannot use the internal feature, because it doesn't support multiline
    if options.version:
        print (__version__.name + " " + __version__.version + "\n" +
               __version__.copyright + "\n" + 
               "Licensed under the " + __version__.license)
        return 0
    
    # Set up logging before everything else
    if options.loglev < 0:
        parser.error("log-level must be positive.")
    loglev_names = [logging.WARNING, logging.INFO, logging.DEBUG]
    loglev = loglev_names[min(len(loglev_names) - 1, options.loglev)]
    logging.getLogger().setLevel(loglev)
    
    # change the log format to be more descriptive
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s (%(module)s) %(levelname)s: %(message)s'))
    logging.getLogger().addHandler(handler)
    
    # anything to do?
    if (not options.check and not options.kill and not options.scan 
        and not options.list and not options.stop and options.move is None
        and options.listprop is None and options.setattr is None
        and options.acquire is None and options.live is None):
        logging.error("no action specified.")
        return 127
    if options.acquire is not None and options.output is None:
        logging.error("name of the output file must be specified.")
        return 127

    
    status = get_backend_status()
    if options.check:
        logging.info("Status of back-end is %s", status)
        return status_to_xtcode[status]
    
    # scan needs to have the backend stopped
    if options.scan:
        if status == BACKEND_RUNNING:
            logging.error("Back-end running while trying to scan for devices")
            return 127
        try:
            return scan()
        except:
            logging.exception("Unexpected error while performing scan.")
            return 127
    
    # check if there is already a backend running
    if status == BACKEND_STOPPED:
        logging.error("No running back-end")
        return 127
    elif status == BACKEND_DEAD:
        logging.error("Back-end appears to be non-responsive.")
        return 127
    
    try:
        if options.kill:
            return kill_backend()
    
        if options.list:
            return list_components()
        
        if options.listprop is not None:
            return list_properties(options.listprop)
        
        if options.setattr is not None:
            for c, a, v in options.setattr:
                ret = set_attr(c, a, v)
                if ret != 0:
                    return ret
            return 0
        
        if options.move is not None:
            for c, a, d in options.move:
                ret = move(c, a, d)
                # TODO move commands to the same actuator should be agglomerated
                if ret != 0:
                    return ret
            return 0
        
        if options.stop:
            return stop_move()
        
        if options.acquire is not None:
            component = options.acquire[0]
            if len(options.acquire) == 1:
                dataflows = ["data"]
            else:
                dataflows = options.acquire[1:]
            acquire(component, dataflows, options.output)
          
        if options.live is not None:
            component = options.live[0]
            if len(options.live) == 1:
                dataflow = "data"
            elif len(options.live) == 2:
                dataflow = options.acquire[2]
            else:
                logging.error("live command accepts only one data-flow")
                return 127
            live_display(component, dataflow)
    except:
        logging.exception("Unexpected error while performing action.")
        return 127
    
    return 0

if __name__ == '__main__':
    ret = main(sys.argv)
    logging.shutdown() 
    exit(ret)
    
# vim:tabstop=4:shiftwidth=4:expandtab:spelllang=en_gb:spell: