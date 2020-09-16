from typing import List

from pyparsing import *


class IndentCheckpoint(ParseElementEnhance):
    """
    This is a wrapper element that simply rolls back changes in the indent stack whenever the contained element
    fails to match. This ensures the stack remains accurate
    """

    def __init__(self, expr: ParserElement, indent_stack: List[int]):
        super().__init__(expr)
        # self.expr = expr
        self.stack = indent_stack

    def parseImpl(self, instring, loc, doActions=True):
        # Backup the stack whenever we reach this element during the parse
        backup_stack = self.stack[:]
        try:
            return self.expr._parse(instring, loc, doActions, callPreParse=False)
        except ParseException as e:
            # On a parse failure, reset the stack
            self.stack[:] = backup_stack
            raise e

    def __str__(self):
        if hasattr(self, "name"):
            return self.name

        if self.strRepr is None:
            self.strRepr = "Indented[" + str(self.expr) + "]"

        return self.strRepr


class IndentParserMixin:
    """
    A mixin that maintains an indent stack, and utility methods for them
    """

    def __init__(self):
        self.stack = [1]

    def pop_indent(self):
        def check_indent(s, l, t):
            self.stack.pop()

        return (Empty() + Empty()).setParseAction(check_indent).setName("Pop")

    def push_indent(self):
        def check_indent(s, l, t):
            curCol = col(l, s)
            self.stack.append(curCol)

        return (Empty() + Empty()).setParseAction(check_indent).setName("Push")

    def peer_indent(self, allow_greater=False):
        """
        :param allow_greater: Allow greater indent than the previous indentation, but don't add it to the stack
        """

        def check_peer_indent(s, l, t):
            if l >= len(s):
                return
            curCol = col(l, s)
            if allow_greater and curCol >= self.stack[-1]:
                return
            elif curCol == self.stack[-1]:
                return
            else:
                if curCol > self.stack[-1]:
                    raise ParseException(s, l, "illegal nesting")
                raise ParseException(s, l, "not a peer entry")

        return Empty().setParseAction(check_peer_indent).setName("Peer")

    def indent(self, update=True):
        """
        :param update: If true, update the stack, otherwise simply check for an indent
        """

        def check_sub_indent(s, l, t):
            curCol = col(l, s)
            if curCol > self.stack[-1]:
                if update:
                    self.stack.append(curCol)
            else:
                raise ParseException(s, l, "not a subentry")

        return (Empty() + Empty().setParseAction(check_sub_indent)).setName("Indent")

    def dedent(self, precise=True):
        def check_dedent(s, l, t):
            if l >= len(s):
                return
            curCol = col(l, s)
            if precise and self.stack and curCol not in self.stack:
                raise ParseException(s, l, "not an unindent")
            if curCol < self.stack[-1]:
                self.stack.pop()

        return Empty().setParseAction(check_dedent).setName("Unindent")


__all__ = [IndentCheckpoint, IndentParserMixin]
