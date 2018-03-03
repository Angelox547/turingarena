import sys

from turingarena.cli import docopt_cli
from turingarena.common import write_to_file
from turingarena.protocol.model.model import InterfaceDefinition
from turingarena.protocol.skeleton.cpp import generate_template_cpp, generate_skeleton_cpp
from turingarena.protocol.skeleton.python import generate_template_python, generate_skeleton_python


@docopt_cli
def generate_template_cli(args):
    """Generate interface template code.

    Usage:
        template [options]

    Options:
        -x --language=<lang>  Source language [default: c++].
        -I --interface=<file>  Interface definition file [default: interface.txt].
    """

    generate(args, {
        "c++": generate_template_cpp,
        "python": generate_template_python,
    })


@docopt_cli
def generate_skeleton_cli(args):
    """Generate interface skeleton code (for debugging).

    Usage:
        skeleton [options]

    Options:
        -x --language=<lang>  Source language [default: c++].
        -I --interface=<file>  Interface definition file [default: interface.txt].
    """

    generate(args, {
        "c++": generate_skeleton_cpp,
        "python": generate_skeleton_python,
    })


def generate(args, generators):
    with open(args["--interface"]) as f:
        interface_text = f.read()
    interface = InterfaceDefinition.compile(interface_text)
    generator = generators[args["--language"]]
    write_to_file(generator(interface), sys.stdout)