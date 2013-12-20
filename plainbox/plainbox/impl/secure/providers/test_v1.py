# This file is part of Checkbox.
#
# Copyright 2013 Canonical Ltd.
# Written by:
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.

#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.

"""
plainbox.impl.secure.providers.test_v1
======================================

Test definitions for plainbox.impl.secure.providers.v1 module
"""

from unittest import TestCase

from plainbox.impl.secure.plugins import PlugInError
from plainbox.impl.secure.providers.v1 import AbsolutePathValidator
from plainbox.impl.secure.providers.v1 import ExistingDirectoryValidator
from plainbox.impl.secure.providers.v1 import IQNValidator
from plainbox.impl.secure.providers.v1 import Provider1
from plainbox.impl.secure.providers.v1 import Provider1Definition
from plainbox.impl.secure.providers.v1 import Provider1PlugIn
from plainbox.impl.secure.providers.v1 import VersionValidator
from plainbox.impl.secure.providers.v1 import WhiteListPlugIn
from plainbox.impl.secure.qualifiers import WhiteList
from plainbox.vendor import mock


class IQNValidatorTests(TestCase):

    def setUp(self):
        self.validator = IQNValidator()
        self.variable = None

    def test_good_values_work(self):
        name = "2013.com.canonical:certification-resources-server"
        self.assertEqual(self.validator(self.variable, name), None)

    def test_must_match_whole_string(self):
        name = "2013.com.canonical:certification-resources-server BOGUS"
        self.assertNotEqual(self.validator(self.variable, name), None)

    def test_bad_values_dont(self):
        self.assertEqual(
            self.validator(self.variable, ""),
            "must look like RFC3720 IQN")


class VersionValidatorTests(TestCase):

    def setUp(self):
        self.validator = VersionValidator()
        self.variable = None

    def test_typical_versions_work(self):
        version = "1.10.7"
        self.assertEqual(self.validator(self.variable, version), None)

    def test_single_digit_versions_work(self):
        version = "5"
        self.assertEqual(self.validator(self.variable, version), None)

    def test_bad_values_dont(self):
        version = "1.5a7"
        self.assertEqual(
            self.validator(self.variable, version),
            "must be a sequence of digits separated by dots")


class ExistingDirectoryValidatorTests(TestCase):

    _PATH = "/some/directory"

    def setUp(self):
        self.validator = ExistingDirectoryValidator()
        self.variable = None

    @mock.patch('os.path.isdir')
    def test_existing_directories_work(self, mock_isdir):
        mock_isdir.return_value = True
        self.assertEqual(self.validator(self.variable, self._PATH), None)
        mock_isdir.assertCalledWith(self._PATH)

    @mock.patch('os.path.isdir')
    def test_missing_directories_dont(self, mock_isdir):
        mock_isdir.return_value = False
        self.assertEqual(
            self.validator(self.variable, self._PATH),
            "no such directory")
        mock_isdir.assertCalledWith(self._PATH)


class AbsolutePathValidatorTests(TestCase):

    def setUp(self):
        self.validator = AbsolutePathValidator()
        self.variable = None

    def test_absolute_values_work(self):
        self.assertEqual(self.validator(self.variable, '/path'), None)

    def test_relative_values_dont(self):
        self.assertEqual(
            self.validator(self.variable, 'path'),
            "cannot be relative")


class Provider1DefinitionTests(TestCase):

    DEF_TEXT = (
        "[PlainBox Provider]\n"
        "location = /some/directory/\n"
        "name = 2013.org.example:smoke-test\n"
        "version = 1.0\n"
        "description = A provider for smoke testing\n")

    def setUp(self):
        self.definition = Provider1Definition()

    def test_smoke(self):
        with mock.patch('os.path.isdir') as mock_isdir:
            # Mock os.path.isdir so that we can validate location
            mock_isdir.return_value = True
            self.definition.read_string(self.DEF_TEXT)
        self.assertEqual(self.definition.location, "/some/directory/")
        self.assertEqual(self.definition.name, "2013.org.example:smoke-test")
        self.assertEqual(self.definition.version, "1.0")
        self.assertEqual(
            self.definition.description, "A provider for smoke testing")


class Provider1PlugInTests(TestCase):

    def setUp(self):
        with mock.patch('os.path.isdir') as mock_isdir:
            # Mock os.path.isdir so that we can validate location
            mock_isdir.return_value = True
            self.plugin = Provider1PlugIn(
                "foo.provider", Provider1DefinitionTests.DEF_TEXT)

    def test_plugin_name(self):
        self.assertEqual(
            self.plugin.plugin_name, "2013.org.example:smoke-test")

    def test_plugin_object(self):
        self.assertIsInstance(self.plugin.plugin_object, Provider1)

    def test_provieder_data(self):
        provider = self.plugin.plugin_object
        self.assertEqual(provider.base_dir, "/some/directory/")
        self.assertEqual(provider.name, "2013.org.example:smoke-test")
        self.assertEqual(provider.version, "1.0")
        self.assertEqual(provider.description, "A provider for smoke testing")


class WhiteListPlugInTests(TestCase):
    """
    Tests for WhiteListPlugIn
    """

    def setUp(self):
        self.plugin = WhiteListPlugIn("/path/to/some.whitelist", "foo\nbar\n")

    def test_plugin_name(self):
        """
        verify that the WhiteListPlugIn.plugin_name property returns
        WhiteList.name
        """
        self.assertEqual(self.plugin.plugin_name, "some")

    def test_plugin_object(self):
        """
        verify that the WhiteListPlugIn.plugin_object property returns a
        WhiteList
        """
        self.assertIsInstance(self.plugin.plugin_object, WhiteList)

    def test_whitelist_data(self):
        """
        verify the contents of the loaded whitelist object
        """
        self.assertEqual(
            self.plugin.plugin_object.inclusive_qualifier_list[0].pattern_text,
            "^foo$")
        self.assertEqual(
            self.plugin.plugin_object.inclusive_qualifier_list[1].pattern_text,
            "^bar$")
        self.assertEqual(
            self.plugin.plugin_object.exclusive_qualifier_list, ())

    def test_init_failing(self):
        """
        verify how WhiteList() initializer works if something is wrong
        """
        # The pattern is purposefully invalid
        with self.assertRaises(PlugInError) as boom:
            WhiteListPlugIn("/path/to/some.whitelist", "*")
        # NOTE: we should have syntax error for whitelists that keeps track or
        # line we're at to help developers figure out where errors such as this
        # are coming from.
        self.assertEqual(
            str(boom.exception),
            ("Cannot load whitelist '/path/to/some.whitelist': "
             "nothing to repeat"))


class Provider1Tests(TestCase):

    BASE_DIR = "base-dir"
    NAME = "2013.org.example:name"
    VERSION = "1.0"
    DESCRIPTION = "description"
    SECURE = True

    def setUp(self):
        self.provider = Provider1(
            self.BASE_DIR, self.NAME, self.VERSION, self.DESCRIPTION,
            self.SECURE)

    def test_repr(self):
        self.assertEqual(
            repr(self.provider),
            "<Provider1 name:'2013.org.example:name' base_dir:'base-dir'>")

    def test_base_dir(self):
        """
        Verify that Provider1.base_dir attribute is set correctly
        """
        self.assertEqual(self.provider.base_dir, self.BASE_DIR)

    def test_name(self):
        """
        Verify that Provider1.name attribute is set correctly
        """
        self.assertEqual(self.provider.name, self.NAME)

    def test_version(self):
        """
        Verify that Provider1.version attribute is set correctly
        """
        self.assertEqual(self.provider.version, self.VERSION)

    def test_description(self):
        """
        Verify that Provider1.description attribute is set correctly
        """
        self.assertEqual(self.provider.description, self.DESCRIPTION)

    def test_jobs_dir(self):
        """
        Verify that Provider1.jobs_dir attribute is set correctly
        """
        self.assertEqual(self.provider.jobs_dir, "base-dir/jobs")

    def test_bin_dir(self):
        """
        Verify that Provider1.bin_dir attribute is set correctly
        """
        self.assertEqual(self.provider.bin_dir, "base-dir/bin")

    def test_whitelists_dir(self):
        """
        Verify that Provider1.whitelists_dir attribute is set correctly
        """
        self.assertEqual(self.provider.whitelists_dir, "base-dir/whitelists")

    def test_CHECKBOX_SHARE(self):
        """
        Verify that Provider1.CHECKBOX_SHARE is always equal to base_dir
        """
        self.assertEqual(self.provider.CHECKBOX_SHARE, self.provider.base_dir)

    def test_extra_PYTHONPATH(self):
        """
        Verify that Provider1.extra_PYTHONPATH is always None
        """
        self.assertIsNone(self.provider.extra_PYTHONPATH)

    def test_secure(self):
        """
        Verify that Provider1.secure attribute is set correctly
        """
        self.assertEqual(self.provider.secure, self.SECURE)

    def test_get_builtin_whitelists__normal(self):
        """
        verify that Provider1.get_builtin_whitelist() loads and returns all of
        the whitelists
        """
        fake_plugins = [WhiteListPlugIn("/path/to/some.whitelist", "foo")]
        with self.provider._whitelist_collection.fake_plugins(fake_plugins):
            whitelist_list = self.provider.get_builtin_whitelists()
        self.assertEqual(len(whitelist_list), 1)
        self.assertEqual(repr(whitelist_list[0]), "<WhiteList name:'some'>")

    def test_get_builtin_whitelists__failing(self):
        """
        verify that Provider1.get_builtin_whitelist() raises the first
        exception that happens during the load process
        """
        fake_plugins = [WhiteListPlugIn("/path/to/some.whitelist", "foo")]
        fake_problems = [IOError("first problem"), OSError("second problem")]
        with self.assertRaises(IOError):
            with self.provider._whitelist_collection.fake_plugins(
                    fake_plugins, fake_problems):
                self.provider.get_builtin_whitelists()

    def test_get_builtin_jobs(self):
        self.skipTest("not implemented")

    def test_get_all_executables(self):
        self.skipTest("not implemented")

    def test_load_jobs(self):
        self.skipTest("not implemented")
