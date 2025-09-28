#!/usr/bin/env python3
"""
Эмулятор командной строки ОС - Вариант 9
Этап 2: Конфигурация с графическим интерфейсом (tkinter)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import getpass
import socket
import argparse
import subprocess
import sys

class ConfigurableGUIShellEmulator:
    def __init__(self, root, vfs_path=None, startup_script=None, custom_prompt=None):
        self.root = root
        self.running = True
        self.username = getpass.getuser()
        self.hostname = socket.gethostname()
        
        # Параметры конфигурации
        self.vfs_path = vfs_path
        self.startup_script = startup_script
        self.custom_prompt = custom_prompt
        
        # Настройка главного окна
        self.setup_window()
        
        self.commands = {
            'ls': self.stub_ls,
            'cd': self.stub_cd,
            'exit': self.exit_shell,
            'help': self.show_help,
            'conf-dump': self.show_config
        }
        
        self.setup_ui()
        self.show_debug_info()
        self.show_welcome_message()
        
        # Автоматически запустить стартовый скрипт если указан
        if self.startup_script:
            self.root.after(1000, self.run_startup_script)
    
    def setup_window(self):
        """Настройка главного окна"""
        title = f"Эмулятор - [{self.username}@{self.hostname}]"
        if self.vfs_path:
            title += f" | VFS: {os.path.basename(self.vfs_path)}"
        self.root.title(title)
        self.root.geometry("900x700")
        self.root.configure(bg='#2b2b2b')
        
        # Создаем меню
        self.setup_menu()
    
    def setup_menu(self):
        """Настройка меню приложения"""
        menubar = tk.Menu(self.root)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новый сеанс", command=self.new_session)
        file_menu.add_separator()
        file_menu.add_command(label="Загрузить стартовый скрипт", command=self.load_startup_script)
        file_menu.add_command(label="Установить путь VFS", command=self.set_vfs_path)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        # Меню Настройки
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Показать конфигурацию", command=self.show_config_dialog)
        config_menu.add_command(label="Изменить приглашение", command=self.change_prompt)
        menubar.add_cascade(label="Настройки", menu=config_menu)
        
        # Меню Тестирование
        test_menu = tk.Menu(menubar, tearoff=0)
        test_menu.add_command(label="Создать тестовые скрипты", command=self.create_test_scripts)
        test_menu.add_command(label="Запустить тесты", command=self.run_tests)
        menubar.add_cascade(label="Тестирование", menu=test_menu)
        
        self.root.config(menu=menubar)
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Панель статуса (показывает текущую конфигурацию)
        self.setup_status_bar(main_frame)
        
        # Текстовая область для вывода
        self.output_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white',
            font=('Consolas', 10)
        )
        self.output_area.pack(fill=tk.BOTH, expand=True, pady=(10, 10))
        self.output_area.config(state=tk.DISABLED)
        
        # Фрейм для ввода команды
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)
        
        # Приглашение к вводу
        prompt_text = self.custom_prompt if self.custom_prompt else f"{self.username}@{self.hostname}:~$ "
        self.prompt_label = ttk.Label(
            input_frame,
            text=prompt_text,
            foreground='#00ff00',
            background='#2b2b2b',
            font=('Consolas', 10, 'bold')
        )
        self.prompt_label.pack(side=tk.LEFT)
        
        # Поле ввода команды
        self.command_entry = ttk.Entry(
            input_frame,
            width=60,
            font=('Consolas', 10)
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.command_entry.bind('<Return>', self.execute_command_event)
        self.command_entry.focus()
        
        # Кнопка выполнения
        self.execute_button = ttk.Button(
            input_frame,
            text="Выполнить",
            command=self.execute_command
        )
        self.execute_button.pack(side=tk.RIGHT)
        
        # Панель инструментов
        self.setup_toolbar(main_frame)
    
    def setup_status_bar(self, parent):
        """Настройка панели статуса"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_text = "Конфигурация: "
        if self.vfs_path:
            status_text += f"VFS: {os.path.basename(self.vfs_path)} | "
        if self.startup_script:
            status_text += f"Скрипт: {os.path.basename(self.startup_script)} | "
        if self.custom_prompt:
            status_text += f"Приглашение: {self.custom_prompt}"
        
        if status_text == "Конфигурация: ":
            status_text += "по умолчанию"
        
        self.status_label = ttk.Label(
            status_frame,
            text=status_text,
            foreground='#ffa500',
            background='#2b2b2b',
            font=('Consolas', 9)
        )
        self.status_label.pack()
    
    def setup_toolbar(self, parent):
        """Настройка панели инструментов"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(toolbar, text="Очистить", command=self.clear_screen).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Конфигурация", command=self.show_config_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Загрузить скрипт", command=self.load_startup_script).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Тесты", command=self.run_tests).pack(side=tk.LEFT)
    
    def show_debug_info(self):
        """Отладочный вывод всех параметров"""
        debug_text = """
---------------------------------------------------------------
|                   ОТЛАДОЧНАЯ ИНФОРМАЦИЯ                     |
---------------------------------------------------------------

"""
        self.print_output(debug_text, 'system')
        
        config_info = f"""Параметры конфигурации:
• Путь к VFS: {self.vfs_path or 'Не указан'}
• Стартовый скрипт: {self.startup_script or 'Не указан'}
• Пользовательское приглашение: {self.custom_prompt or 'Не указано'}

"""
        self.print_output(config_info, 'system')
        self.print_output("=" * 60 + "\n\n", 'system')
    
    def show_welcome_message(self):
        """Показать приветственное сообщение"""
        welcome_text = f"""
---------------------------------------------------------------
|                 Эмулятор командной строки ОС                |
|                         Вариант №9                          |
|                  Этап 2: Конфигурация (GUI)                 |
---------------------------------------------------------------

Доступные команды: 1s, cd, help, conf-dump, exit
Используйте меню для управления конфигурацией

"""
        self.print_output(welcome_text, 'system')
    
    def print_output(self, text, text_type='normal'):
        """Вывод текста в текстовую область"""
        self.output_area.config(state=tk.NORMAL)
        
        colors = {
            'normal': '#ffffff',
            'error': '#ff6b6b',
            'success': '#00ff00',
            'system': '#4ec9b0',
            'command': '#569cd6',
            'debug': '#ce9178'
        }
        
        self.output_area.insert(tk.END, text, text_type)
        self.output_area.tag_config(text_type, foreground=colors.get(text_type, '#ffffff'))
        
        self.output_area.see(tk.END)
        self.output_area.config(state=tk.DISABLED)
    
    def parse_input(self, user_input):
        """Простой парсер, разделяющий ввод на команду и аргументы по пробелам"""
        parts = user_input.strip().split()
        if not parts:
            return None, []
        command = parts[0]
        args = parts[1:]
        return command, args
    
    def stub_ls(self, args):
        """Заглушка для команды ls"""
        self.print_output(f"Команда: ls, Аргументы: {args}\n\n", 'command')
        return True
    
    def stub_cd(self, args):
        """Заглушка для команды cd"""
        self.print_output(f"Команда: cd, Аргументы: {args}\n\n", 'command')
        return True
    
    def show_help(self, args):
        """Показать справку по командам"""
        help_text = """
Доступные команды:

  1s [аргументы]    - Заглушка команды ls
  cd [аргументы]    - Заглушка команды cd
  conf-dump         - Показать текущую конфигурацию
  help              - Показать эту справку
  exit              - Выйти из эмулятора

Графические функции:
• Меню 'Файл' - управление сеансами и скриптами
• Меню 'Настройки' - управление конфигурацией
• Меню 'Тестирование' - создание и запуск тестов

"""
        self.print_output(help_text, 'system')
        return True
    
    def show_config(self, args):
        """Команда conf-dump - показать конфигурацию"""
        config_text = f"""
Текущая конфигурация:
────────────────────
• Путь к VFS: {self.vfs_path or 'Не указан'}
• Стартовый скрипт: {self.startup_script or 'Не указан'}
• Пользовательское приглашение: {self.custom_prompt or 'По умолчанию'}
• Пользователь: {self.username}
• Хост: {self.hostname}

"""
        self.print_output(config_text, 'system')
        return True
    
    def exit_shell(self, args):
        """Команда exit - завершает работу эмулятора"""
        self.print_output("Выход из эмулятора...\n", 'system')
        self.running = False
        self.root.after(1000, self.root.destroy)
        return True
    
    def execute_command(self, event=None):
        """Выполнение команды с обработкой ошибок"""
        user_input = self.command_entry.get().strip()
        if not user_input:
            return
        
        prompt_text = self.custom_prompt if self.custom_prompt else f"{self.username}@{self.hostname}:~$ "
        self.print_output(f"{prompt_text}{user_input}\n", 'normal')
        
        command, args = self.parse_input(user_input)
        self.command_entry.delete(0, tk.END)
        
        if command is None:
            return
        
        if command not in self.commands:
            self.print_output(f"Ошибка: неизвестная команда '{command}'\n\n", 'error')
            return False
        
        try:
            success = self.commands[command](args)
            if not success:
                self.print_output(f"Ошибка выполнения команды '{command}'\n\n", 'error')
        except Exception as e:
            self.print_output(f"Ошибка выполнения команды '{command}': {e}\n\n", 'error')
    
    def execute_command_event(self, event):
        """Обработчик события для выполнения команды по Enter"""
        self.execute_command()
    
    def clear_screen(self):
        """Очистка экрана"""
        self.output_area.config(state=tk.NORMAL)
        self.output_area.delete(1.0, tk.END)
        self.output_area.config(state=tk.DISABLED)
        self.show_debug_info()
        self.show_welcome_message()
    
    def new_session(self):
        """Создать новый сеанс"""
        self.clear_screen()
        self.print_output("Новый сеанс создан.\n\n", 'success')
    
    def load_startup_script(self):
        """Загрузить стартовый скрипт"""
        filename = filedialog.askopenfilename(
            title="Выберите стартовый скрипт",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            self.startup_script = filename
            self.update_status()
            self.print_output(f"Загружен стартовый скрипт: {filename}\n", 'success')
            self.run_startup_script()
    
    def set_vfs_path(self):
        """Установить путь VFS"""
        path = filedialog.askdirectory(title="Выберите папку VFS")
        if path:
            self.vfs_path = path
            self.update_status()
            self.print_output(f"Установлен путь VFS: {path}\n", 'success')
    
    def change_prompt(self):
        """Изменить приглашение к вводу"""
        new_prompt = tk.simpledialog.askstring(
            "Изменение приглашения",
            "Введите новое приглашение:",
            initialvalue=self.custom_prompt or f"{self.username}@{self.hostname}:~$"
        )
        if new_prompt:
            self.custom_prompt = new_prompt
            self.prompt_label.config(text=new_prompt + " ")
            self.update_status()
            self.print_output(f"Приглашение изменено на: {new_prompt}\n", 'success')
    
    def show_config_dialog(self):
        """Показать диалог конфигурации"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Конфигурация эмулятора")
        config_window.geometry("500x300")
        config_window.transient(self.root)
        config_window.grab_set()
        
        ttk.Label(config_window, text="Текущая конфигурация", font=('Arial', 12, 'bold')).pack(pady=10)
        
        config_text = f"""Путь к VFS: {self.vfs_path or 'Не указан'}
Стартовый скрипт: {self.startup_script or 'Не указан'}
Пользовательское приглашение: {self.custom_prompt or 'По умолчанию'}
Пользователь: {self.username}
Хост: {self.hostname}"""
        
        text_widget = scrolledtext.ScrolledText(config_window, width=60, height=10)
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, config_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(config_window, text="Закрыть", command=config_window.destroy).pack(pady=10)
    
    def update_status(self):
        """Обновить панель статуса"""
        status_text = "Конфигурация: "
        if self.vfs_path:
            status_text += f"VFS: {os.path.basename(self.vfs_path)} | "
        if self.startup_script:
            status_text += f"Скрипт: {os.path.basename(self.startup_script)} | "
        if self.custom_prompt:
            status_text += f"Приглашение: {self.custom_prompt}"
        
        if status_text == "Конфигурация: ":
            status_text += "по умолчанию"
        
        self.status_label.config(text=status_text)
    
    def run_startup_script(self):
        """Выполнение стартового скрипта с остановкой при первой ошибке"""
        if not self.startup_script or not os.path.exists(self.startup_script):
            self.print_output("ОШИБКА: Стартовый скрипт не найден\n", 'error')
            return False
        
        self.print_output(f"\n=== Выполнение стартового скрипта: {self.startup_script} ===\n", 'system')
        
        try:
            with open(self.startup_script, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                self.print_output(f"[{line_num}] {line}\n", 'debug')
                command, args = self.parse_input(line)
                
                if command is None:
                    continue
                
                if command not in self.commands:
                    self.print_output(f"ОШИБКА: Неизвестная команда '{command}' в строке {line_num}\n", 'error')
                    self.print_output("ПРЕРЫВАНИЕ: Остановка выполнения скрипта\n", 'error')
                    return False
                
                success = self.commands[command](args)
                if not success:
                    self.print_output(f"ОШИБКА: Сбой выполнения команды в строке {line_num}\n", 'error')
                    self.print_output("ПРЕРЫВАНИЕ: Остановка выполнения скрипта\n", 'error')
                    return False
            
            self.print_output("=== Стартовый скрипт выполнен успешно ===\n\n", 'success')
            return True
            
        except Exception as e:
            self.print_output(f"ОШИБКА при выполнении стартового скрипта: {e}\n", 'error')
            return False
    
    def create_test_scripts(self):
        """Создание тестовых скриптов"""
        scripts = {
            'test_gui_basic.txt': """# Базовый тест для GUI
1s
cd /home
1s -la
help
conf-dump
""",
            
            'test_gui_advanced.txt': """# Продвинутый тест для GUI
1s /var/log
cd /etc
1s -l
cd /nonexistent
1s
conf-dump
help
"""
        }
        
        for filename, content in scripts.items():
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            self.print_output(f"Создан тестовый скрипт: {filename}\n", 'success')
        
        self.print_output("Тестовые скрипты созданы. Используйте 'Загрузить скрипт' для тестирования.\n", 'system')
    
    def run_tests(self):
        """Запуск тестов"""
        test_window = tk.Toplevel(self.root)
        test_window.title("Запуск тестов")
        test_window.geometry("400x200")
        
        ttk.Label(test_window, text="Выберите тест для запуска", font=('Arial', 12, 'bold')).pack(pady=10)
        
        def run_basic_test():
            self.startup_script = 'test_gui_basic.txt'
            self.update_status()
            self.run_startup_script()
            test_window.destroy()
        
        def run_advanced_test():
            self.startup_script = 'test_gui_advanced.txt'
            self.update_status()
            self.run_startup_script()
            test_window.destroy()
        
        ttk.Button(test_window, text="Базовый тест", command=run_basic_test).pack(pady=5)
        ttk.Button(test_window, text="Продвинутый тест", command=run_advanced_test).pack(pady=5)
        ttk.Button(test_window, text="Отмена", command=test_window.destroy).pack(pady=10)
    
    def run(self):
        """Запуск главного цикла"""
        self.root.mainloop()

def create_demo_scripts():
    """Создание демонстрационных скриптов при первом запуске"""
    scripts = {
        'demo_startup.txt': """# Демонстрационный стартовый скрипт для GUI эмулятора
1s
cd /home/user
1s -la
cd /etc
1s
conf-dump
help
# Следующая команда должна вызвать ошибку
cd nonexistent_directory
1s
exit
"""
    }
    
    for filename, content in scripts.items():
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Создан демонстрационный скрипт: {filename}")

def main():
    # Создаем демонстрационные скрипты
    create_demo_scripts()
    
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description='GUI Эмулятор командной строки ОС - Вариант 9')
    parser.add_argument('--vfs-path', help='Путь к физическому расположению VFS')
    parser.add_argument('--startup-script', help='Путь к стартовому скрипту')
    parser.add_argument('--custom-prompt', help='Пользовательское приглашение к вводу')
    
    args = parser.parse_args()
    
    # Проверяем существование стартового скрипта
    if args.startup_script and not os.path.exists(args.startup_script):
        print(f"Ошибка: стартовый скрипт не найден: {args.startup_script}")
        args.startup_script = None
    
    # Создаем и запускаем GUI
    root = tk.Tk()
    emulator = ConfigurableGUIShellEmulator(
        root,
        vfs_path=args.vfs_path,
        startup_script=args.startup_script,
        custom_prompt=args.custom_prompt
    )
    emulator.run()

if __name__ == "__main__":
    main()