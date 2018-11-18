from turingarena.driver.interface.nodes import IntermediateNode


class SequenceNode(IntermediateNode):

    def _get_reference_actions(self):
        for n in self.children:
            yield from n.reference_actions

    def _get_declaration_directions(self):
        for n in self.children:
            yield from n.declaration_directions

    def validate(self):
        for n in self.children:
            yield from n.validate()
