from turingarena_impl.interface.diagnostics import Diagnostic
from .test_utils import assert_interface_error, define_algorithm

interface_text = """
    function f1();
    function f2();

    main {
        loop {
            read a;
            switch a {
                case 1 {
                    call b = f1();
                    write b;
                }
                case 2 {
                    call b = f2();
                    write b;
                } 
                case 3 {
                    break;
                }
            }
        }
    }
"""


def test_loop():
    with define_algorithm(
        interface_text=interface_text,
        language_name="c++",
        source_text="""
            int f1() {return 1;}
            int f2() {return 2;}
        """,
    ) as algo:
        with algo.run() as p:
            print ("running process")
            assert p.call.f1() == 1
            print("call f1() ok")
            assert p.call.f2() == 2
            print("call f2() ok")
            assert p.call.f1() == 1
            print("call f1() ok")


def test_unexpected_break():
    assert_interface_error("""
        main {
            break;
        }
    """, Diagnostic.Messages.UNEXPECTED_BREAK)


def test_unreachable_code():
    assert_interface_error("""
        main {
            loop {
                write 1;
                break;
                write 2;
            }
        }
    """, Diagnostic.Messages.UNREACHABLE_CODE)


def test_infinite_loop():
    assert_interface_error("""
        main {
            loop {
            }
        }        
    """, Diagnostic.Messages.INFINITE_LOOP)