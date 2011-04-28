import sys
import zlib
import urllib
import xml.sax.saxutils

from traceback import print_exc

__author__ = "Markus Guenther"

INDENT_CHAR = "\t"

'''This module provides the public method serialize which can be used to
serialize simple data structures like lists and dictionaries, along with
primitive types for the values those structures contain. Other Python built-in
data structures, like tuples etc., are not supported by this implementation.

The module can be used as follows:

<code>
from SisClient.Testbed.Reporting import serialize

xml_string = serialize.serialize(data_structure, compress=False, encodeBase64=False)
</code>

<code>xml_string</code> contains the serialized XML string of the given data
structure. The two optional parameters can be omitted, if the default values
(both False) shall be used. See the documentation of <code>serialize</code>
for further information.

Some example serializations:
1. Nested lists
<code>
test_list = [1, 2, [3, 4]]
print serialize.serialize(test_list)
</code>
will write the following to the standard output:
<code>
<list name="parent" type="list">
    <item type="int">1</item>
    <item type="int">2</item>
    <item type="list">
        <list name="0" type="list">
            <item type="int">3</item>
            <item type="int">4</item>
        </list>
    </item>
</list>
</code>

2. Nested dictionaries
<code>
test_dict = {'some_value'   :   3,
             'some_dict'    :   {
                                'sub_value'    :   2
                                },
             'some_another_dict'  :  {
                                      'sub_value1'   : 5,
                                      'sub_value2'   : 6
                                     }
            }
print serialize.serialize(test_dict)
</code>
will write the following to the standard output:
<code>
<map name="parent">
    <key name="some_dict" type="dict">
        <map name="some_dict">
            <key name="sub_value" type="int">2</key>
        </map>
    </key>
    <key name="some_value" type="int">3</key>
    <key name="some_another_dict" type="dict">
        <map name="some_another_dict">
            <key name="sub_value2" type="int">6</key>
            <key name="sub_value1" type="int">5</key>
        </map>
    </key>
</map>
</code>
'''

#_______________________________________________________________________________
# PUBLIC SECTION

class SerializationException(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)
    
def serialize(ds, compress=False, encodeBase64=False):
    '''Serializes a given data structure <code>ds</code> into an XML formatted
    string. Returns this string. The optional parameter compress determines if 
    the string shall be compressed before it is dispatched to the caller. This
    parameter is False by default. The second optional parameter encodeBase64
    determines if the string shall be encoded in Base64 format. This parameter
    is by default also set to False.
    '''
    dispatch = ""
    if isinstance(ds, dict):
        dispatch += _serialize_dict(ds)
    elif isinstance(ds, list):
        dispatch += _serialize_list(ds)
    elif isinstance(ds, tuple):
        dispatch += _serialize_tuple(ds)
    else:
        # the data structure is neither a list nor dictionary, so we cannot
        # perform the serialization.
        raise SerializationException("The given data structure is neither a list " + \
                                     "nor a dictionary. It cannot be serialized.")
    if compress:
        dispatch = zlib.compress(dispatch,9)
    if encodeBase64:
        dispatch = dispatch.encode("base64")
        
    return dispatch

#_______________________________________________________________________________
# PRIVATE SECTION
    
def _get_primitive_type_as_string(value):
    if isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, complex):
        return "complex"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, long):
        return "long"
    else:
        raise SerializationException("Unknown type of object %s with type %s" %
                                     (value, value.__class__))
        
def _serialize_tuple(dt, name=None, indent=0):
    if name is None:
        name = "parent"
    serialized_tuple = _add_tuple_begin_tag(indent)
    values = "\n"
    for i in xrange(len(dt)):
        if isinstance(dt[i], dict): 
            values += INDENT_CHAR*(indent+1)+'<value at="%i">\n%s</value>\n' % (i, _serialize_dict(dt[i], str(i), indent+2))
        elif isinstance(dt[i], list):
            values += INDENT_CHAR*(indent+1)+'<value at="%i">\n%s</value>\n' % (i, _serialize_list(dt[i], str(i), indent+2))
            values += INDENT_CHAR*(indent+1)+"</value>\n"
        elif isinstance(dt[i], tuple):
            values += INDENT_CHAR*(indent+1)+'<value at="%i">\n%s</value>\n' % (i, _serialize_tuple(dt[i], str(i), indent+2))
            values += INDENT_CHAR*(indent+1)+"</value>\n"
        else:
            values += INDENT_CHAR*(indent+1)+'<value at="%i">%s</value>\n' % (i, xml.sax.saxutils.escape(str(dt[i])))
    serialized_tuple += values
    serialized_tuple += _add_tuple_close_tag(indent)
    return serialized_tuple

def _serialize_list(dt, name=None, indent=0):
    if name is None:
        name = "parent"
    ll = _add_list_begin_tag(name, indent)
    items = ""
    i = 0
    for item in dt:
        if isinstance(item, dict):
            items += INDENT_CHAR*(indent+1)+"<item>\n%s</item>\n" % _serialize_dict(item, str(i), indent+2)
            i += 1
        elif isinstance(item, list):
            items += INDENT_CHAR*(indent+1)+"<item>\n%s" % _serialize_list(item, str(i), indent+2)
            items += INDENT_CHAR*(indent+1)+"</item>\n"
            i += 1
        elif isinstance(item, tuple):
            items += INDENT_CHAR*(indent+1)+"<item>\n%s" % _serialize_tuple(item, str(i), indent+2)
            items += INDENT_CHAR*(indent+1)+"</item>\n"
            i += 1
        else:
            type_as_string = _get_primitive_type_as_string(item)
            items += INDENT_CHAR*(indent+1)+"<item>%s</item>\n" % xml.sax.saxutils.escape(str(item))
    ll += items
    ll += _add_list_close_tag(indent)
    return ll
    
def _serialize_dict(dt, name=None, indent=0):
    '''Serializes a given dict which contains only primitives or other dicts
       into an XML format.
    '''
    if name is None:
        name = "parent"    
    map = _add_map_begin_tag(name, indent)
    for key in dt.keys():
        value = dt[key]
        if isinstance(value, dict):
            #map += _serialize_dict(value, key, indent+1)
            map += _add_key_value_pair(key, _serialize_dict(value, key, indent+2), "dict", indent)
        elif isinstance(value, list):
            #map += _serialize_list(value, key, indent+1)
            map += _add_key_value_pair(key, _serialize_list(value, key, indent+2), "list", indent)
        elif isinstance(value, tuple):
            map += _add_key_value_pair(key, _serialize_tuple(value, key, indent+2), "tuple", indent)
        else:
            try:
                type_as_string = _get_primitive_type_as_string(value)
                map += _add_key_value_pair(key, xml.sax.saxutils.escape(str(value)), type_as_string, indent)
            except:
                pass
            
    map += _add_map_close_tag(indent)
    
    return map

def _add_tuple_begin_tag(indent):
    return INDENT_CHAR * indent + "%s" % "<tuple>"

def _add_tuple_close_tag(indent):
    dispatch = INDENT_CHAR * indent + "</tuple>"
    if indent is not 0:
        dispatch += "\n"
    return dispatch

def _add_list_begin_tag(name, indent):
    return INDENT_CHAR * indent + "%s" % "<list name=\"%s\">\n" % name

def _add_list_close_tag(indent):
    dispatch = INDENT_CHAR * indent + "</list>"
    if indent is not 0:
        dispatch += "\n"
    return dispatch

def _add_map_begin_tag(name, indent):
    return INDENT_CHAR * indent + "%s" % "<map name=\"%s\">\n" % name
    
def _add_map_close_tag(indent):
    dispatch = INDENT_CHAR * indent + "</map>"
    if indent is 0:
        return dispatch
    else:
        return dispatch + "\n"
    
def _add_key_value_pair(key, value, type, indent):
    dispatch = ""
    if type is "list" or type is "dict" or type is "tuple":
        dispatch = _xml_entry_complex(key, value, indent)
    else:
        dispatch = _xml_entry(key, value, indent)
        
    return dispatch
            
def _xml_entry(key, value, indent):
    return INDENT_CHAR*(indent+1)+"<key name=\"%s\">%s</key>\n" % (key, str(value))

def _xml_entry_complex(key, value, indent):
    dispatch = INDENT_CHAR*(indent+1) + "<key name=\"%s\">\n" % key
    dispatch += INDENT_CHAR*(indent) + "%s" % value # value has the corrent indentation
    dispatch += INDENT_CHAR*(indent+1) + "</key>\n"
    return dispatch
