VERSION = "0.1.0"

import sublime, sublime_plugin
import os, pipes, subprocess
import re

class BitrixInsertComponentCommand(sublime_plugin.TextCommand):
    
    def run(self, edit, region_start=None, region_end=None, text=None):
        self.edit = edit
        self.bitrix_root = get_bitrix_root(self.view.file_name())
        if self.bitrix_root:
            component_name = self.get_component_name()
            if component_name:
                self.expand_component_name(component_name)        
            else:
                self.quick_select_component()
        else:
            sublime.status_message("You are not in a bitrix web root!")

    def get_component_name(self):
        end_pos = self.view.sel()[0].end()
        line = self.view.substr(self.view.line(end_pos))
        matches = re.search('(?P<name>([a-zA-Z_-]+):([a-zA-Z._-]+))', line)
        if matches:
            return matches.group('name')

    def expand_component_name(self, component_name):       
        start_pos = self.view.sel()[0].begin() - len(component_name)
        region = self.view.find( component_name,  start_pos);
        code = self.generate_include_component(component_name)
        if code:
            self.view.replace(self.edit, region, code)

    def generate_include_component(self, component_name):
        command = 'bxc generate:include --no-ansi --component=' + component_name
        (success, output) = run_cmd(self.bitrix_root, command, True)
        if success:
            return output
        elif output: # Show error message
            sublime.status_message(output)

    def get_components(self):
        command = 'bxc component:list --no-ansi'
        (success, output) = run_cmd(self.bitrix_root, command, True)
        return output.split(os.linesep) if success else []

    def quick_select_component(self):
        self.components = self.get_components()
        if self.components:
            window = self.view.window()
            window.show_quick_panel(self.components, self.on_component_select, sublime.MONOSPACE_FONT)

    def on_component_select(self, index):
        if index > -1:  
            component_name = self.components[index];
            code = self.generate_include_component(component_name) 
            self.view.run_command("bitrix_insert_text", {"text": code})

class BitrixSelectComponentTemplate(sublime_plugin.TextCommand):
    
    def run(self, edit):
        self.bitrix_root = get_bitrix_root(self.view.file_name())
        if self.bitrix_root:
            component_name = self.get_component_name()
            self.templates = self.get_component_templates(component_name)
            if self.templates:
                window = self.view.window();
                window.show_quick_panel(self.templates, self.on_template_select, sublime.MONOSPACE_FONT)
        else:
            sublime.status_message("You are not in a bitrix web root!")      

    def get_component_name(self):
        end_pos = self.view.sel()[0].end()
        line = self.view.substr(self.view.line(end_pos))
        pattern = '\$APPLICATION->IncludeComponent\s*\(\s*[\"\'](?P<name>([a-zA-Z_-]+):([a-zA-Z._-]+))[\"\']\s*,\s*';
        matches = re.search(pattern, line)
        if matches:
            return matches.group('name')

    def get_component_templates(self, component_name):
        command = 'bxc templates:list -s --no-ansi ' + component_name
        (success, output) = run_cmd(self.bitrix_root, command, True)
        if not success:
            sublime_plugin.status_message(output)            
        return output.split(os.linesep) if success else []

    def on_template_select(self, index):
        if index > -1:
            template_name = re.sub('\s*\(.+\)$', '', self.templates[index])
            self.view.run_command("bitrix_insert_text", { "text": template_name })

class BitrixInsertText(sublime_plugin.TextCommand):
    def run(self, edit, text):
        if text:
            self.view.insert(edit, self.view.sel()[0].begin(), text)

def get_bitrix_root(start_path):
    parts = start_path.split(os.sep)
    while parts:
        parts.pop()
        dirname = os.sep.join(parts)
        if os.path.isfile(dirname + "/bitrix/.settings.php"):
            return os.sep.join(parts)

# Thanks to Shell Turtlestein Sublime Plugin by misfo
# https://github.com/misfo/Shell-Turtlestein/blob/master/shell_turtlestein.py#L70
def run_cmd(cwd, cmd, wait, input_str=None):
    shell = isinstance(cmd, str)
    if wait:
        proc = subprocess.Popen(cmd, cwd=cwd,
                                     shell=shell,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     stdin=(subprocess.PIPE if input_str else None))
        encoded_input = None if input_str == None else input_str.encode('utf8')
        output, error = proc.communicate(encoded_input)
        return_code = proc.poll()
        if return_code:
            return (False, None)
        else:
            return (True, output.decode('utf8'))
    else:
        subprocess.Popen(cmd, cwd=cwd, shell=shell)
        return (False, None)            