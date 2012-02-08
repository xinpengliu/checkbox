#!/usr/bin/env python

import os
import re
import errno
import posixpath
from glob import glob

from distutils.core import setup
from distutils.util import change_root, convert_path

from distutils.ccompiler import new_compiler
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.command.install_scripts import install_scripts
from DistUtilsExtra.command.build_extra import build_extra
from DistUtilsExtra.command.build_i18n import build_i18n
from DistUtilsExtra.command.build_icons import build_icons


def changelog_version(changelog="debian/changelog"):
    version = "dev"
    if posixpath.exists(changelog):
        head=open(changelog).readline()
        match = re.compile(".*\((.*)\).*").match(head)
        if match:
            version = match.group(1)

    return version

def expand_data_files(data_files):
    for f in data_files:
        if type(f) != str:
            files = f[1]
            i = 0
            while i < len(files):
                if files[i].find("*") > -1:
                    for e in glob(files[i]):
                        files.append(e)
                    files.pop(i)
                    i -= 1
                i += 1

    return data_files

def extract_sources_from_data_files(data_files):
    all_sources = []
    data_files = expand_data_files(data_files)
    for destination, sources in data_files:
        all_sources.extend([s for s in sources if s.endswith(".c")])

    return all_sources

def extract_executables_from_data_files(data_files):
    sources = extract_sources_from_data_files(data_files)
    return [os.path.splitext(s)[0] for s in sources]

def substitute_variables(infile, outfile, variables={}):
    file_in = open(infile, "r")
    file_out = open(outfile, "w")
    for line in file_in.readlines():
        for key, value in variables.items():
            line = line.replace(key, value)
        file_out.write(line)


class checkbox_build(build_extra, object):

    def initialize_options(self):
        super(checkbox_build, self).initialize_options()

        self.sources = []

    def finalize_options(self):
        super(checkbox_build, self).finalize_options()

        # Initialize sources
        data_files = self.distribution.data_files
        self.sources = extract_sources_from_data_files(data_files)

    def run(self):
        super(checkbox_build, self).run()

        cc = new_compiler()
        for source in self.sources:
            executable = os.path.splitext(source)[0]
            cc.link_executable([source], executable, libraries=["rt", "pthread"])


class checkbox_clean(clean, object):

    def initialize_options(self):
        super(checkbox_clean, self).initialize_options()

        self.executables = None

    def finalize_options(self):
        super(checkbox_clean, self).finalize_options()

        # Initialize sources
        data_files = self.distribution.data_files
        self.executables = extract_executables_from_data_files(data_files)

    def run(self):
        super(checkbox_clean, self).run()

        for executable in self.executables:
            try:
                os.unlink(executable)
            except OSError, error:
                if error.errno != errno.ENOENT:
                    raise


# Hack to workaround unsupported option in Python << 2.5
class checkbox_install(install, object):

    user_options = install.user_options + [
        ('install-layout=', None,
         "installation layout to choose (known values: deb)")]

    def initialize_options(self):
        super(checkbox_install, self).initialize_options()

        self.install_layout = None


class checkbox_install_data(install_data, object):

    def finalize_options(self):
        """Add wildcard support for filenames."""
        super(checkbox_install_data, self).finalize_options()

        for f in self.data_files:
            if type(f) != str:
                files = f[1]
                i = 0
                while i < len(files):
                    if "*" in files[i]:
                        for e in glob(files[i]):
                            files.append(e)
                        files.pop(i)
                        i -= 1
                    i += 1

    def run(self):
        """Run substitutions on files."""
        super(checkbox_install_data, self).run()

        examplesfiles = [o for o in self.outfiles if "examples" in o]
        if not examplesfiles:
            return

        # Create etc directory
        etcdir = convert_path("/etc/checkbox.d")
        if not posixpath.isabs(etcdir):
            etcdir = posixpath.join(self.install_dir, etcdir)
        elif self.root:
            etcdir = change_root(self.root, etcdir)
        self.mkpath(etcdir)

        # Create configs symbolic link
        dstdir = posixpath.dirname(examplesfiles[0]).replace("examples",
            "configs")
        if not os.path.exists(dstdir):
            os.symlink(etcdir, dstdir)

        # Substitute version in examplesfiles and etcfiles
        version = changelog_version()
        for examplesfile in examplesfiles:
            etcfile = posixpath.join(etcdir,
                posixpath.basename(examplesfile))
            infile = posixpath.join("examples",
                posixpath.basename(examplesfile))
            for outfile in examplesfile, etcfile:
                substitute_variables(infile, outfile, {
                    "version = dev": "version = %s" % version})


class checkbox_install_scripts(install_scripts, object):

    def run(self):
        """Run substitutions on files."""
        super(checkbox_install_scripts, self).run()

        # Substitute directory in defaults.py
        for outfile in self.outfiles:
            infile = posixpath.join("bin", posixpath.basename(outfile))
            substitute_variables(infile, outfile, {
                "CHECKBOX_SHARE:-.": "CHECKBOX_SHARE:-/usr/share/checkbox",
                "CHECKBOX_DATA:-.": "CHECKBOX_DATA:-$XDG_CACHE_HOME/checkbox"})


class checkbox_build_icons(build_icons, object):

    def initialize_options(self):
        super(checkbox_build_icons, self).initialize_options()

        self.icon_dir = "icons"


setup(
    name = "checkbox",
    version = changelog_version(),
    author = "Marc Tardif",
    author_email = "marc.tardif@canonical.com",
    license = "GPL",
    description = "Checkbox System Testing",
    long_description = """
This project provides an extensible interface for system testing.
""",
    data_files = [
        ("share/checkbox/", ["backend", "run"]),
        ("share/checkbox/data/audio/", ["data/audio/*"]), 
        ("share/checkbox/data/documents/", ["data/documents/*"]), 
        ("share/checkbox/data/images/", ["data/images/*"]), 
        ("share/checkbox/data/video/", ["data/video/*"]), 
        ("share/checkbox/data/settings/", ["data/settings/*"]), 
        ("share/checkbox/data/websites/", ["data/websites/*"]), 
        ("share/checkbox/data/whitelists/", ["data/whitelists/*"]), 
        ("share/checkbox/examples/", ["examples/*"]),
        ("share/checkbox/install/", ["install/*"]),
        ("share/checkbox/patches/", ["patches/*"]),
        ("share/checkbox/plugins/", ["plugins/*.py"]),
        ("share/checkbox/report/", ["report/*.*"]),
        ("share/checkbox/report/images/", ["report/images/*"]),
        ("share/checkbox/scripts/", ["scripts/*"]),
        ("share/checkbox/gtk/", ["gtk/checkbox-gtk.ui", "gtk/*.png"]),
        ("share/checkbox/qt/", ["qt/checkbox-qt.ui", "qt/*.png", "qt/frontend/checkbox-qt-service"]),
        ("share/dbus-1/services/", ["qt/com.canonical.QtCheckbox.service"]),
        ("share/apport/package-hooks/", ["apport/source_checkbox.py"]),
        ("share/apport/general-hooks/", ["apport/checkbox.py"])],
    scripts = ["bin/checkbox-cli", "bin/checkbox-gtk", "bin/checkbox-sru",
        "bin/checkbox-urwid", "bin/checkbox-qt"],
    packages = ["checkbox", "checkbox.contrib", "checkbox.lib", "checkbox.parsers",
        "checkbox.reports", "checkbox_cli", "checkbox_gtk", "checkbox_urwid", "checkbox_qt"],
    package_data = {
        "": ["cputable"]},
    cmdclass = {
        "build": checkbox_build,
        "build_i18n": build_i18n,
        "build_icons": checkbox_build_icons,
        "clean": checkbox_clean,
        "install": checkbox_install,
        "install_data": checkbox_install_data,
        "install_scripts": checkbox_install_scripts}
)
