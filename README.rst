---------------
OBS Overlay Web
---------------

Setup
=====

1. symlink or copy etc/runner-example-production.json to etc/runner.json, that
   will be our main configuration file.

2. ./run setup


Usage
=====

1. ./run python-project --project=example_project
2. Open OBS Studio
3. add browser source: http://localhost:8282/
4. add custom browser dock: http://localhost:8282/controller/
