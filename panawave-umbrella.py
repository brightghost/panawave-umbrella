from tkinter import Tk
from time import sleep
import os
import sys
# Debugging console
from IPython import embed

from pwinterface import PanawaveApp
import pwlogging
import logging as log


def pw_json_serializer(object):
    '''generic method for representing objects in json. will use an
    object's _as_json method if found.'''
    try :
        return object._as_json()
    except (NameError, AttributeError):
        return object.__dict__

def tracefunc(frame, event, arg, indent=[0]):
    '''Debugging function which can be attached to all function calls.
    http://stackoverflow.com/a/8315566
    '''
    if event == "call":
        indent[0] += 2
        print("-" * indent[0] + "> call function", frame.f_code.co_name)
    elif event == "return":
        print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
        indent[0] -= 2
    return tracefunc

if __name__ == "__main__":
    # configure logging
    pwlogging.create_logger(level=log.DEBUG)
    log.info("initializing Panawave Umbrella Editor...")
    profile = False
    if profile == True:
        sys.setprofile(tracefunc)
    master = Tk()
    # global our_app
    our_app = PanawaveApp(master)

