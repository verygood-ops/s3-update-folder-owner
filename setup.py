#!/usr/bin/env python3

from setuptools import setup

setup(
    name='S3 Update Folder Owner script',
    version='1.0',
    description='A script for recursive chown of S3 bucket objects',
    author='Very Good Security, Inc.',
    author_email='dev@verygoodsecurity.com',
    scripts=['bin/s3-update-folder-owner.py'],
    python_requires='>=3.7',
    install_requires=['boto3>=1.14.60']
)
