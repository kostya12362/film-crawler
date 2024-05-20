from setuptools import setup, find_packages

setup(
    name='api_scrapy',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'aiofiles',
        'uvicorn',
        'aioscrapy',
        'fastapi-async-sqlalchemy',
        'pydantic',
        'sqlalchemy',
        'alembic',
    ],
)