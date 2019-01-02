from setuptools import setup

setup(
    install_requires=['flask', 'psycopg2-binary', 'bcrypt', 'pytest', 'turingarena-dev', 'commonmark', 'tabulate',
                      'toml', 'coloredlogs'],
    tests_require=['pytest', 'pytest-flask'],
    setup_requires=['pytest_runner']
)