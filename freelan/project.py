"""Project related classes and functions."""

import os
import sys
import fnmatch

import file_tools
import tools

class Project(object):
    """A class to handle projects."""

    def __init__(self, name, libraries, path=None):
        """Create a new Project reading from the specified path."""

        super(Project, self).__init__()

        self.name = name
        self.libraries = libraries

        if path is None:
            self.abspath = os.getcwd()
        else:
            self.abspath = os.path.normpath(os.path.join(os.getcwd(), path))

        if not hasattr(os, 'related'):
            if not self.abspath.startswith(os.getcwd()):
                raise ValueError('Invalid path: ' + self.abspath)
            self.path = self.abspath[len(os.getcwd()):] or '.'
        else:
            self.path = os.path.relpath(self.abspath)

class LibraryProject(Project):
    """A class to handle library projects."""

    def __init__(self, name, major, minor, libraries, path=None, include_path=None, source_path=None):
        """Create a new LibraryProject reading from the specified path."""

        super(LibraryProject, self).__init__(name, libraries, path)

        self.major = major
        self.minor = minor

        if include_path is None:
            self.include_path = os.path.join(self.path, 'include', self.name)
        else:
            self.include_path = include_path

        if source_path is None:
            self.source_path = os.path.join(self.path, 'src')
        else:
            self.source_path = source_path

        # Scan for include files
        self.include_files = []

        for root, directories, files in os.walk(self.include_path):
            self.include_files += [os.path.join(root, file) for file in file_tools.filter(files, ['*.h', '*.hpp'])]

        # Scan for source files
        self.source_files = []

        for root, directories, files in os.walk(self.source_path):
            self.source_files += [os.path.join(root, file) for file in file_tools.filter(files, ['*.c', '*.cpp'])]

    def configure_environment(self, env):
        """Configure the given environment for building the current project."""

        _env = {
            'CPPPATH': [self.include_path],
            'LIBS': self.libraries
        }

        libraries = env.FreelanLibrary(
            os.path.join(self.path, env.libdir),
            self.name,
            self.major,
            self.minor,
            self.source_files,
            **_env
        )

        libraries_install = env.Install(os.path.join(env['ARGUMENTS']['prefix'], env.libdir), libraries)

        for include_file in self.include_files:
            libraries_install += env.Install(os.path.dirname(os.path.join(env['ARGUMENTS']['prefix'], include_file)), include_file)

        documentation = env.Doxygen('doxyfile')
        env.AlwaysBuild(documentation)
        indentation = env.AStyle(self.source_files + self.include_files)
        env.AlwaysBuild(indentation)

        env.Alias('build', libraries)
        env.Alias('install', libraries_install)
        env.Alias('doc', documentation)
        env.Alias('indent', indentation)

        env.Default('build')

        return libraries + libraries_install + documentation + indentation

    def Sample(self, libraries, path=None):
        """Build a sample project at the given path, or in the current directory if no path is specified."""

        if path is None:
            name = os.path.basename(os.path.abspath(os.getcwd()))
        else:
            name = os.path.basename(os.path.abspath(path))

        return SampleProject(self, name, libraries, path)

class SampleProject(Project):
    """A class to handle samples."""

    def __init__(self, parent_project, name, libraries, path=None, source_files=None):
        """Create a new sample project."""

        if not parent_project.name in libraries:
            libraries.insert(0, parent_project.name)

        super(SampleProject, self).__init__(name, libraries, path)

        self.parent_project = parent_project

        # Scan for source files
        if source_files is None:
            self.source_files = []

            for root, directories, files in os.walk(self.path):
                self.source_files += [os.path.join(root, file) for file in file_tools.filter(files, ['*.c', '*.cpp'])]
        else:
            self.source_files = source_files

    def configure_environment(self, env):
        """Configure the given environment for building the current project."""

        _env = {
            'CPPPATH': [self.path, os.path.join(self.parent_project.abspath, 'include')],
            'LIBPATH': [self.path, os.path.join(self.parent_project.abspath, env.libdir)],
            'LIBS': self.libraries
        }

        sample = env.FreelanProgram(
            self.path,
            self.name,
            self.source_files,
            **_env
        )

        return sample

