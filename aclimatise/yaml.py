from ruamel.yaml import YAML, yaml_object
from ruamel.yaml.comments import CommentedMap

yaml = YAML()


class AttrYamlMixin:
    @classmethod
    def from_yaml(cls, constructor, node):
        state = CommentedMap()
        constructor.construct_mapping(node, state)
        return cls(**state)
