import textwrap
from typing import Any, Dict, Type

from cattr.converters import Converter
from gherkin.errors import ParserError
from gherkin.parser import Parser

from .ast_node.gherkin_document import GherkinDocument
from .errors import DeserializeError, InvalidInput
from .utils import camel_to_snake_case, remove_trailing_spaces


class CustomConverter(Converter):
    def structure_attrs_fromdict(self, obj: Dict[str, Any], cls: Type) -> Any:
        # Make sure the type in the parsed object matches the class we use
        # to structure the object
        if "type" in obj:
            type_name = obj.pop("type")
            cls_name = cls.__name__
            assert type_name == cls_name, f"{type_name} does not match {cls_name}"

        # Note that keys are in camelCase convention, for example, tableHeader,
        # tableBody. Therefore, we need to convert the keys to snake_case.
        transformed_obj = {}
        for key, value in obj.items():
            if isinstance(value, str):
                # For some types of node, the indentation of the lines is included
                # in the value of such nodes. Then the indentation can be changed after
                # formatting. Therefore, we need to dedent the value here for consistent
                # results. We also need to remove trailing spaces.
                value = remove_trailing_spaces(value)
                value = textwrap.dedent(value)

            transformed_obj[camel_to_snake_case(key)] = value

        return super(CustomConverter, self).structure_attrs_fromdict(
            transformed_obj, cls
        )


converter = CustomConverter()


class KryptonParser(Parser):
    # This method is monkeypatched to allow for "rogue" Examples tables
    # to be considered "other". The tool will then treat feature examples tables
    # as part of the feature description.
    # It isn't the greatest workaround, but it let's us use the tool with pytest-bdd.
    def match_Other(self, context, token):
        if token.eof():
            return False
        return self.handle_external_error(
            context, False, token, context.token_matcher.match_Other
        ) or self.handle_external_error(
            context, False, token, context.token_matcher.match_ExamplesLine
        )


def parse(content: str) -> GherkinDocument:
    """
    Parse the content of a file to an AST.
    """
    parser = KryptonParser()

    try:
        parse_result = parser.parse(content)
    except ParserError as e:
        raise InvalidInput(e) from e

    try:
        result = converter.structure(parse_result, GherkinDocument)
    except Exception as e:
        raise DeserializeError(f"{type(e).__name__}: {e}") from e

    return result
