#!/data/work/pythons/python-2.4.5/bin/python

"""KArm class

KArm wrapper to make it easier work with karm data (*.ics) file.
It depends on vobject library which knows how to parse iCalendar
format. This wrapper was written because vobject library does
not provide easy access protocol to parsed data.

From other side wrapper gives us the hierarchy of the nested
tasks instead of list of tasks as it is represented in iCalendar
data file. After reading, processing, altering KArm data (mainly
tasks) you can dump back KArm data into it's file storage.

At the moment only tasks (todos) are taken into account. Events or
any other KArm (iCalendar) components are not implemented yet.
"""
from vobject import iCalendar, readOne

from utils import prettyTime
from todo import Todo
from errors import *

class DummyProperty(object):
    """For not existing iCalendar attributes
    """
    value = None


class KArm(object):
    """KArm class to work with iCalendar formatted data storage
    """
    
    def __init__(self, file=''):
        """Initialize Karm
        
        If file under given path doesn't exist then we will
        create empty calendar.
        And during dump karm will create a new file.
        """
        self.file = ''
        self._calendar = iCalendar()
        self.todos = {}
    
    def load(self, file=''):
        """Load data from the file
        
        If file is None then use file path set on initialization.
        """
        if file:
            self.file = file
        
        # parse iCalendar format into _calendar vobject
        f = open(self.file, 'r')
        self._calendar = readOne(f.read())
        f.close()
        # actuall load of karm tasks
        self._calendar2Tasks()

    def _calendar2Tasks(self):
        """Loop through the loaded vobject's data and create
        appropriate hierarchy of todos
        """
        todos = {}
        for item in self._calendar.contents.get('vtodo', []):
            related_to = item.contents.get('related-to', [DummyProperty,])[0].value
            todos[related_to] = todos.get(related_to, []) + [item,]
        
        # recursively create hierarchy of tasks
        # starting from the root ones
        for item in todos.get(None, []):
            self._component2Task(self, item, todos)
            
    def _component2Task(self, container, component, data):
        """Create todo and adds it to container together
        with it's children
        """
        # create todo item
        todo = Todo(uid=component.contents['uid'][0].value,
                    summary=component.contents['summary'][0].value)
        if component.contents.get('dtstamp', None) is not None:
            todo.dtstamp = component.contents['dtstamp'][0].value
        if component.contents.get('created', None) is not None:
            todo.created = component.contents['created'][0].value
        if component.contents.get('last-modified', None) is not None:
            todo.last_modified = component.contents['last-modified'][0].value
        if component.contents.get('related-to', None) is not None:
            todo.related_to = component.contents['related-to'][0].value
        if component.contents.get('completed', None) is not None:
            todo.completed = component.contents['completed'][0].value
        if component.contents.get('percent-complete', None) is not None:
            todo.percent_complete = component.contents['percent-complete'][0].value
        if component.contents.get('x-kde-karm-totalsessiontime', None) is not None:
            todo.x_kde_karm_totalsessiontime = component.contents['x-kde-karm-totalsessiontime'][0].value
        if component.contents.get('x-kde-karm-totaltasktime', None) is not None:
            todo.x_kde_karm_totaltasktime = component.contents['x-kde-karm-totaltasktime'][0].value
        if component.contents.get('x-basecamp-type', None) is not None:
            todo.x_basecamp_type = component.contents['x-basecamp-type'][0].value
        
        # add it to container
        todo = container.add(todo)
        
        # now it's time to collect all todo's children
        for item in data.get(todo.uid, []):
            child = self._component2Task(todo, item, data)
        
        return todo

    def dump(self, file=''):
        """Dump data back into KArm storage file
        """
        if file:
            self.file = file
        
        self._tasks2Calendar()
        f = open(self.file, 'w')
        f.write(self._calendar.serialize())
        f.close()

    def _tasks2Calendar(self):
        """Loop through the todos hierarchy and transform them
        to vobject's suitable format
        """
        # TODO: it would be great to have here some smart merging
        # instead of simple purge
        self._calendar = iCalendar()
        for todo in self.todos.values():
            self._task2Component(todo, self._calendar)
    
    def _task2Component(self, todo, calendar):
        """Serialize todo together with it's children back
        to vobject's suitable format
        """
        # firstly create vobject component from karm todo item
        component = calendar.add('vtodo')
        component.add('uid').value = todo.uid
        component.add('summary').value = todo.summary
        if todo.dtstamp is not None:
            component.add('dtstamp').value = todo.dtstamp
        if todo.created is not None:
            component.add('created').value = todo.created
        if todo.last_modified is not None:
            component.add('last-modified').value = todo.last_modified
        if todo.related_to is not None:
            component.add('related-to').value = todo.related_to
        if todo.completed is not None:
            component.add('completed').value = todo.completed
        if todo.percent_complete is not None:
            component.add('percent-complete').value = todo.percent_complete
        if todo.x_kde_karm_totalsessiontime is not None:
            component.add('X-KDE-karm-totalSessionTime').value = todo.x_kde_karm_totalsessiontime
        if todo.x_kde_karm_totaltasktime is not None:
            component.add('X-KDE-karm-totalTaskTime').value = todo.x_kde_karm_totaltasktime
        if todo.x_basecamp_type is not None:
            component.add('X-BASECAMP-type').value = todo.x_basecamp_type
        
        # then add children to it
        for todo in todo.todos.values():
            child = self._task2Component(todo, calendar)
        
        return component

    def reload(self):
        """Reload data merging data from changed file with already
        loaded (and maybe changed) data.
        """

    def add(self, todo):
        """Add a root todo to KArm
        """
        if self.todos.has_key(todo.uid):
            raise DuplicationError, 'There already exists root task with "%s" id' % todo.uid
        self.todos[todo.uid] = todo
        return todo
    
    def delete(self, uid):
        """Delete a root todo from KArm
        """
        if not self.todos.has_key(uid):
            raise NotFoundError, 'Root task with "%s" id not found' % uid
        todo = self.todos[uid]
        del self.todos[uid]
        return todo
    
    def __str__(self):
        """Print hierarchy of tasks
        """
        out = ""
        for todo in self.todos.values():
            out += self._strTask(todo)
        return out.encode('utf-8')
    
    def _strTask(self, todo, indent=""):
        sessionTime = todo.x_kde_karm_totalsessiontime or '0'
        totalTime = todo.x_kde_karm_totaltasktime or '0'
        out = '%s%s [%s] (%s, total:%s)\n' % (indent,
                                              todo.summary,
                                              todo.uid,
                                              prettyTime(int(sessionTime)),
                                              prettyTime(int(totalTime)))
        # loop through the children recursively
        for todo in todo.todos.values():
            out += self._strTask(todo, '%s    ' % indent)
        return out
