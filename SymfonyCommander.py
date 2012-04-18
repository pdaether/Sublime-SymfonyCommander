import os
import os.path
import subprocess
import sublime
import sublime_plugin


class SymfonyCommander(sublime_plugin.TextCommand):
    def callSymfony(self, command):
        project_settings = self.view.settings().get('SymfonyCommander', {})
        base_directory = ""
        if project_settings:
            base_directory = project_settings.get('base_directory')
        if not base_directory:
            #try to find it somewhere upwards:
            view_name = self.view.file_name()
            if view_name:
                dir_name = os.path.dirname(view_name)
                found_root = False
                reached_end = False
                while not found_root and not reached_end:
                    for file in os.listdir(dir_name):
                        if file == "app" and os.path.isdir(dir_name + "/" + file):
                            #found an app dir
                            if os.path.exists(dir_name + "/" + file + '/console'):
                                base_directory = dir_name
                                found_root = True
                    #travers up
                    old_dir = dir_name
                    dir_name = os.path.dirname(dir_name)
                    if dir_name == old_dir:
                        reached_end = True
        if not base_directory:
            self.output("Can't find the root directory of the symfony project. Please have a look at the README. You can find it here: https://github.com/pdaether/Sublime-SymfonyCommander")
            return
        os.chdir(base_directory)
        # CMD:
        s = sublime.load_settings("SymfonyCommander.sublime-settings")
        php_command = s.get('php_command')
        if not php_command:
            command = "app/console " + command
        else:
            command = php_command + " app/console " + command
        result, e = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, cwd=base_directory).communicate()
        if e:
            self.output(e)
        else:
            if not result:
                result = "Finished " + command
            self.output(result)

    def output(self, value):
        self.multi_line_output(value)

    def multi_line_output(self, value, panel_name='SymfonyCommander'):
        # Create the output Panel and start edit
        panel = self.view.window().get_output_panel(panel_name)
        panel.set_read_only(False)
        panel.set_syntax_file('Packages/Text/Plain text.tmLanguage')
        edit = panel.begin_edit()
        panel.insert(edit, panel.size(), value)
        panel.end_edit(edit)
        panel.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output." + panel_name})


# Clear Cache
class SymfonyCommanderClearCacheCommand(SymfonyCommander):
    def run(self, edit):
        self.callSymfony('cache:clear')


class SymfonyCommanderClearCacheProdCommand(SymfonyCommander):
    def run(self, edit):
        self.callSymfony('cache:clear --env=prod')


class SymfonyCommanderClearCacheDevCommand(SymfonyCommander):
    def run(self, edit):
        self.callSymfony('cache:clear --env=dev')


class SymfonyCommanderCacheWarmupCommand(SymfonyCommander):
    def run(self, edit):
        self.callSymfony('cache:warmup')


class SymfonyCommanderRouterDebugCommand(SymfonyCommander):
    def run(self, edit):
        self.callSymfony('router:debug')


class SymfonyCommanderAssetsInstallCommand(SymfonyCommander):
    def run(self, edit):
        self.callSymfony('assets:install web')


class SymfonyCommanderAssetsInstallSymlinksCommand(SymfonyCommander):
    def run(self, edit):
        self.callSymfony('assets:install --symlink web')


class SymfonyCommanderSendMailCommand(SymfonyCommander):
    def run(self, edit):
        self.callSymfony('swiftmailer:spool:send')


# Command to run node with arguments
class SymfonyCommanderSendMailArgumentsCommand(SymfonyCommander):
    def run(self, edit):
        sublime.active_window().show_input_panel("Arguments", "--message-limit=10 --time-limit=10", self.on_input, None, None)

    def on_input(self, message):
        command = message.split()
        command.insert(0, self.view.file_name())
        command.insert(0, 'node')
        self.callSymfony('swiftmailer:spool:send ' + message)


# Command to run node with arguments
class SymfonyCommanderAsseticDumpArgumentsCommand(SymfonyCommander):
    def run(self, edit):
        sublime.active_window().show_input_panel("Arguments", "--env=dev --no-debug --watch --force --period=30", self.on_input, None, None)

    def on_input(self, message):
        command = message.split()
        command.insert(0, self.view.file_name())
        command.insert(0, 'node')
        self.callSymfony('assetic:dump ' + message)
