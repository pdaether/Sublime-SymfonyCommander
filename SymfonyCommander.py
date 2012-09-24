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

    cache_name = 'default'
    routes = {}
    containers = {}
    entities = {}
    templates = {}
    common_snippets = {}

    symfony_api_url = 'http://api.symfony.com/{v}/index.html?q={s}&src=SymfonyCommander'
    symfony_doc_url = 'http://symfony.com/search?version={v}&q={s}&src=SymfonyCommander'

    syntax_list = {"PHP": True, 'HTML': True, 'HTML (Twig)': True, 'XML': True, 'YAML': True}

    valid_scopes = (
            'string.quoted.single.php',
            'string.quoted.double.php',
            'string.quoted.single.twig',
            'string.quoted.single.twig',
            'string.quoted.double.html',
            'string.quoted.single.html',
            'string.quoted.single.xml',
            'string.quoted.double.xml',
            'source.yaml'
    )

    def loadSettings(self):
        self.base_directory = ''
        if self.view:
            project_settings = self.view.settings().get('SymfonyCommander', {})
            if project_settings:
                self.base_directory = project_settings.get('base_directory')
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

            #Init Cache for the Project
            if self.base_directory:
                if self.base_directory not in SymfonyCommanderBase.containers:
                    SymfonyCommanderBase.containers[self.base_directory] = []
                if self.base_directory not in SymfonyCommanderBase.routes:
                    SymfonyCommanderBase.routes[self.base_directory] = []
                if self.base_directory not in SymfonyCommanderBase.entities:
                    SymfonyCommanderBase.entities[self.base_directory] = []
                if self.base_directory not in SymfonyCommanderBase.templates:
                    SymfonyCommanderBase.templates[self.base_directory] = []
                if self.base_directory not in SymfonyCommanderBase.common_snippets:
                    SymfonyCommanderBase.common_snippets[self.base_directory] = []

        s = sublime.load_settings("SymfonyCommander.sublime-settings")
        self.php_command = s.get('php_command')
        if s.get('api_search_version'):
            self.api_search_version = s.get('api_search_version')
        if s.get('doc_search_version'):
            self.doc_search_version = s.get('doc_search_version')

    def getCurrentBundleFolder(self):
        view_name = self.view.file_name()
        bundle_folder = False
        if view_name:
            dir_name = os.path.dirname(view_name)
            found_folder = False
            reached_end = False
            while not found_folder and not reached_end:
                for file in os.listdir(dir_name):
                    if file.endswith('Bundle') and os.path.isdir(dir_name + "/" + file):
                        bundle_folder = dir_name
                        found_folder = True
                #travers up
                old_dir = dir_name
                dir_name = os.path.dirname(dir_name)
                if dir_name == old_dir:
                    reached_end = True
        return bundle_folder

    def callSymfony(self, command, quiet=False):
        self.loadSettings()
        if not self.base_directory:
            if not quiet:
                self.output("Can't find the root directory of the symfony project. Please have a look at the README. You can find it here: https://github.com/pdaether/Sublime-SymfonyCommander")
            return
        os.chdir(self.base_directory)
        # CMD:
        if not self.php_command:
            command = "php app/console --no-ansi " + command
        else:
            command = self.php_command + " app/console --no-ansi " + command
        result, e = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, cwd=self.base_directory).communicate()
        if e:
            return e
        else:
            if not result and not quiet:
                result = "Finished " + command
            return result

    def callPhpunit(self, command):
        self.loadSettings()
        if not self.base_directory:
            self.output("Can't find the root directory of the symfony project. Please have a look at the README. You can find it here: https://github.com/pdaether/Sublime-SymfonyCommander")
            return
        os.chdir(self.base_directory)
        command = "phpunit " + command
        result, e = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, cwd=self.base_directory).communicate()
        if e:
            return e
        else:
            if not result:
                result = "Finished " + command
            return result

    def loadRoutes(self, force=False):
        if not force and len(SymfonyCommanderBase.routes[self.base_directory]) > 0:
            return
        routes_string = self.callSymfony('router:debug', True)
        if not routes_string:
            return
        lines = routes_string.splitlines()
        SymfonyCommanderBase.route_info = []
        SymfonyCommanderBase.routes[self.base_directory] = []
        for idx, val in enumerate(lines):
            if not val.startswith('Name') and not val.startswith('[router]'):
                route_name, restwords = val.split(' ', 1)
                SymfonyCommanderBase.route_info.append([route_name, restwords.strip()])
                SymfonyCommanderBase.routes[self.base_directory].append(route_name)

    def loadContainer(self, force=False):
        if not force and len(SymfonyCommanderBase.containers[self.base_directory]) > 0:
            return
        container_string = self.callSymfony('container:debug', True)
        if not container_string:
            return
        lines = container_string.splitlines()
        SymfonyCommanderBase.container_info = []
        SymfonyCommanderBase.containers[self.base_directory] = []
        for idx, val in enumerate(lines):
            if not val.startswith('Name') and not val.startswith('[container]'):
                container_name, restwords = val.split(' ', 1)
                SymfonyCommanderBase.container_info.append([container_name, restwords.strip()])
                SymfonyCommanderBase.containers[self.base_directory].append(container_name)

    def loadEntities(self, force=False):
        self.loadSettings()
        if not force and len(SymfonyCommanderBase.entities[self.base_directory]) > 0:
            return
        if not self.base_directory:
            return
        SymfonyCommanderBase.entities[self.base_directory] = []
        src_dir = self.base_directory + "/src"
        if not os.path.isdir(src_dir):
            return
        for file in os.listdir(src_dir):
            company_dir = src_dir + "/" + file
            prefix = file
            if os.path.isdir(company_dir):
                for file in os.listdir(company_dir):
                    bundle_dir = company_dir + "/" + file
                    prefix = prefix + file
                    if self.common_snippets[self.base_directory].count(prefix) < 1:
                        self.common_snippets[self.base_directory].append(prefix)
                    if os.path.isdir(bundle_dir):
                        entities_dir = bundle_dir + "/Entity"
                        if os.path.isdir(entities_dir):
                            for file in os.listdir(entities_dir):
                                file_match = re.search(r'^((.)(?!Repository))*\.php$', file)
                                if file_match:
                                    entity_name_match = re.search(r'^(.*)\.php$', file)
                                    SymfonyCommanderBase.entities[self.base_directory].append(entity_name_match.group(1))
                                    SymfonyCommanderBase.entities[self.base_directory].append(prefix + ':' + entity_name_match.group(1))

    def loadTemplates(self, force=False):
        self.loadSettings()
        if not force and len(SymfonyCommanderBase.templates[self.base_directory]) > 0:
            return
        if not self.base_directory:
            return
        SymfonyCommanderBase.templates[self.base_directory] = []
        src_dir = self.base_directory + "/src"
        if not os.path.isdir(src_dir):
            return
        for file in os.listdir(src_dir):
            company_dir = src_dir + "/" + file
            prefix = file
            if os.path.isdir(company_dir):
                for file in os.listdir(company_dir):
                    bundle_dir = company_dir + "/" + file
                    prefix = prefix + file
                    #the short identifier of the bundle:
                    if self.common_snippets[self.base_directory].count(prefix) < 1:
                        self.common_snippets[self.base_directory].append(prefix)
                    if os.path.isdir(bundle_dir):
                        tpl_dir = bundle_dir + "/Resources/views"
                        if os.path.isdir(tpl_dir):
                            results = self.getTemplateNames(tpl_dir, prefix + ':', [])
                            for result in results:
                                SymfonyCommanderBase.templates[self.base_directory].append(result)
                            # for file in os.listdir(tpl_dir):
                            #     file_match = re.search(r'^(.*)\.(twig|php)$', file)
                            #     if file_match:
                            #         SymfonyCommanderBase.templates[self.base_directory].append(file_match.group(0))
                            #         SymfonyCommanderBase.templates[self.base_directory].append(prefix + ':' + file_match.group(0))

    def getTemplateNames(self, dir, prefix, results):
        for file in os.listdir(dir):
            file_match = re.search(r'^(.*)\.(twig|php)$', file)
            if file_match:
                # results.append(file_match.group(0))
                results.append(prefix + ':' + file_match.group(0))
            if os.path.isdir(dir + "/" + file):
                if re.match(r'.*:$', prefix):
                    results = self.getTemplateNames(dir + "/" + file, prefix + file, results)
                else:
                    results = self.getTemplateNames(dir + "/" + file, prefix + '/' + file, results)
        return results

    def clearCache(self):
        SymfonyCommanderBase.containers[self.base_directory] = []
        SymfonyCommanderBase.routes[self.base_directory] = []
        SymfonyCommanderBase.entities[self.base_directory] = []
        SymfonyCommanderBase.templates[self.base_directory] = []
        SymfonyCommanderBase.common_snippets[self.base_directory] = []

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

    def is_enabled(self):
        self.loadSettings()
        return self.base_directory


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

    def is_enabled(self):
        return True


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

    def is_enabled(self):
        filename = self.view.file_name()
        if re.search(r'(.+)[/\\](.+)Controller.php', filename):
            return True
        elif re.search(r'(.+)[/\\](.+).html.twig', filename):
            return True
        else:
            return False


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
        self.loadSettings()
        if not self.base_directory:
            return []
        # check is supported type of file
        syntax, _ = os.path.splitext(os.path.basename(view.settings().get('syntax')))
        syntax = self.syntax_list.get(syntax)
        if syntax == None:
            return []

        # only complete single line/selection
        if len(locations) != 1:
            return []

        # only if in a string contenxt
        scope = view.syntax_name(view.sel()[0].end())

        is_valid_scope = False
        for valid_scope in self.valid_scopes:
            if scope.count(valid_scope):
                is_valid_scope = True
        if not is_valid_scope:
            return []

        # check the content of the actual scope and
        # optimize the completions if needed
        # scope_content = view.substr(view.extract_scope(view.sel()[0].end()))
        current_scope_region = view.extract_scope(view.sel()[0].end())
        scope_context_region = sublime.Region(current_scope_region.begin(), view.sel()[0].end())
        scope_content = view.substr(scope_context_region)
        match_prefix = re.search(r"([\w\.:]*)$", scope_content)
        if match_prefix:
            search_prefix = match_prefix.group(1)
        else:
            search_prefix = False
        self.loadRoutes()
        self.loadContainer()
        self.loadEntities()
        self.loadTemplates()

        snippets = []

        for val in SymfonyCommanderBase.common_snippets[self.base_directory]:
            if val.startswith(prefix):
                snippets.append((val, val))

        for val in SymfonyCommanderBase.routes[self.base_directory]:
            new_snippet = self.checkPrefix(prefix, search_prefix, val, ' [Route]')
            if new_snippet:
                snippets.append(new_snippet)

        for val in SymfonyCommanderBase.containers[self.base_directory]:
            new_snippet = self.checkPrefix(prefix, search_prefix, val, ' [Service]')
            if new_snippet:
                snippets.append(new_snippet)

        for val in SymfonyCommanderBase.entities[self.base_directory]:
            new_snippet = self.checkPrefix(prefix, search_prefix, val, ' [Entity]')
            if new_snippet:
                snippets.append(new_snippet)

        for val in SymfonyCommanderBase.templates[self.base_directory]:
            new_snippet = self.checkPrefix(prefix, search_prefix, val, ' [Tpl]')
            if new_snippet:
                snippets.append(new_snippet)

        return snippets

    def checkPrefix(self, prefix, search_prefix, val, tipstring):
        if search_prefix and search_prefix != prefix:
            if val.startswith(search_prefix):
                if not re.match(r".*[\.\:]$", search_prefix):
                    replace_str = re.sub(r'((.*)[\:\.])(.(?![\:\.]))*$', r'\1', search_prefix)
                    # insert_val = re.sub('[\:\.](.(?![\:\.]))*$', '', val)
                    insert_val = val.replace(replace_str, '', 1)
                else:
                    insert_val = val.replace(search_prefix, '', 1)
                return (val + tipstring, insert_val)
        else:
            if val.startswith(prefix):
                return (val + tipstring, val)
        return False


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

    def is_enabled(self):
        if len(self.view.sel()) > 1:
            return False
        for selection in self.view.sel():
            if selection.empty():
                return False
            else:
                return True


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


class SymfonyCommanderRunTestCommand(sublime_plugin.TextCommand, SymfonyCommanderBase):
    def run(self, edit, path=''):
        self.output(self.callPhpunit(' -c app ' + path))

    def is_enabled(self):
        self.loadSettings()
        return self.base_directory


class SymfonyCommanderRunTestBundleCommand(sublime_plugin.TextCommand, SymfonyCommanderBase):
    def run(self, edit, path=''):
        bundle_folder = self.getCurrentBundleFolder()
        if bundle_folder:
            self.output(self.callPhpunit(' -c app ' + bundle_folder))

    def is_enabled(self):
        self.loadSettings()
        return self.getCurrentBundleFolder()
