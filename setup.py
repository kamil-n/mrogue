import sys
from cx_Freeze import setup, Executable
from mrogue import __version__

files = ['terminal10x16_gs_ro.png', 'Bmac_smooth_16x24.png', 'Cooz_curses_14x16.png', 'Kyzsmooth.png']
buildOptions = dict(packages=[], excludes=[], include_files=files, build_exe=f'MRogue_{__version__}_{sys.platform}')
base = 'Win32GUI' if sys.platform == 'win32' else None
executables = [Executable('rogue.py', base=base, targetName='MRogue')]

# execute with >>\path\to\python.exe setup.py build<<

setup(name='mrogue',
      version=__version__,
      description='MRogue',
      options=dict(build_exe=buildOptions),
      executables=executables, requires=['numpy', 'tcod'])
