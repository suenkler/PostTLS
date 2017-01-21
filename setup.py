import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="posttls",
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    license="AGPLv3",
    description="Postfix' Transport Encryption under Control of the User",
    long_description=README,
    url="https://posttls.com/",
    author="Hendrik Suenkler",
    author_email="hendrik@posttls.com",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 1.8",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: AGPLv3",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
