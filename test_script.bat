# Тестирование с параметрами по умолчанию
python shell_emulator.py

# Тестирование с VFS
python shell_emulator.py -vfs example_vfs.xml

# Тестирование со стартовым скриптом
python shell_emulator.py -script startup_script.txt

# Тестирование с обоими параметрами
python shell_emulator.py -vfs example_vfs.xml -script startup_script.txt