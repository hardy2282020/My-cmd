import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import sys
import xml.etree.ElementTree as ET
import hashlib
import base64
from datetime import datetime
import json

class VFSNode:
    def __init__(self, name, is_file=False, content=None):
        self.name = name
        self.is_file = is_file
        self.content = content if content else ""
        self.children = {}
        self.parent = None

class VFS:
    def __init__(self):
        self.root = VFSNode("")
        self.current_dir = self.root
        self.name = "default_vfs"
    
    def load_from_xml(self, xml_content):
        try:
            root = ET.fromstring(xml_content)
            self.name = root.get('name', 'default_vfs')
            self.root = self._parse_xml_node(root)
            self.current_dir = self.root
            return True
        except Exception as e:
            return False
    
    def _parse_xml_node(self, xml_node):
        node_name = xml_node.get('name', '')
        is_file = xml_node.get('type', 'dir') == 'file'
        
        node = VFSNode(node_name, is_file)
        
        if is_file:
            content_elem = xml_node.find('content')
            if content_elem is not None and content_elem.text:
                # Декодируем base64 если нужно
                if content_elem.get('encoding') == 'base64':
                    node.content = base64.b64decode(content_elem.text).decode('utf-8')
                else:
                    node.content = content_elem.text
        else:
            for child in xml_node:
                if child.tag == 'node':
                    child_node = self._parse_xml_node(child)
                    child_node.parent = node
                    node.children[child_node.name] = child_node
        
        return node
    
    def get_path(self, node=None):
        if node is None:
            node = self.current_dir
        
        path_parts = []
        current = node
        while current and current.name:
            path_parts.insert(0, current.name)
            current = current.parent
        
        return '/' + '/'.join(path_parts) if path_parts else '/'
    
    def change_directory(self, path):
        if path == '/':
            self.current_dir = self.root
            return True
        
        if path.startswith('/'):
            target_dir = self.root
            path_parts = path[1:].split('/')
        else:
            target_dir = self.current_dir
            path_parts = path.split('/')
        
        for part in path_parts:
            if part == '..':
                if target_dir.parent:
                    target_dir = target_dir.parent
            elif part == '.':
                continue
            elif part in target_dir.children and not target_dir.children[part].is_file:
                target_dir = target_dir.children[part]
            else:
                return False
        
        self.current_dir = target_dir
        return True
    
    def list_directory(self, path=None):
        if path is None:
            target_dir = self.current_dir
        else:
            # Для простоты, ищем директорию по пути
            if path.startswith('/'):
                target_dir = self.root
                path_parts = path[1:].split('/')
            else:
                target_dir = self.current_dir
                path_parts = path.split('/')
            
            for part in path_parts:
                if part and part in target_dir.children and not target_dir.children[part].is_file:
                    target_dir = target_dir.children[part]
                else:
                    return []
        
        return [name for name in target_dir.children.keys()]

class ShellEmulator:
    def __init__(self):
        self.vfs = VFS()
        self.commands = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit,
            'clear': self.cmd_clear,
            'find': self.cmd_find,
            'pwd': self.cmd_pwd,
            'vfs-info': self.cmd_vfs_info,
            'help': self.cmd_help,
            'chmod': self.cmd_chmod
        }
        
        # Создаем VFS по умолчанию
        self.create_default_vfs()
    
    def create_default_vfs(self):
        # Создаем простую структуру по умолчанию
        self.vfs = VFS()
        self.vfs.name = "default_vfs"
        
        # Создаем несколько директорий и файлов
        home_dir = VFSNode("home", False)
        home_dir.parent = self.vfs.root
        self.vfs.root.children["home"] = home_dir
        
        user_dir = VFSNode("user", False)
        user_dir.parent = home_dir
        home_dir.children["user"] = user_dir
        
        file1 = VFSNode("readme.txt", True, "Welcome to Shell Emulator!")
        file1.parent = user_dir
        user_dir.children["readme.txt"] = file1
        
        file2 = VFSNode("config.txt", True, "Default configuration")
        file2.parent = user_dir
        user_dir.children["config.txt"] = file2
        
        etc_dir = VFSNode("etc", False)
        etc_dir.parent = self.vfs.root
        self.vfs.root.children["etc"] = etc_dir
        
        self.vfs.current_dir = user_dir
    
    def load_vfs_from_xml(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            new_vfs = VFS()
            if new_vfs.load_from_xml(xml_content):
                self.vfs = new_vfs
                return True
            return False
        except Exception as e:
            return False
    
    def calculate_vfs_hash(self):
        # Простой хеш на основе структуры VFS
        data = self._serialize_vfs_structure(self.vfs.root)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _serialize_vfs_structure(self, node):
        result = node.name + ("(file)" if node.is_file else "(dir)")
        if node.is_file:
            result += f"[{node.content}]"
        else:
            for child in node.children.values():
                result += self._serialize_vfs_structure(child)
        return result
    
    def execute_command(self, command_line):
        parts = command_line.strip().split()
        if not parts:
            return ""
        
        command = parts[0]
        args = parts[1:]
        
        if command in self.commands:
            try:
                return self.commands[command](args)
            except Exception as e:
                return f"Error executing command {command}: {str(e)}"
        else:
            return f"Unknown command: {command}"
    
    def cmd_ls(self, args):
        path = args[0] if args else None
        items = self.vfs.list_directory(path)
        return "\n".join(items) if items else ""
    
    def cmd_cd(self, args):
        if not args:
            return "cd: missing argument"
        
        path = args[0]
        if self.vfs.change_directory(path):
            return ""
        else:
            return f"cd: {path}: No such file or directory"
    
    def cmd_exit(self, args):
        return "EXIT"
    
    def cmd_clear(self, args):
        return "CLEAR"
    
    def cmd_find(self, args):
        if not args:
            return "find: missing pattern"
        
        pattern = args[0]
        results = []
        self._find_in_vfs(self.vfs.current_dir, pattern, results, "")
        return "\n".join(results) if results else f"No files found matching '{pattern}'"
    
    def _find_in_vfs(self, node, pattern, results, current_path):
        current_path = current_path + "/" + node.name if current_path else node.name
        
        if pattern.lower() in node.name.lower():
            results.append(current_path)
        
        if not node.is_file:
            for child in node.children.values():
                self._find_in_vfs(child, pattern, results, current_path)
    
    def cmd_pwd(self, args):
        return self.vfs.get_path()
    
    def cmd_vfs_info(self, args):
        vfs_hash = self.calculate_vfs_hash()
        return f"VFS Name: {self.vfs.name}\nSHA-256 Hash: {vfs_hash}"
    
    def cmd_help(self, args):
        help_text = "Available commands:\n"
        for cmd in self.commands:
            help_text += f"  {cmd}\n"
        return help_text
    
    def cmd_chmod(self, args):
        if len(args) < 2:
            return "Usage: chmod <mode> <file>"
        
        # В этой эмуляции просто возвращаем сообщение об успехе
        return f"Changed permissions of {args[1]} to {args[0]}"

class ShellGUI:
    def __init__(self, root):
        self.root = root
        self.shell = ShellEmulator()
        self.setup_gui()
        
        # Показываем приветственное сообщение
        self.output_text.insert(tk.END, "Shell Emulator started. Type 'help' for available commands.\n")
        self.output_text.insert(tk.END, f"Current directory: {self.shell.vfs.get_path()}\n")
        self.output_text.insert(tk.END, "-> ")
        self.output_text.see(tk.END)
    
    def setup_gui(self):
        self.root.title("Shell Emulator")
        self.root.geometry("800x600")
        
        # Создаем текстовое поле для вывода
        self.output_text = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            width=80, 
            height=30,
            font=("Courier", 10)
        )
        self.output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Создаем поле ввода
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(input_frame, text="Command:").pack(side=tk.LEFT)
        self.input_entry = tk.Entry(input_frame, width=70, font=("Courier", 10))
        self.input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.input_entry.bind('<Return>', self.execute_command)
        
        # Кнопка выполнения команды
        tk.Button(input_frame, text="Execute", command=self.execute_command).pack(side=tk.LEFT, padx=5)
        
        # Фокус на поле ввода
        self.input_entry.focus()
    
    def execute_command(self, event=None):
        command = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)
        
        if not command:
            return
        
        # Добавляем команду в вывод
        self.output_text.insert(tk.END, f"{command}\n")
        
        # Выполняем команду
        result = self.shell.execute_command(command)
        
        # Обрабатываем специальные команды
        if result == "EXIT":
            self.root.quit()
            return
        elif result == "CLEAR":
            self.output_text.delete(1.0, tk.END)
        else:
            if result:
                self.output_text.insert(tk.END, f"{result}\n")
        
        # Показываем текущую директорию
        self.output_text.insert(tk.END, f"Current directory: {self.shell.vfs.get_path()}\n")
        self.output_text.insert(tk.END, "-> ")
        self.output_text.see(tk.END)

def main():
    # Парсим аргументы командной строки
    vfs_path = None
    startup_script = None
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-vfs' and i + 1 < len(sys.argv):
            vfs_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '-script' and i + 1 < len(sys.argv):
            startup_script = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    root = tk.Tk()
    app = ShellGUI(root)
    
    # Загружаем VFS если указан путь
    if vfs_path:
        shell = app.shell
        if shell.load_vfs_from_xml(vfs_path):
            app.output_text.insert(tk.END, f"Loaded VFS from: {vfs_path}\n")
            app.output_text.insert(tk.END, f"VFS Name: {shell.vfs.name}\n")
        else:
            app.output_text.insert(tk.END, f"Failed to load VFS from: {vfs_path}\n")
    
    # Выполняем стартовый скрипт если указан
    if startup_script:
        try:
            with open(startup_script, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Эмулируем ввод команды
                        app.input_entry.insert(0, line)
                        app.execute_command()
        except Exception as e:
            app.output_text.insert(tk.END, f"Error executing startup script: {str(e)}\n")
    
    app.output_text.see(tk.END)
    root.mainloop()

if __name__ == "__main__":
    main()
    