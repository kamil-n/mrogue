import sys
from cx_Freeze import setup, Executable
from modules import __version__

files = ['item_templates.json', 'monster_templates.json', 'terminal10x16_gs_ro.png']
buildOptions = dict(packages=[], excludes=[], include_files=files)
base = 'Win32GUI' if sys.platform == 'win32' else None
executables = [Executable('__main__.py', base=base, targetName='MRogue')]

# execute with >>\path\to\python.exe setup.py build<<

setup(name='mrogue',
      version=__version__,
      description='MRogue',
      options=dict(build_exe=buildOptions),
      executables=executables, requires=['numpy', 'tcod'])
