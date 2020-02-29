#!/usr/bin/env python

from distutils.core import setup

setup(
    install_requires=[
        "certifi==2019.11.28",
        "chardet==3.0.4",
        "fake-useragent==0.1.11",
        "idna==2.9",
        "lxml==4.5.0",
        "requests==2.23.0",
        "requests-toolbelt==0.9.1",
        "urllib3==1.25.8",
    ],
    name="github-issue-attachment-uploader",
    version="1.0",
    description="A tool to upload images/files from the command line and generate a direct link without having to create issues on the website. Useful for generating asset links on the go.",
    author="idealwebsolutions",
    url="https://github.com/idealwebsolutions/github-issue-attachment-uploader",
    scripts=['bin/upload-attachment'],
    py_modules=['github.upload']
)
