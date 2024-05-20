import re


def transform_upper_snake_case(name: str) -> str:
    """
    Converts the exception name from CamelCase to UPPER_SNAKE_CASE.

     :param name: Exception name in CamelCase format.
     :return: Exception name in the format UPPER_SNAKE_CASE.
     """
    # Use a regular expression to add underscores before capital letters, except the first one
    snake_case_name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()
    return snake_case_name
