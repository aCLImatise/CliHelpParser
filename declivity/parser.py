from parsimonious.grammar import Grammar, NodeVisitor
from parsimonious.nodes import RegexNode

grammar = Grammar(
    """
    help = spaced_section+
    spaced_section = space* section space*
    section = option_section / usage_section
    
    usage_section = ~r"usage:"i usage
    usage = ~r".+$"m
    
    option_section = option_preamble space? option_list
    option_preamble = ~r".+(arguments|options):"i
    option_list = space* option+ space*
    option = whitespace* flags whitespace* description?
    flags = flag (flagsep flag)*
    flagsep = ("," / "|") " "?
    
    space = whitespace / newline
    whitespace = ~r"\s"
    newline = "\\n"
    
    flag = (short_flag / long_flag) metavar?
    short_flag = ~r"-\w"
    long_flag = ~r"--\w+"
    
    description = description_char+
    description_char = ~r"."s
    
    choices = "{" choice_list "}"
    choice_list = option ("," option)
    
    metavar = metavar_sep word
    metavar_sep = "=" / " "
    word = ~r"\w+"
    """
)


class RuleVisitor(NodeVisitor):
    @staticmethod
    def parse_list(args):
        """
        Parses a rule where we have a mandatory first argument, then an optional list of separator + argument
        For example:
            option_list = option ("," option)
        :param args:
        :return:
        """
        ret = [args[0]]
        for optional in args[1]:
            ret.append(optional[2])
        return ret

    def visit_description(self, node, children):
        return ''.join(children)

    def visit_option_section(self, node, children):
        _, _, option_list = children
        return option_list

    def visit_section(self, node, children):
        return children

    def visit_spaced_section(self, node, children):
        _, section, _ = children
        return section

    def visit_option_list(self, node, children):
        _, option, _ = children
        return option

    def visit_option(self, node, children):
        _, flags, _, description = children
        metavar = [flag['metavar'] for flag in flags if flag['metavar'] is not None]
        return {
            'flags': [flag['flag'] for flag in flags],
            'metavar': metavar[0] if len(metavar) > 0 else None,
            'description': description[0]
        }

    def visit_flags(self, node, children):
        return self.parse_list(children)

    def visit_flag(self, node, children):
        flag, metavar = children
        return {
            'flag': flag[0],
            'metavar': metavar[0] if isinstance(metavar, list) else None
        }

    def visit_metavar(self, node, children):
        metavar_sep, word = children
        return word

    def visit_choices(self, node, children):
        l_brace, option_list, r_brace = children
        return option_list

    def visit_choice_list(self, node, children):
        return self.parse_list(children)

    def generic_visit(self, node, visited_children):
        """Replace childbearing nodes with a list of their children; keep
        others untouched.
        For our case, if a node has children, only the children are important.
        Otherwise, keep the node around for (for example) the flags of the
        regex rule. Most of these kept-around nodes are subsequently thrown
        away by the other visitor methods.
        We can't simply hang the visited children off the original node; that
        would be disastrous if the node occurred in more than one place in the
        tree.
        """
        if isinstance(node, RegexNode):
            return node.text

        return visited_children or node  # should semantically be a tuple


def parse(text: str):
    tree = grammar.parse(text)
    visitor = RuleVisitor()
    return visitor.visit(tree)
