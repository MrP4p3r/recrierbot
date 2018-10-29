import os
from setuptools import setup, find_packages


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


setup(
    name='recrierbot',
    version='2.0.15',
    packages=find_packages(),
    python_requires='>=3.7.0',
    install_requires=[
        'aiohttp',
        'aiosocksy',
        'sqlalchemy-aio',
        'sqlalchemy',
        'aiogram==1.4',
        'emoji',
        'jinja2',
    ],
    entry_points={
        'console_scripts': [
            'recrierbot_server = recrierbot.__main__:main',
        ],
    },
    package_data={'': package_files('recrierbot/handlers/templates/templates')},
)
