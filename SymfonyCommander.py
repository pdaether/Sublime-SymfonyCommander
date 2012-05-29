# MIT License**
#
# Copyright (c) 2012 Patrick Daether, public < at > pd-digital.de
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import os
import os.path
import subprocess
import sublime
import sublime_plugin
import re
import webbrowser

# Some global vars:
jump_to_action = ''


class SymfonyCommanderBase:

    base_directory = ''
    api_search_version = 'master'  # or somthing like v2.0.14 ...
    doc_search_version = 'master'  # or  2.0

    routes = []
    containers = []

    symfony_api_url = 'http://api.symfony.com/{v}/index.html?q={s}&src=SymfonyCommander'
    symfony_doc_url = 'http://symfony.com/search?version={v}&q={s}&src=SymfonyCommander'

    def loadSettings(self):
        if self.view:
            project_settings = self.view.settings().get('SymfonyCommander', {})
            if project_settings:
                self.base_directory = project_settings.get('base_directory')

        s = sublime.load_settings("SymfonyCommander.sublime-settings")
        self.php_command = s.get('php_command')
        if s.get('api_search_version'):
            self.api_search_version = s.get('api_search_version')
        if s.get('doc_search_version'):
            self.doc_search_version = s.get('doc_search_version')

    def callSymfony(self, command, quiet=False):
        self.loadSettings()
        if not self.base_directory:
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
                                self.base_directory = dir_name
                                found_root = True
                    #travers up
                    old_dir = dir_name
                    dir_name = os.path.dirname(dir_name)
                    if dir_name == old_dir:
                        reached_end = True
        if not self.base_directory:
            if not quiet:
                self.output("Can't find the root directory of the symfony project. Please have a look at the README. You can find it here: https://github.com/pdaether/Sublime-SymfonyCommander")
            return
        os.chdir(self.base_directory)
        # CMD:
        if not self.php_command:
            command = "app/console " + command
        else:
            command = self.php_command + " app/console " + command
        result, e = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, cwd=self.base_directory).communicate()
        if e:
            return e
        else:
            if not result and not quiet:
                result = "Finished " + command
            return result

    def loadRoutes(self, force=False):
        if not force and len(SymfonyCommanderBase.routes) > 0:
            return
        routes_string = self.callSymfony('router:debug', True)
        if not routes_string:
            return
        lines = routes_string.splitlines()
        SymfonyCommanderBase.route_info = []
        SymfonyCommanderBase.routes = []
        for idx, val in enumerate(lines):
            if not val.startswith('Name') and not val.startswith('[router]'):
                route_name, restwords = val.split(' ', 1)
                SymfonyCommanderBase.route_info.append([route_name, restwords.strip()])
                SymfonyCommanderBase.routes.append(route_name)

    def loadContainer(self, force=False):
        if not force and len(SymfonyCommanderBase.containers) > 0:
            return
        container_string = self.callSymfony('container:debug', True)
        if not container_string:
            return
        lines = container_string.splitlines()
        SymfonyCommanderBase.container_info = []
        SymfonyCommanderBase.containers = []
        for idx, val in enumerate(lines):
            if not val.startswith('Name') and not val.startswith('[container]'):
                container_name, restwords = val.split(' ', 1)
                SymfonyCommanderBase.container_info.append([container_name, restwords.strip()])
                SymfonyCommanderBase.containers.append(container_name)

    def clearCache(self):
        SymfonyCommanderBase.containers = []
        SymfonyCommanderBase.routes = []

    def output(self, value):
        self.multi_line_output(value)

    def multi_line_output(self, value, panel_name='SymfonyCommander'):
        # Create the output Panel
        panel = self.view.window().get_output_panel(panel_name)
        panel.set_read_only(False)
        panel.set_syntax_file('Packages/Text/Plain text.tmLanguage')
        edit = panel.begin_edit()
        panel.insert(edit, panel.size(), value)
        panel.end_edit(edit)
        panel.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output." + panel_name})

    def open_url(self, url):
        url = url.replace(' ', '%20')
        webbrowser.open_new_tab(url)

    def getApiUrl(self, text):
        self.loadSettings()
        return self.symfony_api_url.format(v=self.api_search_version, s=text)

    def getDocumentationUrl(self, text):
        self.loadSettings()
        return self.symfony_doc_url.format(v=self.doc_search_version, s=text)


class SymfonyCommander(SymfonyCommanderBase, sublime_plugin.TextCommand):

    def injectText(self, edit, text):
        for r in self.view.sel():
            if r.size() > 0:
                self.view.replace(edit, r, text)
            else:
                self.view.insert(edit, r.begin(), text)


class SymfonyCommanderClearCacheCommand(SymfonyCommander):
    def run(self, edit):
        self.clearCache()


class SymfonyCommanderExecuteCommand(SymfonyCommander):
    def run(self, edit, command):
        result = self.callSymfony(command)
        if result:
            self.output(result)


class SymfonyCommanderExecuteArgumentsCommand(SymfonyCommander):
    def run(self, edit, command, arguments):
        self.command = command
        sublime.active_window().show_input_panel("Arguments", arguments, self.on_input, None, None)

    def on_input(self, message):
        result = self.callSymfony(self.command + ' ' + message)
        if result:
            self.output(result)


# Command to run with arguments
class SymfonyCommanderAsseticDumpArgumentsCommand(SymfonyCommander):
    def run(self, edit):
        sublime.active_window().show_input_panel("Arguments", "--env=dev --no-debug --watch --force --period=30", self.on_input, None, None)

    def on_input(self, message):
        self.output(self.callSymfony('assetic:dump ' + message))


class SymfonyCommanderSelectRouteCommand(SymfonyCommander, sublime_plugin.WindowCommand):
    def run(self, edit):

        self.loadRoutes()

        def on_select_route(num):
            if num != -1:
                route_name = SymfonyCommanderBase.route_info[num][0]
                self.injectText(edit, route_name)

        self.view.window().show_quick_panel(SymfonyCommanderBase.route_info, on_select_route, sublime.MONOSPACE_FONT)


class SymfonyCommanderSelectContainerCommand(SymfonyCommander, sublime_plugin.WindowCommand):
    def run(self, edit):

        self.loadContainer()

        def on_select_container(num):
            if num != -1:
                container_name = SymfonyCommanderBase.container_info[num][0]
                self.injectText(edit, container_name)

        self.view.window().show_quick_panel(SymfonyCommanderBase.container_info, on_select_container, sublime.MONOSPACE_FONT)


class SymfonyCommanderSwitchFileCommand(SymfonyCommander, sublime_plugin.TextCommand):
    def run(self, edit):
        global jump_to_action
        file = self.view.file_name()
        file_match = re.search(r'(.+)[/\\](.+)Controller.php', file)
        if file_match:
            folder = file_match.group(1)
            file = file_match.group(2)
            action = self.get_current_function(self.view)
            if action:
                a = re.search('(\w+)Action', action).group(1)
                self.view.window().open_file(folder + os.sep + '..' + os.sep + 'Resources' + os.sep + 'views' + os.sep + file + os.sep + a + '.html.twig')
        elif re.search(r'(.+)[/\\](.+).html.twig', file):
            file_match = re.search(r'(.+)[/\\](.+)[/\\](.+).html.twig', file)
            folder = file_match.group(1)
            controller = file_match.group(2)
            action = file_match.group(3)
            self.view.window().open_file(folder + os.sep + '..' + os.sep + '..' + os.sep + 'Controller' + os.sep + controller + 'Controller.php')
            jump_to_action = action
        else:
            sublime.status_message('Cannot find the correct file, sorry!' + file)

    def get_current_function(self, view):
        sel = view.sel()[0]
        functionRegs = view.find_by_selector('entity.name.function')
        cf = None
        for r in reversed(functionRegs):
            if r.a < sel.a:
                cf = view.substr(r)
                break
        return cf


class SymfonyEvent(sublime_plugin.EventListener, SymfonyCommanderBase):
    def on_load(self, view):
        global jump_to_action
        if jump_to_action:
            sel = view.find(jump_to_action + "Action", 0)
            view.show(sel)
            jump_to_action = ''


class SymfonyCommanderAutocomplete(sublime_plugin.EventListener, SymfonyCommanderBase):

    def on_query_completions(self, view, prefix, locations):
        self.view = view

        # only complete single line/selection
        if len(locations) != 1:
            return []

        self.loadRoutes()
        self.loadContainer()

        snippets = []

        for val in SymfonyCommanderBase.routes:
            snippets.append((val, val))

        for val in SymfonyCommanderBase.containers:
            snippets.append((val, val))

        return snippets


class SymfonyCommanderSearchSelectionCommand(sublime_plugin.TextCommand, SymfonyCommanderBase):
    def run(self, edit, source='api'):

        if len(self.view.sel()) > 1:
            return

        for selection in self.view.sel():
            if selection.empty():
                text = self.view.word(selection)

            text = self.view.substr(selection)

            if source == 'api':
                url = self.getApiUrl(text)
            else:
                url = self.getDocumentationUrl(text)

            self.open_url(url)


class SymfonyCommanderSearchInputCommand(sublime_plugin.WindowCommand, SymfonyCommanderBase):

    source = 'api'

    def run(self, source='api'):
        self.view = self.window.active_view()
        self.source = source
        if source == 'api':
            title = 'Search Symfony API for'
        else:
            title = 'Search Symfony Documentation for'

        self.window.show_input_panel(title, '',
            self.on_done, self.on_change, self.on_cancel)

    def on_done(self, text):
        if self.source == 'api':
            url = self.getApiUrl(text)
        else:
            url = self.getDocumentationUrl(text)
        self.open_url(url)

    def on_change(self, input):
        pass

    def on_cancel(self):
        pass
