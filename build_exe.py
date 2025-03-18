import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--name=Учет опок',
    '--clean',
    '--add-data=db_init.py;.',
    '--add-data=db_operations.py;.',
    '--add-data=init_repair_dates.py;.',
    '--add-data=opoka_usage_history.json;.',
    '--exclude-module=PyQt5',
    '--exclude-module=PyQt6'
]) 