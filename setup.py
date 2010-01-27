# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010, 2degrees Limited <gustavonarea@2degreesnetwork.com>.
# All Rights Reserved.
#
# This file is part of twod.wsgi <http://bitbucket.org/Gustavo/twod.wsgi/>,
# which is subject to the provisions of the BSD at
# <http://bitbucket.org/Gustavo/twod.wsgi/src/tip/LICENSE>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.txt")).read()
version = open(os.path.join(here, "VERSION.txt")).readline().rstrip()

setup(name="twod.wsgi",
      version=version,
      description="Enhanced WSGI support for Django applications",
      long_description=README,
      classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Paste",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
        ],
      keywords="django wsgi paste web",
      author="Gustavo Narea",
      author_email="gustavonarea@2degreesnetwork.com",
      namespace_packages = ["twod"],
      url="http://bitbucket.org/Gustavo/twod.wsgi/",
      license="BSD (http://bitbucket.org/Gustavo/twod.wsgi/src/tip/LICENSE)",
      packages=find_packages(exclude=["tests"]),
      package_data={
        '': ["VERSION.txt", "README.txt"],
        'docs': ["Makefile", "source/*"]},
      exclude_package_data={"": ["README.txt", "docs"]},
      include_package_data=True,
      zip_safe=False,
      tests_require = [
        "nose",
        "coverage",
        ],
      install_requires=[
        "Django >= 1.1",
        "WebOb >= 0.9.7",
        "PasteDeploy >= 1.3.3",
        "setuptools",
        ],
      test_suite="nose.collector",
      entry_points = """\
        [paste.app_factory]
        main = twod.wsgi.appsetup:wsgify_django
      """
      )
