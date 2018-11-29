import itertools
import logging
from collections import namedtuple
from functools import partial

from turingarena.driver.interface.analysis import TreeAnalyzer
from turingarena.driver.interface.expressions import ExpressionCompiler
from turingarena.driver.interface.nodes import PrintCallbackRequest, PrintCallbackIndex, CallbackStart, CallbackEnd, \
    ForIndex, MainExit, InitialCheckpoint, Case, CallbackImplementation, statement_classes, Step, ParameterDeclaration, \
    CallbackPrototype, ConstantDeclaration, Block, Variable
from turingarena.driver.interface.validate import Validator
from turingarena.driver.interface.variables import ReferenceDeclaration, ReferenceResolution
from turingarena.util.visitor import visitormethod, classvisitormethod

logger = logging.getLogger(__name__)


class InterfaceContext(namedtuple("InterfaceContext", [
    "methods",
    "constants",
]), TreeAnalyzer, ExpressionCompiler):
    def with_constant(self, declaration):
        return self._replace(
            constants=self.constants + (declaration,),
        )

    def with_method(self, method):
        return self._replace(
            methods=self.methods + (method,),
        )

    @property
    def methods_by_name(self):
        return {m.name: m for m in self.methods}

    def constant_declaration(self, ast):
        return ConstantDeclaration(
            variable=Variable(name=ast.name),
            value=self.expression(ast.value),
        )

    def prototype(self, cls, ast):
        return cls(
            name=ast.declarator.name,
            parameter_declarations=[
                self.parameter_declaration(p)
                for p in ast.declarator.parameters
            ],
            has_return_value=(ast.declarator.type == 'function'),
            callbacks=[
                self.prototype(CallbackPrototype, c)
                for c in ast.callbacks
            ],
        )

    def parameter_declaration(self, ast):
        return ParameterDeclaration(
            variable=Variable(name=ast.name),
            dimensions=len(ast.indexes),
        )

    def main_block(self, ast):
        return self.main_block_context.block(
            ast,
            prepend_nodes=[InitialCheckpoint()],
            append_nodes=[MainExit()],
        )

    @property
    def main_block_context(self):
        return self.initial_context.with_reference_actions(
            a(c.variable)
            for c in self.constants
            for a in [
                partial(ReferenceDeclaration, dimensions=0),
                ReferenceResolution,
            ]
        )

    @property
    def initial_context(self):
        return StatementContext(
            global_context=self,
            prev_reference_actions=(),
            index_variables=(),
            main_block=True,
            in_loop=False,
        )


class StatementContext(namedtuple("StatementContext", [
    "global_context",
    "prev_reference_actions",
    "index_variables",
    "main_block",
    "in_loop",
]), Validator, TreeAnalyzer, ExpressionCompiler):
    def with_reference_actions(self, actions):
        actions = tuple(actions)
        assert all(
            a.reference is not None
            for a in actions
        )
        return self._replace(
            prev_reference_actions=self.prev_reference_actions + actions
        )

    def get_resolved_references(self):
        return {
            a.reference
            for a in self.prev_reference_actions
            if isinstance(a, ReferenceResolution)
        }

    @property
    def reference_declaration_mapping(self):
        return {
            a.reference.variable.name: a
            for a in self.prev_reference_actions
            if isinstance(a, ReferenceDeclaration)
        }

    def with_index_variable(self, variable):
        return self._replace(
            index_variables=self.index_variables + (variable,),
        )

    def with_loop(self):
        return self._replace(in_loop=True)

    def is_relevant(self, n):
        "Whether this node should be kept in the parent block"
        return self._is_relevant(n)

    @visitormethod
    def _is_relevant(self, n):
        pass

    def _is_relevant_SwitchValueResolve(self, n):
        return not self.is_resolved(n.value)

    def _is_relevant_IfConditionResolve(self, n):
        return not self.is_resolved(n.condition)

    def _is_relevant_CallReturn(self, n):
        return n.return_value is not None

    def _is_relevant_PrintNoCallbacks(self, n):
        return n.method and n.method.callbacks

    def _is_relevant_AcceptCallbacks(self, n):
        return n.method and n.method.has_callbacks

    def _is_relevant_object(self, n):
        return True

    @visitormethod
    def dimensions(self, e) -> int:
        pass

    def dimensions_Literal(self, e):
        return 0

    def dimensions_Variable(self, e):
        try:
            reference_declaration = self.reference_declaration_mapping[e.name]
        except KeyError:
            return 0
        return reference_declaration.dimensions

    def dimensions_Subscript(self, e):
        array_dimensions = self.dimensions(e.array)
        if array_dimensions < 1:
            # not an array, fix
            return 0
        return array_dimensions - 1

    @visitormethod
    def is_resolved(self, e) -> bool:
        pass

    def is_resolved_Literal(self, e):
        return True

    def is_resolved_Variable(self, e):
        return e in self.get_resolved_references()

    def is_resolved_Subscript(self, e):
        return (
                e in self.get_resolved_references()
                or self.is_resolved(e.array)
        )

    def group_nodes(self, nodes):
        pass

    @classvisitormethod
    def compile(self, cls, ast):
        pass

    def compile_object(self, cls, ast):
        return cls()

    def compile_IONode(self, cls, ast):
        return cls(arguments=[
            self.expression(a) for a in ast.arguments
        ])

    def compile_Return(self, cls, ast):
        return cls(value=self.expression(ast.value))

    def compile_For(self, cls, ast):
        index = ForIndex(
            variable=Variable(name=ast.index),
            range=self.expression(ast.range),
        )

        return cls(
            index=index,
            body=self.with_index_variable(index).with_reference_actions([
                ReferenceDeclaration(index.variable, dimensions=0),
                ReferenceResolution(index.variable),
            ]).block(ast.body)
        )

    def compile_SwitchNode(self, cls, ast):
        return cls(
            value=self.expression(ast.value),
            cases=[
                Case(
                    labels=[self.expression(l) for l in case_ast.labels],
                    body=self.block(case_ast.body),
                )
                for case_ast in ast.cases
            ],
        )

    def compile_IfNode(self, cls, ast):
        return cls(
            condition=self.expression(ast.condition),
            then_body=self.block(ast.then_body),
            else_body=self.block(ast.else_body) if ast.else_body is not None else None,
        )

    def compile_Loop(self, cls, ast):
        return cls(
            body=self.with_loop().block(ast.body)
        )

    def compile_CallNode(self, cls, ast):
        method = self.global_context.methods_by_name.get(ast.name)

        body_by_name = {
            ast.declarator.name: ast.body
            for ast in ast.callbacks
        }

        callbacks = [
            self.callback_implementation(
                prototype=prototype,
                index=index,
                ast=body_by_name.get(prototype.name),
            )
            for index, prototype in enumerate(method.callbacks)
        ]

        return cls(
            method=method,
            arguments=[self.expression(a) for a in ast.arguments],
            return_value=self.expression(ast.return_value) if ast.return_value is not None else None,
            callbacks=callbacks,
        )

    def callback_implementation(self, prototype, index, ast):
        prepend_nodes = [
            CallbackStart(prototype),
            PrintCallbackRequest(),
            PrintCallbackIndex(index=index, prototype=prototype),
        ]

        if prototype.has_return_value:
            append_nodes = []
        else:
            append_nodes = [CallbackEnd()]

        return CallbackImplementation(
            index=index,
            prototype=prototype,
            body=self.block(
                ast,
                prepend_nodes=prepend_nodes,
                append_nodes=append_nodes,
            )
        )

    def group_children(self, children):
        group = []
        for node in children:
            can_be_grouped = self.can_be_grouped(node)

            if can_be_grouped and len(self._group_directions(group + [node])) <= 1:
                group.append(node)
                continue

            if group:
                yield self._make_step(group)
                group.clear()

            if not can_be_grouped:
                yield node
            else:
                group.append(node)

        if group:
            yield self._make_step(group)

    def _make_step(self, group):
        return Step(tuple(group), self._group_direction(group))

    def _group_direction(self, group):
        directions = self._group_directions(group)
        if not directions:
            return None
        [direction] = directions
        return direction

    def _group_directions(self, group):
        return {d for n in group for d in self.declaration_directions(n)}

    def _compile_block_flat(self, asts):
        inner_context = self._replace(main_block=False)
        for ast in asts:
            for cls in statement_classes[ast.statement_type]:
                node = inner_context.compile(cls, ast)
                if not inner_context.is_relevant(node):
                    continue
                yield node
            inner_context = inner_context.with_reference_actions(inner_context.reference_actions(node))

    def block(self, ast, prepend_nodes=(), append_nodes=()):
        return Block(
            children=tuple(
                self.group_children(
                    itertools.chain(
                        prepend_nodes,
                        self._compile_block_flat(ast.statements),
                        append_nodes,
                    )
                )
            )
        )
