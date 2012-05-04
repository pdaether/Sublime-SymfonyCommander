# SymfonyCommander

**_Integration of the Symfony 2 console right into Sublime Text 2_**

This [Sublime Text 2](http://sublimetext.com/) package integrates the most common [Symfony 2](http://www.symfony.com) console commands right into your _lovely editor of choice &trade;_.

It provides the following features:

- Clear the cache
- Warmup an empty cache
- Assetic: Dump all assets to the filesystem
- Install bundles web assets under the public web directory
- Display current routes for an application
- Displays current services for an application
- Send emails from the spool
- Doctrine: Clear result cache
- Doctrine: Clear query cache
- Doctrine: Clear meta cache

More commands are on the way.
If you want to be informed about new versions of this plugin just watch this repro on github or watch out for some [tweets](https://twitter.com/#!/pdaether).

If you need some Symfony code snippets in addition to this package just install [sublime-symfony2](https://github.com/raulfraile/sublime-symfony2). It is a great package for speed up your Symfony 2 development as well.

## Usage

### Command palette

![Command Palette](http://pdaether.github.com/images/command_palette.jpg "Command Palette")

Open the Command Palette with the shortcut `Command+Shift+P` on OS X or `Control+Shift+P` otherwise.
Alternative you can open the Command Palette in the menu (_Tools -> Command Palette..._).

**Speedup tip:**

You don't need to type the complete command (`SymfonyCommander...`) in the Command Palette to get to to the right command.
For example if you type something short like `sccl` you get directly to the _SymfonyCommander cache:clear_ commands.

### Call the Symfony commands through the contextmenu of an file.

![Contextmenu](http://pdaether.github.com/images/contextmenu.jpg "Contextmenu")


## Install

### Installation with Package Control (recommended)

1. The easiest way to install SymfonyCommander is through Package Control, which can be found [here](http://wbond.net/sublime_packages/package_control).

2. After the installation of Package Control bring up the Command Palette (`Command+Shift+P` on OS X, `Control+Shift+P` otherwise). Select "Package Control: Install Package" and wait until the list with all available packages will appear. 

3. Than select "SymfonyCommander". 

Package Control will automatically keep SymfonyCommander up to date with the latest version.


### Installation with git

Clone this repository in your Sublime Packages directory which you can find here:

- OS X : `~/Library/Application Support/Sublime Text 2/Packages/`
- Linux: `~/.Sublime Text 2/Packages/`
- Windows: `%APPDATA%/Sublime Text 2/Packages/`

## Configuration

### Global settings

Settings can be configured with a `SymfonyCommander.sublime-settings` file in your `User` folder.
You can copy the one provided in this package.

	{
		"php_command": "/usr/bin/php"
	}

With `php_command` you can define where SymfonyCommander can find the php binary. If it is `false` than SymfonyCommader calls the Symfony console directly without php binary (works well on OS X an Linux).
Otherwise you can point `php_command` to the php binary path, for example `C:\php\php.exe` or `/usr/bin/php`.
The default is `false`.


### Project specific settings

SymfonyCommander tries to find the Symfony `app/console` script automatically. Therefor SymfonyCommander takes the active file an traverses the directory path up and searches for `app/console`.
This works in most cases.

Otherwise you have to tell SymfonyCommander where to find the console script on a project basis.
To point SymfonyCommander to the root directory of your Symfony installation you need to set this path in the Sublime Text Project file (_*.sublime-project_) under the _settings_-section.

	"settings":{
		"SymfonyCommander":{
			"base_directory": "/www/htdocs/your-symfony-project/"
		}
	}


## License

**MIT License**


Copyright (c) 2012 Patrick Daether, public < at > pd-digital.de

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

