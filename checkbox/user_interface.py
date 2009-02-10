#
# Copyright (c) 2008 Canonical
#
# Written by Marc Tardif <marc@interunion.ca>
#
# This file is part of Checkbox.
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.
#
import gettext
import logging

from checkbox.contrib.REThread import REThread

from checkbox.lib.iterator import NEXT


class UserInterface(object):
    """Abstract base class for encapsulating the workflow and common code for
       any user interface implementation (like GTK, Qt, or CLI).

       A concrete subclass must implement all the abstract show_* methods."""

    def __init__(self, config):
        self._config = config

        self.direction = NEXT
        self.gettext_domain = "checkbox"
        gettext.textdomain(self.gettext_domain)

    def do_function(self, function, *args, **kwargs):
        thread = REThread(target=function, name="do_function",
            args=args, kwargs=kwargs)
        thread.start()

        while thread.isAlive():
            self.show_pulse()
            thread.join(0.1)
        thread.exc_raise()

        return thread.return_value()

    def show_error(self, title, text):
        logging.error("%s: %s", title, text)

    def show_wait(self, message, function, *args, **kwargs):
        self.do_function(function, *args, **kwargs)

    def show_pulse(self):
        pass

    def show_intro(self, title, text):
        raise NotImplementedError, \
            "this function must be overridden by subclasses"

    def show_category(self, title, text, category):
        raise NotImplementedError, \
            "this function must be overridden by subclasses"

    def show_test(self, test, result):
        raise NotImplementedError, \
            "this function must be overridden by subclasses"

    def show_exchange(self, authentication, reports=[], message=None,
                      error=None):
        raise NotImplementedError, \
            "this function must be overridden by subclasses"

    def show_final(self, message):
        raise NotImplementedError, \
            "this function must be overridden by subclasses"
