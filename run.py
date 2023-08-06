import os
import sys
print(sys.argv)
one = "" if len(sys.argv) <= 1 else sys.argv[1]
os.system(f'cmd /k "E:/Workspace/evenv10/Scripts/python.exe "{__file__[:-6]+"main.py"}" "{one}""')
