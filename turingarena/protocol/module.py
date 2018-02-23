import importlib
import os
import pickle
import sys

import pkg_resources

from turingarena.common import ImmutableObject
from turingarena.modules import module_to_python_package, prepare_module_dir
from turingarena.protocol.exceptions import ProtocolError

PROTOCOL_QUALIFIER = "protocol"
ORIGINAL_SOURCE_FILENAME = "_original_source_filename.txt"


class ProtocolSource(ImmutableObject):
    __slots__ = [
        "filename",
        "text",
    ]

    def compile(self, **kwargs):
        # FIXME: make top-level
        from turingarena.protocol.model.model import ProtocolDefinition
        from turingarena.protocol.parser import parse_protocol

        ast = parse_protocol(self.text, **kwargs)
        return ProtocolDefinition.compile(ast=ast)

    def generate(self, *, dest_dir, name):
        module_dir = prepare_module_dir(dest_dir, PROTOCOL_QUALIFIER, name)
        try:
            definition = self.compile(filename=self.filename)
        except ProtocolError as e:
            sys.exit(e.get_user_message())
        dest_source_filename = os.path.join(module_dir, "_source.tap")
        with open(dest_source_filename, "w") as f:
            f.write(self.text)
        dest_original_filename_filename = os.path.join(module_dir, ORIGINAL_SOURCE_FILENAME)
        with open(dest_original_filename_filename, "w") as f:
            f.write(self.filename)

        # FIXME: make top-level
        from turingarena.protocol.proxy.python import generate_proxy
        from turingarena.protocol.skeleton import generate_skeleton

        with open(os.path.join(module_dir, "_definition.pickle"), "wb") as f:
            pickle.dump(definition, f)
        generate_proxy(module_dir, definition)
        generate_skeleton(definition, dest_dir=os.path.join(module_dir, "_skeletons"))


class ProtocolModule:
    __slots__ = ["name", "source"]

    def __init__(self, name):
        self.name = name

        module = self.module_name()
        source_text = pkg_resources.resource_string(module, "_source.tap").decode()
        source_original_filename = pkg_resources.resource_string(module, ORIGINAL_SOURCE_FILENAME).decode()

        self.source = ProtocolSource(
            text=source_text,
            filename=source_original_filename,
        )

    def module_name(self):
        return module_to_python_package(PROTOCOL_QUALIFIER, self.name)

    def load_definition(self):
        module = self.module_name()
        path = pkg_resources.resource_filename(module, "_definition.pickle")
        with open(path, "rb") as f:
            return pickle.load(f)

    def load_interface_signature(self, interface_name):
        proxy_module = importlib.import_module(
            module_to_python_package(PROTOCOL_QUALIFIER, self.name) + "._proxy",
        )
        return getattr(proxy_module, interface_name)
