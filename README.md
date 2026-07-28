# pytools
This repository contains various tools for personal use written in Python:
- [mdheadlist](https://github.com/CyberFicus/pytools#mdheadlist) 
- [OPM](https://github.com/CyberFicus/pytools#opm)

I prioritise simplicity of portability and setup, so I aim to:
- Rely only on Python 3.14.4 standard library
- Have no external dependencies

# mdheadlist
A simple script that integrates with "Shell commands" plugin for Obsidian.md and generates table of contents for the currently open note. Table of contents is a list of obsidian links to headers in the current file, where nested subheaders are indented.

### Setup

1. Go to shell commands plugin settings, create new shell command and write the following (obviously, <path> should be relative to shell commands working directory):
```
# Windows
python <path>\mdheadlist.py {{file_path:absolute}} 
# Unix
python <path>/mdheadlist.py {{file_path:absolute}}
```
2. Name the command, then go to its settings. In output section, choose:
- Output channel for stdout: "Current file: Caret position"
- Output channel for stderr: "Error balloon"
3. Use it the same way as any other shell command in the plugin

# OPM
OPM stands for Obsidian Plugin Manager. It is an interactive CLI tool with a set of commands and a rather niche use case. I have multiple Obsidian.md vaults and in several of them I have the same plugins with the same config, which can be pretty big (e.g. LaTeX Suite plugin). I want to synchronise changes to these configs across vaults, so I do not need to repeat them manually. The simplest solution is to make a directory with all plugins and then place symlinks to it at the ".obsidian/plugins" directory of each vault. But then all plugin configs will be synchronised, and I don't want it. So, the solution is to create separate symlinks for each plugin in each vault. Which is boring and tiresome, and so OPM was born.

### Setup:
1. Gather all your obsidian vaults (or symlinks/junctions to them) in a single directory. Lets call it <obs_dir>
2. Open file "opm.py". At the beginning, you can see config, where you can change the folder for synchronised (OPM calls them uploaded) plugins
3. Close and save the file, then run:
```
python opm.py <obs_dir>
```
4. If any error messages appear, fix the problem and go to step 3
5. Enter "help" and read the help message
6. Use the tool hovewer you like!

### Notes:
- Currently only Windows is supported
- On Windows junctions are used instead of symlinks whenever possible, as their creation requires no admin privileges by default 
