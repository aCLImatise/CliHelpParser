from declivity.parser import Command
from declivity import cli_types
from declivity.converter import WrapperGenerator
import cwlgen
from io import StringIO
import tempfile


class CwlGenerator(WrapperGenerator):
    @staticmethod
    def snake_case(words: list):
        return '_'.join([word.lower() for word in words])

    @staticmethod
    def to_cwl_type(typ: cli_types.CliType):
        if isinstance(typ, cli_types.CliFile):
            return 'File'
        elif isinstance(typ, cli_types.CliDir):
            return 'Directory'
        elif isinstance(typ, cli_types.CliString):
            return 'string'
        elif isinstance(typ, cli_types.CliFloat):
            return 'double'
        elif isinstance(typ, cli_types.CliInteger):
            return 'long'
        elif isinstance(typ, cli_types.CliBoolean):
            return 'boolean'
        elif isinstance(typ, cli_types.CliEnum):
            return 'string'
        elif isinstance(typ, cli_types.CliList):
            return CwlGenerator.to_cwl_type(typ.value) + '[]'
        elif isinstance(typ, cli_types.CliTuple):
            return list(set(typ.values))
        else:
            raise Exception('Invalid type!')

    def generate_wrapper(self, cmd: Command) -> str:
        cwl_tool = cwlgen.CommandLineTool(
            tool_id=self.snake_case(cmd.command),
            base_command=cmd.command,
            cwl_version='v1.0'
        )

        for pos in cmd.positional:
            cwl_tool.inputs.append(cwlgen.CommandInputParameter(
                param_id=self.choose_variable_name(pos, format='snake'),
                param_type=self.to_cwl_type(pos.get_type()),
                input_binding=cwlgen.CommandLineBinding(
                    position=pos.position
                ),
                doc=pos.description
            ))

        for flag in cmd.named:
            cwl_tool.inputs.append(cwlgen.CommandInputParameter(
                param_id=self.choose_variable_name(flag, format='snake'),
                param_type=self.to_cwl_type(flag.args.get_type()),
                input_binding=cwlgen.CommandLineBinding(
                    prefix=flag.longest_synonym
                ),
                doc=flag.description,

            ))

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as temp:
            cwl_tool.export(temp.name)
            return temp.read()
