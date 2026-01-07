import sys, inspect
sys.path.insert(0, 'c:/djc/dj-course/M1/azor-chatdog-py/src')
from ui import session_picker
print('PICK_SESSION_OK')
print('sig:', inspect.signature(session_picker.pick_session))
