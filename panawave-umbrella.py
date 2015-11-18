from tkinter import Tk
from time import sleep
import os
import sys
# Debugging console
from IPython import embed

from pwinterface import PanawaveApp


def pw_json_serializer(object):
    '''generic method for representing objects in json. will use an
    object's _as_json method if found.'''
    try :
        return object._as_json()
    except (NameError, AttributeError):
        return object.__dict__

if __name__ == "__main__":
    print("initializing Panawave Umbrella Editor...")
    master = Tk()
    global our_app
    our_app = PanawaveApp(master)

