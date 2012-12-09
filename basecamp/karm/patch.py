"""Patch vobject python iCalendar library

iCalendar format allows us to extend existing components with our own
content lines. These lines should start with 'X-' string.

KArm uses this extending possibility extensively for it's time logging.
E. g.:
  X-KDE-karm-totalSessionTime:0^M
  X-KDE-karm-totalTaskTime:0^M

As you see, here we have property names with lower cased letters.
But by using vobject python library it's impossible to serialize
lower cased property names. This library suppress all content lines and
components names to be in upper case.

That's why we should patch this library to allow us to create iCalendar
file for KArm.

"""

import cStringIO
import codecs

import vobject.base
from vobject.base import ContentLine, Component, foldOneLine

def karm_defaultSerialize(obj, buf, lineLength):
    """Encode and fold obj and its children, write to buf or return a string."""

    outbuf = buf or cStringIO.StringIO()

    if isinstance(obj, Component):
        if obj.group is None:
            groupString = ''
        else:
            groupString = obj.group + '.'
        if obj.useBegin:
            foldOneLine(outbuf, str(groupString + u"BEGIN:" + obj.name), lineLength)
        for child in obj.getSortedChildren():
            #validate is recursive, we only need to validate once
            child.serialize(outbuf, lineLength, validate=False)
        if obj.useBegin:
            foldOneLine(outbuf, str(groupString + u"END:" + obj.name), lineLength)
    elif isinstance(obj, ContentLine):
        startedEncoded = obj.encoded
        if obj.behavior and not startedEncoded: obj.behavior.encode(obj)
        s=codecs.getwriter('utf-8')(cStringIO.StringIO()) #unfolded buffer
        if obj.group is not None:
            s.write(obj.group + '.')
        ####################################################################
        # this is an actual patch: make name uppercase unless it's extension
        name = obj.name
        if not name.startswith('X-'):
            name = name.upper()
        s.write(obj.name)
        ####################################################################
        for key, paramvals in obj.params.iteritems():
            s.write(';' + key + '=' + ','.join(quoteEscape(p) for p in paramvals))
        s.write(':' + obj.value)
        if obj.behavior and not startedEncoded: obj.behavior.decode(obj)
        foldOneLine(outbuf, s.getvalue(), lineLength)

    return buf or outbuf.getvalue()

# first backup original method
vobject.base._old_defaultSerialize = vobject.base.defaultSerialize
# then patch
vobject.base.defaultSerialize = karm_defaultSerialize

def karm_contentline_init__(self, name, params, value, group=None,
                            encoded=False, isNative=False,
                            lineNumber = None, *args, **kwds):
        """Take output from parseLine, convert params list to dictionary."""
        # group is used as a positional argument to match parseLine's return
        super(ContentLine, self).__init__(group, *args, **kwds)
        ####################################################################
        # this is an actual patch: make name uppercase unless it's extension
        if not name.startswith('X-'):
            name = name.upper()
        self.name        = name
        ####################################################################
        self.value       = value
        self.encoded     = encoded
        self.params      = {}
        self.singletonparams = []
        self.isNative = isNative
        self.lineNumber = lineNumber
        def updateTable(x):
            if len(x) == 1:
                self.singletonparams += x
            else:
                paramlist = self.params.setdefault(x[0].upper(), [])
                paramlist.extend(x[1:])
        map(updateTable, params)
        qp = False
        if 'ENCODING' in self.params:
            if 'QUOTED-PRINTABLE' in self.params['ENCODING']:
                qp = True
                self.params['ENCODING'].remove('QUOTED-PRINTABLE')
                if 0==len(self.params['ENCODING']):
                    del self.params['ENCODING']
        if 'QUOTED-PRINTABLE' in self.singletonparams:
            qp = True
            self.singletonparams.remove('QUOTED-PRINTABLE')
        if qp:
            self.value = str(self.value).decode('quoted-printable')

        # self.value should be unicode for iCalendar, but if quoted-printable
        # is used, or if the quoted-printable state machine is used, text may be
        # encoded
        if type(self.value) is str:
            charset = 'iso-8859-1'
            if 'CHARSET' in self.params:
                charsets = self.params.pop('CHARSET')
                if charsets:
                    charset = charsets[0]
            self.value = unicode(self.value, charset)

# first backup original method
ContentLine.__old_init__ = ContentLine.__init__
# then patch
ContentLine.__init__ = karm_contentline_init__
