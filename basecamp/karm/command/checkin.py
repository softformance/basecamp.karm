"""KArm checkin command

Requires vobject python iCalendar library.

Create time entries at basecamp's account in cases:
    1. ToDo item has more than 0 minutes logged by itself
       You will be able to comment such time entries during the check in as
       prompt
    2. ToDo item has nested todos with non-zero session time,
       all of these nested todos are treated as a seperate time entries,
       their content will be send together with time entries as their's
       comments
    3. ToDo item which is a straight child of a project and has no special
       basecamp type it will be logged as a time entry for the project with
       it's content as a time entry comment
    4. Something else? Not yet ;)

"""

import time

from basecamp.api import Basecamp

from basecamp.karm import patch
from basecamp.karm import KArm
from basecamp.karm.utils import prettyTime, bcTime, getSessionTime

from cmdhelper.cmd import Command
from cmdhelper.errors import CMDHelperArgError

class CheckIn(Command):

    description = "KArm checkin command. Takes session time from " \
                  "your KArm tasks and logs them into basecamp " \
                  "account as time entries."

    user_options = [
        ('date=', 'd', "date to use for each time entry "
         "(date format: year-mm-dd, e.g. '2009-02-14')"),
    ]
    
    def initialize_options(self):
        self.date = None

    def finalize_options(self):
        super(CheckIn, self).finalize_options()
        # check format of the entered date
        if self.date is not None:
            self.checkDate(self.date)
    
    def checkDate(self, date):
        """Raise error in case date is not in format: year-mm-dd
        
        e.g. 2009-02-14
        """
        try:
            time.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise CMDHelperArgError, "Date format is invalid, should be: " \
                "year-mm-dd, e.g. '2009-02-14'"

    def getUserId(self, bc):
        person = bc.getAuthenticatedPerson()
        if person is not None:
            return person.id
        else:
            raise Exception, "Could not retrieve logged in person"

    def run(self):

        karm = KArm()
        karm.load(self.storage)
        bc = Basecamp(self.url, self.user, self.password)
            
        userId = self.getUserId(bc)

        updated = False
        # now let's go through the collected data
        # and decide what to do with each entry
        for project_id, project in karm.todos.items():
            if project.x_basecamp_type != 'project':
                continue
            
            if self.cmdutil.debug:
                print 'Processing project: <%s> [%s]... ' % (
                    project.summary, project_id)
            pSessionTime = getSessionTime(project)
            if pSessionTime is not None:
                # log time for project, aka create time entry for project
                summary = raw_input("    Please, enter time entry (%s) "
                                    "description for project "
                                    "(<Enter> to skip comment): " %
                                    prettyTime(pSessionTime))
                entry = bc.createTimeEntryForProject(
                    int(project_id),
                    bcTime(pSessionTime),
                    date=self.date,
                    person_id=userId,
                    description=summary
                )
                if self.cmdutil.debug:
                    print "    Add time to project: (%s)" % \
                        bcTime(pSessionTime)
                # update karm file
                project.x_kde_karm_totalsessiontime = '0'
                updated = True
                if self.cmdutil.debug:
                    print "    Reset project's session time to 0"
                    
            # now loop through the project's todo lists
            for list_id, todolist in project.todos.items():
                if todolist.x_basecamp_type == 'todolist':
                    # go deeper to find todos
                    for todo_id, todo in todolist.todos.items():
                        if todo.x_basecamp_type != 'todoitem':
                            # create todo in basecamp
                            todo_id = str(bc.createTodoItem(
                                int(list_id),
                                content=todo.summary,
                                notify=True
                            ).id)
                            todolist.delete(todo.uid)
                            todo.uid = todo_id
                            todolist.add(todo)
                            todo.x_basecamp_type = 'todoitem'
                            updated = True
                        
                        # check for todos time entry
                        pSessionTime = getSessionTime(todo)
                        if pSessionTime is not None:
                            # log time for todo item
                            summary = raw_input(
                                "    Please, enter time entry (%s) "
                                "description for todo item <%s> "
                                "(<Enter> to skip comment): " %
                                (prettyTime(pSessionTime), todo.summary)
                            )
                            entry = bc.createTimeEntryForTodoItem(
                                int(todo_id),
                                bcTime(pSessionTime),
                                date=self.date,
                                person_id=userId,
                                description=summary
                            )
                            if self.cmdutil.debug:
                                print "    Added time for todo item <%s>: " \
                                      "(%s)" % (bcTime(pSessionTime),
                                                todo.summary)
                            # update karm file
                            todo.x_kde_karm_totalsessiontime = '0'
                            updated = True
                            if self.cmdutil.debug:
                                print "    Reset todo's session time to 0"
                        
                        # then check whether todo has more time entries inside
                        for entry_id, entry in todo.todos.items():
                            # log time if such exists
                            pSessionTime = getSessionTime(entry)
                            if pSessionTime is not None:
                                # log time for todo item
                                summary = entry.summary
                                dummy = bc.createTimeEntryForTodoItem(
                                    int(todo_id),
                                    bcTime(pSessionTime),
                                    date=self.date,
                                    person_id=userId,
                                    description=summary
                                )
                                if self.cmdutil.debug:
                                    print "    Added time for todo item " \
                                          "<%s>: (%s)" % (
                                        bcTime(pSessionTime),
                                        todo.summary
                                    )
                                # update karm file
                                entry.x_kde_karm_totalsessiontime = '0'
                                updated = True
                                
                            # delete time entry if it is checked
                            if entry.isCompleted():
                                todo.delete(entry_id)
                                updated = True
                        
                        # delete todo itself if it is checked as done
                        if todo.isCompleted() and not todo.todos:
                            # check todo item as done in basecamp
                            if bc.completeTodoItem(int(todo_id)) and \
                               self.cmdutil.debug:
                                    print "    Checked as done todo item " \
                                          "[%s]:" % todo_id
                            todolist.delete(todo_id)
                            updated = True
                            if self.cmdutil.debug:
                                print "    Deleted todo item " \
                                      "<%s>" % todo.summary
                else:
                    # possibly we've got time entry for project
                    # with entry comment as todo body
                    pSessionTime = getSessionTime(todolist)
                    if pSessionTime is not None:
                        # log time for project
                        summary = todolist.summary
                        entry = bc.createTimeEntryForProject(
                            int(project_id),
                            bcTime(pSessionTime),
                            date=self.date,
                            person_id=userId,
                            description=summary
                        )
                        if self.cmdutil.debug:
                            print "    Added time for project: (%s)" % \
                                bcTime(pSessionTime)
                        # update karm file
                        todolist.x_kde_karm_totalsessiontime = '0'
                        updated = True

                # after logging time delete such kind of todo
                # in case it is checked as done
                if todolist.isCompleted() and not todolist.todos:
                    project.delete(list_id)
                    updated = True
                    if self.cmdutil.debug:
                        print "    Deleted list [%s]" % list_id
            
            # check whether project has any lists
            # if not then delete this project from karm
            if project.isCompleted() and not project.todos:
                karm.delete(project_id)
                updated = True
                if self.cmdutil.debug:
                    print "    Deleted project [%s]" % project_id

        # dump karm storage if something has changed
        if updated:
            karm.dump()
            if self.cmdutil.debug:
                print "Done..."
        elif self.cmdutil.debug:
            print "Nothing has changed..."
