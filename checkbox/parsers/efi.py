#
# This file is part of Checkbox.
#
# Copyright 2011 Canonical Ltd.
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
import re


class EfiDevice:

    path = "/sys/class/dmi/id/bios_version"
    category = "EFI"

    def __init__(self, product, vendor=None):
        self.product = product
        self.vendor = vendor


class EfiParser:
    """Parser for EFI information."""

    def __init__(self, stream):
        self.stream = stream

    def run(self, result):
        vendor_product_pattern = re.compile(
            r"^(?P<vendor>.*)\s+by\s+(?P<product>.*)$")

        for line in self.stream.readlines():
            line = line.strip()
            match = vendor_product_pattern.match(line)
            if match:
                product = match.group("product")
                vendor = match.group("vendor")
                device = EfiDevice(product, vendor)
            else:
                device = EfiDevice(line)

            result.setEfiDevice(device)
