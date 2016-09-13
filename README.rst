# Penfold Pillar Box

## A message dispatching application

* `Source code @ GitHub <https://github.com/ade25/penfold>`_
* `Releases @ PyPI <http://pypi.python.org/pypi/penfold>`_
* `Documentation @ ReadTheDocs <http://penfold.readthedocs.org>`_
* `Continuous Integration @ Travis-CI <http://travis-ci.org/a25kk/penfold>`_

## How it works

This project templates provides a full blown Django project environment. It comes
with a Django project located unter the src directory

## Installation

This buildout is intended to be used via the development profile to provide
a ready to work on setup. To get started with a new development environment
clone the buildout to your local machine and initialize the buildout:

``` bash
$ git clone git@github.com:ade25/penfold.git
$ cd ./penfold
$ virtualenv-3.4 .
$ ./bin/pip install zc.buildout
$ bin/buildout -Nc development.cfg
```

## Configuration

The generated buildout asumes that the developer has setup a local egg cache and therefore provides a buildout 'default.cfg' containing:

``` ini
[buildout]
eggs-directory      = /home/yourusername/.buildout/eggs
download-cache      = /home/yourusername/.buildout/downloads
extends-cache       = /home/yourusername/.buildout/extends

socket-timeout      = 3

[fabric]
username            = yourusername
```
