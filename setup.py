#!/usr/bin/env python
# coding: utf8

import os

from setuptools import setup

# if there's a converted readme, use it, otherwise fall back to markdown
if os.path.exists('README.rst'):
    readme_path = 'README.rst'
else:
    readme_path = 'README.md'

# avoid importing the module
__version__ = None
exec(open('shoptools/_version.py').read())

setup(
    name='django-shoptools',
    version=__version__,
    description='Another Django eCommerce library',
    long_description=open(readme_path).read(),
    author='Greg Brown',
    author_email='greg@sons.co.nz',
    url='https://github.com/sonsandco/django-shoptools',
    packages=['shoptools'],
    license='BSD License',
    zip_safe=False,
    platforms='any',
    python_requires='>=3.4',
    install_requires=['Django>=1.8', 'django-countries>=4.0'],
    include_package_data=True,
    package_data={},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Framework :: Django',
    ],
)
