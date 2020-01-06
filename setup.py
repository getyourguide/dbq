from setuptools import find_packages, setup

setup(
    name='dbq',
    version='0.9.0',
    author='GetYourGuide GmbH',
    description='Run a query on Databricks',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='Apache License, Version 2.0',
    license_file='LICENSE',
    url='https://github.com/getyourguide/dbq',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'databricks-dbapi',
        'tabulate',
    ],
    entry_points={
        'console_scripts': [
            'dbq = dbq.main:run',
        ],
    },
)
