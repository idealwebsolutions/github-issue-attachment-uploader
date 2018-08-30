# github-issues-attachment-uploader
A tool to upload images/files from the command line and generate a direct link without having to create issues on the website

# Install
Project uses pipenv to install deps. Tool requires Python 3.6+.

    $ git clone https://github.com/idealwebsolutions/github-issue-attachment-uploader.git
    $ pipenv install

# Usage

    $ pipenv shell
    $ python cli.py <path/to/file> [--repository <name>] [--debug]

First time usage will request user credentials (only username and default repository is stored) to save for future uses (saved in HOME directory as `.gh_upload_attachment`). Passwords will be requested per usage and are not saved/stored ever.

# Why
Wanted an easy way to upload and use screenshots on my README files without having to use a third party platform or commit the file to my repo. This method is primarily used for issues/pr/comments, but this tool allows you to use it for more than those use cases.

# Support
[Check out the official support article here](https://help.github.com/articles/file-attachments-on-issues-and-pull-requests)

# License
MIT
