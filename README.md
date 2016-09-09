# Penfold Pillar Box Application

## Application for secure message dispatching on Ade25 servers

* `Source code @ GitHub <https://github.com/a25kk/penfold>`_
* `Continuous Integration @ Travis-CI <http://travis-ci.org/a25kk/penfold>`_

## Installation

This project is based in the Pyramid web framework and is best used
inside a dedicated virtual environment:

``` bash
$ git clone git@github.com:ade25/penfold.git
$ cd ./penfold
$ virtualenv-3.4 env
$ ./env/bin/pip install -r requirements.txt 
```

## Configuration

The project provides an example development.ini file that you need to
adjust in order to start development. 

``` bash
$ cp development.ini.sample development.ini
```

Please configure a database:

```bash
$ ../env/bin/initialize_PenfoldBox_db development.ini
```


## Development

Initialize the data base and start the development server

```bash
$ ./env/bin/pserve development.ini --reload
```

## Deployment

The buildout generates a fabric push deployment configuration providing several strategies.

### Deploy changes

Update codebase by doing a 'git pull' and restart wsgi client(s)

``` bash
$ fab deploy
```
