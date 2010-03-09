#
# This file is part of Checkbox.
#
# Copyright 2010 Canonical Ltd.
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
import os
import shutil
import signal

from subprocess import call, PIPE
from tempfile import mkdtemp

from checkbox.lib.fifo import FifoReader, FifoWriter, create_fifo

from checkbox.plugin import Plugin
from checkbox.properties import Path


class BackendInfo(Plugin):

    command = Path(default="%(checkbox_share)s/backend")

    def register(self, manager):
        super(BackendInfo, self).register(manager)

        for (rt, rh) in [
             ("message-exec", self.message_exec),
             ("stop", self.stop)]:
            self._manager.reactor.call_on(rt, rh)

        # Backend should run as early as possible
        self._manager.reactor.call_on("gather", self.gather, -1000)

    def get_root_command(self, command):
        uid = os.getuid()
        if uid == 0:
            prefix = []
        elif os.getenv("DISPLAY") and \
                call(["which", "kdesudo"],
                    stdout=PIPE, stderr=PIPE) == 0 and \
                call(["pgrep", "-x", "-u", str(uid), "ksmserver"],
                    stdout=PIPE, stderr=PIPE) == 0:
            prefix = ["kdesudo", "--"]
        elif os.getenv("DISPLAY") and \
                call(["which", "gksu"],
                    stdout=PIPE, stderr=PIPE) == 0 and \
                call(["pgrep", "-x", "-u", str(uid), "gnome-panel|gconfd-2"],
                    stdout=PIPE, stderr=PIPE) == 0:
            prefix = ["gksu", "-k", "--"]
        else:
            prefix = ["sudo", "-E"]

        # Append PATH
        prefix.append("PATH=%s" % os.environ["PATH"])

        # Extend command
        prefix.extend(command)

        return prefix

    def gather(self):
        self.directory = mkdtemp(prefix="checkbox")
        child_input = create_fifo(os.path.join(self.directory, "input"), 0600)
        child_output = create_fifo(os.path.join(self.directory, "output"), 0600)

        self.pid = os.fork()
        if self.pid > 0:
            self.parent_writer = FifoWriter(child_input)
            self.parent_reader = FifoReader(child_output)

        else:
            command = [self.command, child_input, child_output]
            root_command = self.get_root_command(command)
            os.execvp(root_command[0], root_command)
            # Should never get here

    def message_exec(self, message):
        if "user" in message:
            self.parent_writer.write_object(message)
            result = self.parent_reader.read_object()
            self._manager.reactor.fire("message-result", *result)

    def stop(self):
        os.kill(self.pid, signal.SIGHUP)
        os.waitpid(self.pid, 0)

        shutil.rmtree(self.directory)


factory = BackendInfo
