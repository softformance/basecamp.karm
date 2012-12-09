"""KArm update command

Requires vobject python iCalendar library.

KArm update script.
Requests data from basecamp server and update existing iCalendar
file for using it in KArm utility.

How merging is done:
1. New projects, todos and todo lists are simply added to KArm.
2. Deleted or completed items are only notified, not actually deleted from
   KArm.
3. Updated items are appropriately updated in KArm (summary, content and
   total times).
"""

from basecamp.api import Basecamp

from basecamp.karm import patch
from basecamp.karm import KArm
from basecamp.karm.todo import Todo
from basecamp.karm.utils import prettyTime, bcTime, getSessionTime

from cmdhelper.cmd import Command

class Update(Command):

    description = "KArm update command. Requests data from basecamp " \
                  "server and merges retrieved data with existing " \
                  "iCalendar storage file."

    user_options = [
        ('active-projects', 'a', "fetch only those projects which "
         "have assigned to you todos (default False)"),
        ('update-time', 't', "update todos total time calculated from "
         "all time entries for certain todo item (default False)"),
    ]

    boolean_options = ['active-projects', 'update-time']

    def initialize_options(self):
        self.active_projects = False
        self.update_time = False
    
    def run(self):

        karm = KArm()
        karm.load(self.storage)
        bc = Basecamp(self.url, self.user, self.password)

        # flag that will show at the end whether something has been
        # updated eventually and if we really need to dump new storage
        updated = False

        # update projects
        projects = bc.getProjects()
        todolists = bc.getTodoLists()
        if self.active_projects:
            active_ids = [todolist.project_id for todolist in todolists]
            projects = [project for project in projects
                           if project.id in active_ids]
        
        # firstly update projects
        for project in projects:
            task = karm.todos.get(str(project.id), None)
            if task is None:
                karm.add(Todo(
                    str(project.id),
                    project.name,
                    x_kde_ktimetracker_bctype='project'
                ))
                updated = True
                if self.cmdutil.debug:
                    print "Added project: <%s> [%d]" % (project.name,
                                                        project.id)
            else:
                if task.summary != project.name:
                    task.summary = project.name
                    updated = True
                    if self.cmdutil.debug:
                        print "Updated project: <%s> [%d]" % (project.name,
                                                              project.id)

        # then update todo lists with their todo items
        for todolist in todolists:
            project_id = str(todolist.project_id)
            task = karm.todos[project_id].todos.get(str(todolist.id), None)
            if task is None:
                task = karm.todos[project_id].add(Todo(
                    str(todolist.id),
                    todolist.name,
                    related_to=project_id,
                    x_kde_ktimetracker_bctype='todolist'
                ))
                updated = True
                if self.cmdutil.debug:
                    print "Added todo list to project <%s> [%d]: <%s> [%d]" % (
                        karm.todos[project_id].summary,
                        todolist.project_id,
                        todolist.name,
                        todolist.id
                    )
            else:
                if task.summary != todolist.name:
                    task.summary = todolist.name
                    updated = True
                    if self.cmdutil.debug:
                        print "Updated todo list: <%s> [%d] " \
                              "(project <%s> [%d])" % (
                        todolist.name,
                        todolist.id,
                        karm.todos[project_id].summary,
                        todolist.project_id
                    )
            
            for todo in todolist.todo_items:
                new_todo = False
                subtask = task.todos.get(str(todo.id), None)
                if subtask is None:
                    new_todo = True
                    subtask = task.add(Todo(
                        str(todo.id),
                        todo.content,
                        related_to=task.uid,
                        x_kde_ktimetracker_bctype='todoitem'
                    ))
                    updated = True
                    if self.cmdutil.debug:
                        print "Added todo item <%s> to <%s> [%d] todolist " \
                              "(project <%s> [%d])" % (
                            todo.content,
                            todolist.name,
                            todolist.id,
                            karm.todos[project_id].summary,
                            todolist.project_id
                        )
                else:
                    # TODO: todo.content string should be escaped
                    #       before comparison
                    if subtask.summary != todo.content:
                        subtask.summary = todo.content
                        updated = True
                        if self.cmdutil.debug:
                            print "Updated todoitem #%d " \
                                  "from <%s> todolist [%d] " \
                                  "(<%s> project [%d])" % (
                                todolist.todo_items.index(todo),
                                todolist.name,
                                todolist.id,
                                karm.todos[project_id].summary,
                                todolist.project_id
                            )

                # update todo item's time
                if self.update_time:
                    if subtask.x_kde_ktimetracker_totalsessiontime is None:
                        subtask.x_kde_ktimetracker_totalsessiontime = '0'
                    if subtask.x_kde_ktimetracker_totaltasktime is None:
                        subtask.x_kde_ktimetracker_totaltasktime = '0'
                    sessionMinutes = int(subtask.x_kde_ktimetracker_totalsessiontime)
                    totalMinutes = int(subtask.x_kde_ktimetracker_totaltasktime)
                    
                    # fetch total todo item's time from basecamp
                    hours = 0.0
                    for time_entry in bc.getEntriesForTodoItem(todo.id):
                        hours += float(time_entry.hours)
                        
                    if int(hours * 60.0) != totalMinutes - sessionMinutes:
                        subtask.x_kde_ktimetracker_totaltasktime = str(
                            sessionMinutes + int(hours * 60.0)
                        )
                        updated = True
                        if new_todo and self.cmdutil.debug:
                            print "Added total time to a newly created <%s> " \
                                  "todo item to <%s> todo list [%d] " \
                                  "(project <%s> [%d])" % (
                                todo.content,
                                todolist.name,
                                todolist.id,
                                karm.todos[project_id].summary,
                                todolist.project_id
                            )
                        else:
                            if self.cmdutil.debug:
                                print "Updated todoitem's <%s> total time " \
                                      "(todolist <%s> [%d], " \
                                      "project <%s> [%d])" % (
                                todo.content,
                                todolist.name,
                                todolist.id,
                                karm.todos[project_id].summary,
                                todolist.project_id
                            )

        # dump result if something has changed
        if updated:
            karm.dump()
            if self.cmdutil.debug:
                print "Done..."
        elif self.cmdutil.debug:
                print "Nothing has changed..."
