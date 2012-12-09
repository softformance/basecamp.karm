#!/usr/bin/env python
"""KArm command line utility

Depends on cmdhelper package.
Loads karm.commands entry points to retrieve available commmands.
"""

from cmdhelper import CMDHelper

class KArmUtility(CMDHelper):
    """KArmUtility class
    
    All the hard work is performed by CMDHelper and karm commands not
    by KArm utility itself ;-)
    """

    global_options = [
        ('url=', 'U', "an url to basecamp account"),
        ('user=', 'u', "a user name for basecamp authentication"),
        ('password=', 'p', "a password for the given user name"),
        ('storage=', 's', "a path to karm storage file"),
        ('debug', 'd', "print about what is going on during execution"),
    ] + CMDHelper.global_options
    
    required_options = ['url', 'user', 'password', 'storage']
    
    def __init__(self, *args, **kw):
        super(KArmUtility, self).__init__(*args, **kw)
        
        # karm's global options
        self.url = None
        self.user = None
        self.password = None
        self.storage = None
        self.debug = True


def main():
    app = KArmUtility(entry_point='karm.commands')
    app.run()

if __name__ == '__main__':
    main()
