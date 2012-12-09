"""Utility functions like date and time formatting, etc.

"""
import time
import re

def timeStamp2KArm(timestamp=None):
    """Format timestamp to suitable for KArm date and time format
    
    Return RFC2445 format: YYYYMMDDTHHMMSSZ
    """
    if timestamp is None:
        timestamp = time.time()
    return time.strftime('%Y%m%dT%H%M%SZ', time.localtime(timestamp))

def unescape(pattern):
    """Unescape all non-alphanumeric characters in pattern.
    
    Oposite to re.escape function.
    """
    return re.sub(r'\\(\W)', r'\1', pattern)

def prettyTime(time):
    hours, minutes = divmod(time, 60)
    return '%02d:%02d' % (hours, minutes)

def bcTime(time):
    return '%.2f' % round(time / 60.0, 2)

def getSessionTime(todo):
    sessionTime = todo.x_kde_ktimetracker_totalsessiontime
    if sessionTime is not None:
        sessionTime = int(sessionTime)
        if sessionTime > 0:
            return sessionTime
    return None
