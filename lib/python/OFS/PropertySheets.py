##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""Property sheets"""
__version__='$Revision: 1.51 $'[11:-2]

import time, string, App.Management, Globals
from ZPublisher.Converters import type_converters
from DocumentTemplate.DT_Util import html_quote
from Globals import HTMLFile, MessageDialog
from string import find,join,lower,split,rfind
from Acquisition import Implicit, Explicit
from App.Common import rfc1123_date
from webdav.common import urlbase
from ExtensionClass import Base
from Globals import Persistent
from Traversable import Traversable

class View(App.Management.Tabs, Base):
    """A view of an object, typically used for management purposes
    """

    def manage_workspace(self, URL1, RESPONSE):
        '''Implement a "management" interface
        '''
        RESPONSE.redirect(URL1+'/manage')

    def tpURL(self): return self.id
        
    def manage_options(self):
        """Return a manage option data structure for me instance
        """
        try: r=self.REQUEST
        except: r=None
        if r is None:
            pre='../../'
        else:
            pre=r['URL']
            for i in (1,2,3):
                l=rfind(pre,'/')
                if l >= 0:
                    pre=pre[:l]
            pre=pre+'/'
            
        r=[]
        for d in self.aq_parent.aq_parent.manage_options:
            path=d['action']
            option={'label': d['label'],
                      'action': pre+path,
                      'path': '../../'+path}
            help=d.get('help')
            if help is not None:
                option['help']=help
            r.append(option)
        return r

    def tabs_path_info(self, script, path):
        l=rfind(path,'/')
        if l >= 0:
            path=path[:l]
            l=rfind(path,'/')
            if l >= 0: path=path[:l]
        return View.inheritedAttribute('tabs_path_info')(
            self, script, path)

    def meta_type(self):
        try: return self.aq_parent.aq_parent.meta_type
        except: return ''


class PropertySheet(Traversable, Persistent, Implicit):
    """A PropertySheet is a container for a set of related properties and
       metadata describing those properties. PropertySheets may or may not
       provide a web interface for managing its properties."""

    _properties=()
    _extensible=1
    icon='p_/Properties_icon'
    
    def property_extensible_schema__(self): return self._extensible

    def __init__(self, id, md=None):
        # Create a new property set, using the given id and namespace
        # string. The namespace string should be usable as an xml name-
        # space identifier.
        self.id=id
        self._md=md or {}
        
    def xml_namespace(self):
        # Return a namespace string usable as an xml namespace
        # for this property set.
        return self._md.get('xmlns', '')

    def v_self(self):
        return self

    def p_self(self):
        return self.v_self()

    def valid_property_id(self, id):
        # Return a true value if the given id is valid to use as 
        # a property id. Note that this method does not consider 
        # factors other than the actual value of the id, such as 
        # whether the given id is already in use.
        if not id or (id[:1]=='_') or (' ' in id):
            return 0
        return 1

    def hasProperty(self, id):
        # Return a true value if a property exists with the given id.
        for prop in self.propertyMap():
            if id==prop['id']:
                return 1
        return 0

    def getProperty(self, id, default=None):
        # Return the property with the given id, returning the optional
        # second argument or None if no such property is found.
        if self.hasProperty(id):
            return getattr(self.v_self(), id)
        return default

    def _wrapperCheck(self, object):
        # Raise an error if an object is wrapped.
        if hasattr(object, 'aq_base'):
            raise ValueError, 'Invalid property value: wrapped object'
        return

    def getPropertyType(self, id):
        """Get the type of property 'id', returning None if no
           such property exists"""
        pself=self.p_self()
        self=self.v_self()
        for md in pself._properties:
            if md['id']==id:
                return md.get('type', 'string')
        return None

    def _setProperty(self, id, value, type='string', meta=None):
        # Set a new property with the given id, value and optional type.
        # Note that different property sets may support different typing
        # systems.
        self._wrapperCheck(value)
        if not self.valid_property_id(id):
            raise 'Bad Request', 'Invalid property id, %s.' % id
        if not self.property_extensible_schema__():
            raise 'Bad Request', (
                'Properties cannot be added to this property sheet')
        pself=self.p_self()
        self=self.v_self()
        if hasattr(aq_base(self),id):
            if not (id=='title' and not self.__dict__.has_key(id)):
                raise 'Bad Request', (
                    'Invalid property id, <em>%s</em>. It is in use.' % id)
        if meta is None: meta={}
        prop={'id':id, 'type':type, 'meta':meta}
        pself._properties=pself._properties+(prop,)
        if type in ('selection', 'multiple selection'):
            if not value:
                raise 'Bad Request', (
                    'The value given for a new selection property '
                    'must be a variable name<p>')
            prop['select_variable']=value
            if type=='selection': value=None
            else: value=[]
        setattr(self, id, value)

    def _updateProperty(self, id, value, meta=None):
        # Update the value of an existing property. If value is a string,
        # an attempt will be made to convert the value to the type of the
        # existing property. If a mapping containing meta-data is passed,
        # it will used to _replace_ the properties meta data.
        self._wrapperCheck(value)
        if not self.hasProperty(id):
            raise 'Bad Request', 'The property %s does not exist.' % id
        propinfo=self.propertyInfo(id)
        if not 'w' in propinfo.get('mode', 'wd'):
            raise 'Bad Request', '%s cannot be changed.' % id
        if type(value)==type(''):
            proptype=propinfo.get('type', 'string')
            if type_converters.has_key(proptype):
                value=type_converters[proptype](value)
        if meta is not None:
            props=[]
            pself=self.p_self()
            for prop in pself._properties:
                if prop['id']==id: prop['meta']=meta
                props.append(prop)
            pself._properties=tuple(props)
        setattr(self.v_self(), id, value)

    def _delProperty(self, id):
        # Delete the property with the given id. If a property with the
        # given id does not exist, a ValueError is raised.
        if not self.hasProperty(id):
            raise 'Bad Request', 'The property %s does not exist.' % id
        vself=self.v_self()
        if hasattr(vself, '_reserved_names'):
            nd=vself._reserved_names
        else: nd=()
        if (not 'd' in self.propertyInfo(id).get('mode', 'wd')) or (id in nd):
            raise 'Bad Request', '%s cannot be deleted.' % id
        delattr(vself, id)
        pself=self.p_self()
        pself._properties=tuple(filter(lambda i, n=id: i['id'] != n,
                                       pself._properties))

    def propertyIds(self):
        # Return a list of property ids.
        return map(lambda i: i['id'], self.propertyMap())

    def propertyValues(self):
        # Return a list of property values.
        return map(lambda i, s=self: s.getProperty(i['id']),
                   self.propertyMap())

    def propertyItems(self):
        # Return a list of (id, property) tuples.
        return map(lambda i, s=self: (i['id'], s.getProperty(i['id'])), 
                   self.propertyMap())

    def propertyInfo(self, id):
        # Return a mapping containing property meta-data
        for p in self.propertyMap():
            if p['id']==id: return p
        raise ValueError, 'The property %s does not exist.' % id

    def propertyMap(self):
        # Return a tuple of mappings, giving meta-data for properties.
        # Some ZClass instances dont seem to have an _properties, so
        # we have to fake it...
        return self.p_self()._properties




    def _propdict(self):
        dict={}
        for p in self.propertyMap():
            dict[p['id']]=p
        return dict

    propstat='<d:propstat xmlns:n="%s">\n' \
             '  <d:prop>\n' \
             '%s\n' \
             '  </d:prop>\n' \
             '  <d:status>HTTP/1.1 %s</d:status>\n%s' \
             '</d:propstat>\n'

    propdesc='  <d:responsedescription>\n' \
             '  %s\n' \
             '  </d:responsedescription>\n'

    def dav__allprop(self, propstat=propstat, join=string.join):
        # DAV helper method - return one or more propstat elements
        # indicating property names and values for all properties.
        result=[]
        for item in self.propertyMap():
            name, type=item['id'], item.get('type','string')
            value=self.getProperty(name)
            if type=='tokens':
                value=join(value, ' ')
            elif type=='lines':
                value=join(value, '\n')
            # check for xml property
            attrs=item.get('meta', {}).get('__xml_attrs__', None)
            if attrs is not None:
                attrs=map(lambda n: ' %s="%s"' % n, attrs.items())
                attrs=join(attrs, '')
            else:
                # Quote non-xml items here?
                attrs='' 
            prop='  <n:%s%s>%s</n:%s>' % (name, attrs, value, name)
            result.append(prop)
        if not result: return ''
        result=join(result, '\n')
        return propstat % (self.xml_namespace(), result, '200 OK', '')

    def dav__propnames(self, propstat=propstat, join=string.join):
        # DAV helper method - return a propstat element indicating
        # property names for all properties in this PropertySheet.
        result=[]
        for name in self.propertyIds():
            result.append('  <n:%s/>' % name)
        if not result: return ''
        result=join(result, '\n')
        return propstat % (self.xml_namespace(), result, '200 OK', '')


    def dav__propstat(self, name, result,
                      propstat=propstat, propdesc=propdesc,
                      join=string.join):
        # DAV helper method - return a propstat element indicating
        # property name and value for the requested property.
        xml_id=self.xml_namespace()
        propdict=self._propdict()
        if not propdict.has_key(name):
            prop='<n:%s xmlns:n="%s"/>\n' % (name, xml_id)
            code='404 Not Found'
            if not result.has_key(code):
                result[code]=[prop]
            else: result[code].append(prop)
            return
        else:
            item=propdict[name]
            name, type=item['id'], item.get('type','string')
            value=self.getProperty(name)
            if type=='tokens':
                value=join(value, ' ')
            elif type=='lines':
                value=join(value, '\n')
            # allow for xml properties
            attrs=item.get('meta', {}).get('__xml_attrs__', None)
            if attrs is not None:
                attrs=map(lambda n: ' %s="%s"' % n, attrs.items())
                attrs=join(attrs, '')
            else:
                # quote non-xml items here?
                attrs=''
            prop='<n:%s%s xmlns:n="%s">%s</n:%s>\n' % (
                 name, attrs, xml_id, value, name)
            code='200 OK'
            if not result.has_key(code):
                result[code]=[prop]
            else: result[code].append(prop)
            return            


    del propstat
    del propdesc


    # Web interface
    
    manage=HTMLFile('properties', globals())
    def manage_propertiesForm(self, URL1):
        " "
        raise 'Redirect', URL1+'/manage'

    def manage_addProperty(self, id, value, type, REQUEST=None):
        """Add a new property via the web. Sets a new property with
        the given id, type, and value."""
        if type_converters.has_key(type):
            value=type_converters[type](value)
        self._setProperty(id, value, type)
        if REQUEST is not None:
            return self.manage(self, REQUEST)

    def manage_changeProperties(self, REQUEST=None, **kw):
        """Change existing object properties by passing either a mapping
           object of name:value pairs {'foo':6} or passing name=value
           parameters."""
        if REQUEST is None: props={}
        else: props=REQUEST
        if kw:
            for name, value in kw.items():
                props[name]=value
        propdict=self._propdict()
        for name, value in props.items():
            if self.hasProperty(name):
                self._updateProperty(name, value)
        if REQUEST is not None:
            return MessageDialog(
                title  ='Success!',
                message='Your changes have been saved.',
                action ='manage')

    def manage_editProperties(self, REQUEST):
        """Edit object properties via the web."""
        for prop in self.propertyMap():
            name=prop['id']
            if REQUEST.has_key(name):
                value=REQUEST.get(name)
                self._updateProperty(name, value)
        return MessageDialog(
               title  ='Success!',
               message='Your changes have been saved',
               action ='manage')

    def manage_delProperties(self, ids=None, REQUEST=None):
        """Delete one or more properties specified by 'ids'."""
        if ids is None:
            return MessageDialog(
                   title='No property specified',
                   message='No properties were specified!',
                   action ='./manage',)
        for id in ids:
            self._delProperty(id)
        if REQUEST is not None:
            return self.manage(self, REQUEST)

class Virtual:

    def __init__(self):
        pass
    
    def v_self(self):
        return self.aq_parent.aq_parent

class DefaultProperties(Virtual, PropertySheet, View):
    """The default property set mimics the behavior of old-style Zope
       properties -- it stores its property values in the instance of
       its owner."""

    id='default'
    _md={'xmlns': 'http://www.zope.org/propsets/default'}


class DAVProperties(Virtual, PropertySheet, View):
    """WebDAV properties"""

    id='webdav'
    _md={'xmlns': 'DAV:'}
    pm=({'id':'creationdate',     'mode':'r'},
        {'id':'displayname',      'mode':'r'},
        {'id':'resourcetype',     'mode':'r'},
        {'id':'getlastmodified',  'mode':'r'},
        {'id':'getcontenttype',   'mode':'r'},
        {'id':'getcontentlength', 'mode':'r'},
        {'id':'source',           'mode':'r'},
        )

    def getProperty(self, id, default=None):
        method='dav__%s' % id
        if not hasattr(self, method):
            return default
        return getattr(self, method)()

    def _setProperty(self, id, value, type='string', meta=None):
        raise ValueError, '%s cannot be set.' % id

    def _updateProperty(self, id, value):
        raise ValueError, '%s cannot be updated.' % id

    def _delProperty(self, id):
        raise ValueError, '%s cannot be deleted.' % id

    def propertyMap(self):
        return self.pm
    
    def dav__creationdate(self):
        return ''

    def dav__displayname(self):
        return absattr(self.v_self().id)

    def dav__resourcetype(self):
        vself=self.v_self()
        if hasattr(aq_base(vself), 'isAnObjectManager') and \
           vself.isAnObjectManager:
            return '<n:collection/>'
        return ''

    def dav__getlastmodified(self):
        vself=self.v_self()
        if hasattr(vself, '_p_mtime'):
            return rfc1123_date(vself._p_mtime)
        return ''

    def dav__getcontenttype(self):
        vself=self.v_self()
        if hasattr(vself, 'content_type'):
            return vself.content_type
        return ''

    def dav__getcontentlength(self):
        vself=self.v_self()
        if hasattr(vself, 'get_size'):
            return vself.get_size()
        return ''

    def dav__source(self):
        vself=self.v_self()
        if hasattr(vself, 'document_src'):
            url=urlbase(vself.absolute_url())
            return '\n  <n:link>\n' \
                   '  <n:src>%s</n:src>\n' \
                   '  <n:dst>%s/document_src</n:dst>\n' \
                   '  </n:link>\n  ' % (url, url)
        return ''

    def dav__supportedlock(self):
        return '\n  <n:lockentry>\n' \
               '  <d:lockscope><d:exclusive/></d:lockscope>\n' \
               '  <d:locktype><d:write/></d:locktype>\n' \
               '  </n:lockentry>\n  '


class PropertySheets(Traversable, Implicit, App.Management.Tabs):
    """A tricky container to keep property sets from polluting
       an object's direct attribute namespace."""
    
    id='propertysheets'

    webdav =DAVProperties()
    def _get_defaults(self):
        return (self.webdav,)
    
    def __propsets__(self):
        propsets=self.aq_parent.__propsets__
        __traceback_info__= propsets, type(propsets)
        return self._get_defaults() + propsets

    def __bobo_traverse__(self, REQUEST, name=None):
        for propset in self.__propsets__():
            if propset.id==name:
                return propset.__of__(self)
        return getattr(self, name)

    def __getitem__(self, n):
        return self.__propsets__()[n].__of__(self)

    def values(self):
        propsets=self.__propsets__()
        return map(lambda n, s=self: n.__of__(s), propsets)

    def items(self):
        propsets=self.__propsets__()
        r=[]
        for n in propsets:
            if hasattr(n,'id'): id=n.id
            else: id=''
            r.append((id, n.__of__(self)))

        return r
        
    def get(self, name, default=None):
        for propset in self.__propsets__():
            if propset.id==name or propset.xml_namespace()==name:
                return propset.__of__(self)
        return default

    def manage_addPropertySheet(self, id, ns):
        """ """
        md={'xmlns':ns}
        ps=PropertySheet(id, md)
        self.addPropertySheet(ps)
        return 'OK'

    def addPropertySheet(self, propset):
        propsets=self.aq_parent.__propsets__
        propsets=propsets+(propset,)
        self.aq_parent.__propsets__=propsets

    def delPropertySheet(self, name):
        result=[]
        for propset in self.aq_parent.__propsets__:
            if propset.id != name and  propset.xml_namespace() != name:
                result.append(propset)
        self.parent.__propsets__=tuple(result)

    # Why?
    #def __del__(self):
    #    self.parent=None
        
    def __len__(self):
        return len(self.__propsets__())


    # Management interface:

    manage=Globals.HTMLFile('propertysheets', globals())

    def manage_options(self):
        """Return a manage option data structure for me instance
        """
        try: r=self.REQUEST
        except: r=None
        if r is None:
            pre='../'
        else:
            pre=r['URL']
            for i in (1,2):
                l=rfind(pre,'/')
                if l >= 0:
                    pre=pre[:l]
            pre=pre+'/'
            
        r=[]
        for d in self.aq_parent.manage_options:
            r.append({'label': d['label'], 'action': pre+d['action']})
        return r

    def tabs_path_info(self, script, path):
        l=rfind(path,'/')
        if l >= 0: path=path[:l]
        return PropertySheets.inheritedAttribute('tabs_path_info')(
            self, script, path)


class DefaultPropertySheets(PropertySheets):
    """A PropertySheets container that contains a default property
       sheet for compatibility with the arbitrary property mgmt
       design of Zope PropertyManagers."""
    default=DefaultProperties()
    webdav =DAVProperties()
    def _get_defaults(self):
        return (self.default, self.webdav)


class FixedSchema(PropertySheet):

    def __init__(self, id, base, md=None):
        FixedSchema.inheritedAttribute('__init__')(self, id, md)
        self._base=base

    def propertyMap(self):
        # Return a tuple of mappings, giving meta-data for properties.
        r=[]
        for d in self._base.propertyMap():
            mode=d.get('mode', 'wd')
            if 'd' in mode:
                dd={}
                dd.update(d)
                d=dd
                d['mode']=filter(lambda c: c != 'd', mode)
            r.append(d)
            
        return tuple(r)

    def property_extensible_schema__(self):
        return 0
        return self._base._extensible
    


class vps(Base):
    # The vps object implements a "computed attribute" - it ensures
    # that a PropertySheets instance is returned when the propertysheets
    # attribute of a PropertyManager is accessed.
    def __init__(self, c=PropertySheets):
        self.c=c
        
    def __of__(self, parent):
        return self.c().__of__(parent)

def absattr(attr):
    if callable(attr):
        return attr()
    return attr

def aq_base(ob):
    if hasattr(ob, 'aq_base'):
        return ob.aq_base
    return ob
