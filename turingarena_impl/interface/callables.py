import logging
from collections import namedtuple

from turingarena_impl.interface.block import Block
from turingarena_impl.interface.common import AbstractSyntaxNodeWrapper, Instruction
from turingarena_impl.interface.diagnostics import Diagnostic
from turingarena_impl.interface.expressions import SyntheticExpression
from turingarena_impl.interface.statements.statement import SyntheticStatement
from turingarena_impl.interface.variables import Variable

logger = logging.getLogger(__name__)


class ParameterDeclaration(AbstractSyntaxNodeWrapper):
    __slots__ = []

    @property
    def variable(self):
        return Variable(
            value_type=Variable.value_type_dimensions(self.ast.indexes),
            name=self.ast.name,
        )


class CallablePrototype(AbstractSyntaxNodeWrapper):
    __slots__ = []

    @property
    def name(self):
        return self.ast.declarator.name

    @property
    def parameter_declarations(self):
        return [
            ParameterDeclaration(ast=p, context=self.context)
            for p in self.ast.declarator.parameters
        ]

    @property
    def parameters(self):
        return [
            p.variable
            for p in self.parameter_declarations
        ]

    @property
    def has_return_value(self):
        return self.ast.declarator.type == 'function'

    @property
    def callbacks(self):
        return [
            CallbackPrototype(callback, self.context)
            for callback in self.ast.callbacks
        ]

    @property
    def has_callbacks(self):
        return bool(self.callbacks)

    def validate(self):
        return []


class MethodPrototype(CallablePrototype):
    __slots__ = []


class CallbackPrototype(CallablePrototype):
    __slots__ = []

    def validate(self):
        for callback in self.callbacks:
            yield Diagnostic(
                Diagnostic.Messages.UNEXPECTED_CALLBACK,
                callback.name,
                parseinfo=callback.ast.parseinfo,
            )
        for parameter in self.parameter_declarations:
            if parameter.variable.value_type.dimensions:
                yield Diagnostic(
                    Diagnostic.Messages.CALLBACK_PARAMETERS_MUST_BE_SCALARS,
                    callback.name,
                    parseinfo=parameter.ast.parseinfo,
                )


class SyntheticCallbackBody(namedtuple("SyntheticCallbackBody", ["context", "body"])):
    @property
    def synthetic_statements(self):
        callback_index = self.context.callback_index
        yield SyntheticStatement("write", arguments=[
            SyntheticExpression("int_literal", value=1),  # more callbacks
        ])
        yield SyntheticStatement("write", arguments=[
            SyntheticExpression("int_literal", value=callback_index),
        ])
        yield from self.body.synthetic_statements


class CallbackImplementation(CallbackPrototype):
    __slots__ = []

    @property
    def synthetic_body(self):
        return SyntheticCallbackBody(
            self.context,
            self.body,
        )

    @property
    def body(self):
        # TODO: generate block if body is None ('default' is specified)
        return Block(
            ast=self.ast.body,
            context=self.context.local_context.create_inner().with_variables(self.parameters),
        )

    def validate(self):
        yield from self.prototype.validate()

    def generate_instructions(self, bindings):
        inner_bindings = {
            **bindings,
            **{
                p.name: [None] for p in self.parameters
            }
        }
        yield CallbackCallInstruction(self, bindings=inner_bindings)
        yield from self.body.generate_instructions(inner_bindings)


class CallbackCallInstruction(Instruction, namedtuple("CallbackCallInstruction", [
    "callback", "bindings",
])):
    def on_generate_response(self):
        parameters = [
            self.bindings[p.name][0]
            for p in self.callback.parameters
        ]

        assert all(isinstance(v, int) for v in parameters)
        return (
            [1] +  # has callback
            [self.callback.context.callback_index] +
            parameters
        )
