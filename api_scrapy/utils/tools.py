import re
import os
import importlib
from uuid import UUID
from typing import Type

from aioscrapy import Spider, Crawler

from ..settings import config


def transform_upper_snake_case(name: str) -> str:
    """
    Converts the exception name from CamelCase to UPPER_SNAKE_CASE.

     :param name: Exception name in CamelCase format.
     :return: Exception name in the format UPPER_SNAKE_CASE.
     """
    # Use a regular expression to add underscores before capital letters, except the first one
    snake_case_name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()
    return snake_case_name


def load_all_spiders() -> dict[str, Type[Spider] | Crawler | str]:
    spiders = dict()
    for root, _, files in os.walk(config.BASE_DIR):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                module_path = str(os.path.join(root, file))
                module_name = os.path.relpath(module_path, config.BASE_DIR).replace(os.path.sep, '.')[:-3]
                if 'api_scrapy' in module_name:
                    continue
                try:
                    module = importlib.import_module(module_name)
                    for attr in dir(module):
                        obj = getattr(module, attr)
                        if isinstance(obj, type) and issubclass(obj, Spider) and obj.__module__ == module.__name__:
                            if obj.name in spiders.keys():
                                raise ValueError(f"Spider with name {obj.name} already exists if {module_name}")
                            spiders[obj.name] = obj
                except ImportError:
                    continue
    return spiders


def get_log_file_path(spider_name: str, instance_id: UUID) -> str:
    log_dir = os.path.join(config.log_dir, spider_name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    filename = f"{str(instance_id)}.log"
    return os.path.join(log_dir, filename)


def structure_stats(stats: dict) -> dict[str, dict]:
    structured_stats = {}
    for key, value in stats.items():
        parts = key.split('/')
        d = structured_stats
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return structured_stats
