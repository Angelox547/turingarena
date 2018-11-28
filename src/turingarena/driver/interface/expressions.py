import logging
from abc import abstractmethod
from collections import namedtuple

logger = logging.getLogger(__name__)


class ExpressionCompiler:
    __slots__ = []

    def expression(self, ast):
        return getattr(self, f"_compile_{ast.expression_type}")(ast)

    def _compile_int_literal(self, ast):
        return IntLiteralAst(value=int(ast.int_literal))

    def _compile_reference_subscript(self, ast):
        return self._compile_subscript(ast, ast.indices)

    def _compile_subscript(self, ast, index_asts):
        if index_asts:
            array = self._compile_subscript(ast, index_asts[:-1])
            index = Expression.compile(index_asts[-1])
            return Subscript(array, index)
        else:
            return VariableReference(ast.variable_name)


class Expression:
    __slots__ = []

    @staticmethod
    def compile(ast):
        return ExpressionCompiler().expression(ast)


class Literal(Expression):
    __slots__ = []

    @property
    @abstractmethod
    def value(self):
        pass


class IntLiteral(Literal):
    __slots__ = []


class IntLiteralAst(namedtuple("IntLiteralAst", ["value"]), IntLiteral):
    __slots__ = []


class IntLiteralSynthetic(
    namedtuple("IntLiteralSynthetic", ["value"]),
    IntLiteral,
):
    __slots__ = []


class VariableReference(namedtuple("VariableReference", ["variable_name"]), Expression):
    __slots__ = []


class Subscript(Expression, namedtuple("Subscript", [
    "array",
    "index",
])):
    __slots__ = []
