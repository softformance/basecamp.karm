"""KArm checkout command

Requires vobject python iCalendar library.

Requests data from basecamp server and create appropriate iCalendar
file for using it in KArm utility.

Previous KArm configuration won't be taken into account. It will be
only backed up.
"""

from basecamp.api import Basecamp

from basecamp.karm import patch
from basecamp.karm import KArm
from basecamp.karm.todo import Todo

from cmdhelper.cmd import Command

class CheckOut(Command):

    description = "KArm checkout command. Requests data from basecamp " \
                  "server and create appropriate iCalendar file for " \
                  "using it in KArm utility."

    user_options = [
        ('active-projects', 'a', "fetch only those projects which "
         "have assigned to you todos (default False)"),
        ('fetch-time', 't', "fetch todos total time calculated from "
         "all time entries for certain todo item (default False)"),
    ]
    
    boolean_options = ['active-projects', 'fetch-time']

    def initialize_options(self):
        self.active_projects = False
        self.fetch_time = False
    
    def run(self):
        karm = KArm()
        bc = Basecamp(self.url, self.user, self.password)
        counter = 0

        # add projects as todo items to karm
        projects = bc.getProjects()
        todolists = bc.getTodoLists()
        if self.active_projects:
            active_ids = [todolist.project_id for todolist in todolists]
            projects = [project for project in projects
                           if project.id in active_ids]
        for project in projects:
            karm.add(Todo(
                str(project.id),
                project.name,
                x_basecamp_type='project'
            ))
            if self.cmdutil.debug:
                print "Added project: <%s>" % project.name

        # add todolists with their todo items to karm
        for todolist in todolists:
            project_id = str(todolist.project_id)
            task = karm.todos[project_id].add(Todo(
                str(todolist.id),
                todolist.name,
                related_to=project_id,
                x_basecamp_type='todolist'
            ))
            if self.cmdutil.debug:
                print "    Added todo list: <%s>" % todolist.name
            
            # add todo items eventually
            for todo in todolist.todo_items:
                hours = 0.0
                if self.fetch_time:
                    for time_entry in bc.getEntriesForTodoItem(todo.id):
                        hours += float(time_entry.hours)
                task.add(Todo(
                    str(todo.id),
                    todo.content,
                    related_to=str(todolist.id),
                    x_basecamp_type='todoitem',
                    x_kde_karm_totaltasktime=str(int(hours * 60.0))
                ))
                if self.cmdutil.debug:
                    print "        Added todo item: <%s>" % todo.content
                counter += 1

        # dump result
        karm.dump(self.storage)
        if self.cmdutil.debug:
            print 'Added %d todo items...' % counter
            print 'Done...'
