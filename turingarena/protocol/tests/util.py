import os
import random
import string
import sys
from collections import deque
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from turingarena.protocol.module import ProtocolSource
from turingarena.protocol.proxy.library import ProxiedAlgorithm
from turingarena.sandbox.languages.cpp import CppAlgorithmSource
from turingarena.sandbox.languages.python import PythonAlgorithmSource


@contextmanager
def algorithm(*, protocol_text, language, source_text, interface_name):
    protocol = "test_protocol_" + ''.join(random.choices(string.ascii_lowercase, k=8))
    interface = f"{protocol}:{interface_name}"

    protocol_source = ProtocolSource(
        text=protocol_text,
        filename="<none>",
    )

    languages = {
        "c++": CppAlgorithmSource,
        "python": PythonAlgorithmSource,
    }

    algorithm_source = languages[language](
        interface=interface,
        filename=None,
        language=language,
        text=source_text,
    )

    with TemporaryDirectory() as temp_dir:
        protocol_source.generate(dest_dir=temp_dir, name=protocol)

        sys.path.append(temp_dir)
        old_path = os.environ["PYTHONPATH"]
        try:
            os.environ["PYTHONPATH"] = temp_dir

            algorithm_dir = os.path.join(temp_dir, "algorithm")
            algorithm_source.compile(algorithm_dir)

            impl = ProxiedAlgorithm(
                algorithm_dir=algorithm_dir,
                interface=interface,
            )

            yield impl
        finally:
            sys.path.remove(temp_dir)
            os.environ["PYTHONPATH"] = old_path


def callback_mock(calls, return_values=None):
    if return_values is not None:
        return_values = deque(return_values)

    def mock(*args):
        calls.append((mock, args))

        if return_values is not None:
            return return_values.popleft()

    return mock
