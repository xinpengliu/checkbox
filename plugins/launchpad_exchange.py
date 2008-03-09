#
# Copyright (c) 2008 Canonical
#
# Written by Marc Tardif <marc@interunion.ca>
#
# This file is part of HWTest.
#
# HWTest is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HWTest is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HWTest.  If not, see <http://www.gnu.org/licenses/>.
#
import time
import pprint
import bz2
import logging

from gettext import gettext as _
from socket import gethostname
from StringIO import StringIO

from hwtest.log import format_delta
from hwtest.plugin import Plugin
from hwtest.transport import HTTPTransport


class LaunchpadExchange(Plugin):

    required_attributes = ["transport_url", "timeout"]

    def register(self, manager):
        super(LaunchpadExchange, self).register(manager)
        self._form = {
            "field.private": False,
            "field.contactable": False,
            "field.live_cd": False,
            "field.format": u'VERSION_1',
            "field.actions.upload": u'Upload'}

        for (rt, rh) in [
             ("exchange", self.exchange),
             ("report-datetime", self.report_datetime),
             ("report-architecture", self.report_architecture),
             ("report-submission_id", self.report_submission_id),
             ("report-system_id", self.report_system_id),
             ("report-distribution", self.report_distribution),
             ("report-email", self.report_email),
             ("report-launchpad", self.report_launchpad)]:
            self._manager.reactor.call_on(rt, rh)

    def report_datetime(self, message):
        self._form["field.date_created"] = message

    def report_architecture(self, message):
        self._form["field.architecture"] = message

    def report_submission_id(self, message):
        self._form["field.submission_key"] = message

    def report_system_id(self, message):
        self._form["field.system"] = message

    def report_distribution(self, message):
        self._form["field.distribution"] = message.distributor_id
        self._form["field.distroseries"] = message.release

    def report_email(self, message):
        self._form["field.emailaddress"] = message

    def report_launchpad(self, message):
        self._file = message

    def exchange(self):
        import hwtest.contrib.urllib2_file

        # Encode form data
        form = {}
        for field, value in self._form.items():
            form[field] = str(value).encode("utf-8")

        # Compress and add payload to form
        payload = file(self._file, "r").read()
        cpayload = bz2.compress(payload)
        f = StringIO(cpayload)
        f.name = '%s.xml.bz2' % str(gethostname())
        f.size = len(cpayload)
        form["field.submission_data"] = f

        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            logging.debug("Uncompressed payload length: %d", len(payload))

        self._manager.set_error()
        start_time = time.time()
        transport = HTTPTransport(self.config.transport_url)
        ret = transport.exchange(form, timeout=int(self.config.timeout))
        if not ret:
            self._manager.set_error(_("Failed to contact the server,\n"
                "are you connected to the Internet."))
            return
        elif ret.code != 200:
            self._manager.set_error(_("Failed to upload to server,\n"
                "please try again later."))
            return

        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            logging.debug("Response headers:\n%s",
                          pprint.pformat(ret.headers.items()))

        headers = ret.headers.getheaders("x-launchpad-hwdb-submission")
        if not headers:
            self._manager.set_error(_("Information was not posted to Launchpad."))
            return

        for header in headers:
            if "Error" in header:
                # HACK: this should return a useful error message
                self._manager.set_error(header)
                logging.error(header)
                return

        response = ret.read()
        logging.info("Sent %d bytes and received %d bytes in %s.",
                     f.size, len(response),
                     format_delta(time.time() - start_time))


factory = LaunchpadExchange
