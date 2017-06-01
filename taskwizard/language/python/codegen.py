import os

from taskwizard.generation.codegen import AbstractDriverGenerator, AbstractInterfaceDriverGenerator, AbstractSupportGenerator
from taskwizard.generation.utils import write_to_file, indent_all


class InterfaceDriverGenerator(AbstractInterfaceDriverGenerator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.module_path = os.path.join(
            self.driver_generator.package_dir,
            self.interface.name + ".py"
        )

    def generate(self):
        module_file = open(self.module_path, "w")
        write_to_file(self.generate_module(), module_file)

    def generate_module(self):
        global_scope = {}

        yield "class {name}:".format(
            name=self.interface.name
        )
        yield from indent_all(self.generate_class_body())

    def generate_class_body(self):
        yield "pass"


class DriverGenerator(AbstractDriverGenerator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.package_dir = os.path.join(self.dest_dir, "interfaces")

    def generate(self):
        os.mkdir(self.package_dir)

        for interface in self.task.interfaces:
            self.generate_interface(interface)

    def generate_interface(self, interface):
        InterfaceDriverGenerator(self, interface).generate()


class SupportGenerator(AbstractSupportGenerator):
    pass