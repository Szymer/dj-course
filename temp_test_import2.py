import sys, inspect
sys.path.insert(0, 'c:/djc/dj-course/M1/azor-chatdog-py/src')
from files import session_files
from ui import session_picker
print('SESSION_LIST_FN', hasattr(session_files, 'list_sessions'))
print('PICK_FN', hasattr(session_picker, 'pick_session'))
print('PICK_SIG', inspect.signature(session_picker.pick_session))
