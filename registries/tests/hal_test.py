from registries.hal import HalRegistry
from registries.tests.helpers import TestHelper


class HalRegistryTest(TestHelper):

    def test_system_vendor(self):
        registry = HalRegistry(self.config)
        self.assertTrue(registry.computer.system.vendor is not None)
