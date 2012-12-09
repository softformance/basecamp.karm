#!/data/work/pythons/python-2.4.5/bin/python

"""KTime Todo class

The main data atom in KTime.

Todo schema:

    DTSTAMP:20081206T203902Z
    X-KDE-ktimetracker-bctype:todoitem
    X-KDE-ktimetracker-totalSessionTime:0
    X-KDE-ktimetracker-totalTaskTime:0
    CREATED:20081127T210402Z
    UID:6494365
    LAST-MODIFIED:20081206T203902Z
    SUMMARY:example todo
    RELATED-TO:1018268
    COMPLETED:20081203T232709Z
    PERCENT-COMPLETE:100

"""

from errors import NotFoundError, DuplicationError
from utils import timeStamp2KArm, unescape


class Todo(object):
    """Todo class
    
    Todo Attributes:
        uid - unique id
        dtstamp - date and time stamp
        created - date and time of creation
        last_modified - date and time of last modification
        summary - task name
        related_to - parent task uid or None in case it's root task
        completed - date and time when task was completed
        percent_complete - how many percents of the task is completed
        x_kde_ktimetracker_totalsessiontime - KTime session time of the task
        x_kde_ktimetracker_totaltasktime - KTime time of the task
        x_kde_ktimetracker-bctype - type of task as it's represented in basecamp
                              (project, todolist, todoitem or None)
        
        todos - contained todos
    
    """
    
    def __init__(self, uid, summary, dtstamp=None, created=None,
                 last_modified=None, related_to=None, completed=None,
                 percent_complete=None, x_kde_ktimetracker_totalsessiontime=None,
                 x_kde_ktimetracker_totaltasktime=None, x_kde_ktimetracker_bctype=None):
        self.uid = uid
        self.summary = unescape(summary)
        self.dtstamp = dtstamp
        self.created = created
        self.last_modified = last_modified
        self.related_to = related_to
        self.completed = completed
        self.percent_complete = percent_complete
        self.x_kde_ktimetracker_totalsessiontime = x_kde_ktimetracker_totalsessiontime
        self.x_kde_ktimetracker_totaltasktime = x_kde_ktimetracker_totaltasktime
        self.x_kde_ktimetracker_bctype = x_kde_ktimetracker_bctype

        self.todos = {}
    
    def markAsComplete(self):
        """Mark task as completed
        
        This method set 'completed' datetime attribute and
        set 'percent_complete' attribute to '100' value
        """
        self.completed = timeStamp2KArm()
        self.percent_complete = '100'

    def markAsInComplete(self):
        """Mark task as not completed
        
        This method set 'completed' datetime attribute to None
        and set 'percent_complete' attribute to '0' value
        """
        self.completed = None
        self.percent_complete = '0'
    
    def isCompleted(self):
        """Return whether task is already completed
        """
        return self.completed is not None and self.percent_complete == '100'

    def add(self, todo):
        """Add contained todo
        """
        if self.todos.has_key(todo.uid):
            raise DuplicationError, 'There already exists task with "%s" id in "%s" task' % (todo.uid, self.uid)
        self.todos[todo.uid] = todo
        return todo
    
    def delete(self, uid):
        """Delete contained todo
        """
        if not self.todos.has_key(uid):
            raise NotFoundError, 'Task with "%s" id not found in "%s" task' % (uid, self.uid)
        todo = self.todos[uid]
        del self.todos[uid]
        return todo
