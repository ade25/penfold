import getpass
from fabric.api import task
from fabric.api import cd
from fabric.api import env
from fabric.api import run
from fabric.api import roles

from ade25.fabfiles import project
from ade25.fabfiles.server import controls

from slacker import Slacker
slack = Slacker('xoxp-2440800772-2440800774-18737814324-4f66a898de')

env.use_ssh_config = True
env.forward_agent = True
env.port = '22'
env.user = 'root'
env.hosts = ['z16']
env.hosts_staging = ['z16']
env.hostname = 'z16'
env.hostname_staging = 'z16'
env.webserver = '/opt/webserver/buildout.webserver'
env.code_root = '/opt/sites/penfold/buildout.penfold'
env.local_root = '/Users/cb/dev/penfold'
env.sitename = 'penfold'
env.code_user = 'root'
env.prod_user = 'www'
# Uncomment and add your name here
env.actor = 'Christoph Boehner-Figas'

env.roledefs = {
    'production': ['z16'],
    'staging': ['z3']
}


@task
@roles('staging')
def deploy_staging(actor=None):
    """ Deploy to staging server """
    opts = dict(
        sitename=env.get('sitename'),
        hostname=env.get('hostname_staging'),
        actor=actor or env.get('actor') or getpass.getuser(),
    )
    project.site.update()
    project.site.restart()
    msg = '[%(hostname)s] *%(sitename)s* staged by %(actor)s' % opts
    user = 'fabric'
    icon = ':ship:'
    slack.chat.post_message('#general', msg, username=user, icon_emoji=icon)


@task
@roles('production')
def deploy(actor=None):
    """ Deploy current master to production server """
    opts = dict(
        sitename=env.get('sitename'),
        hostname=env.get('hostname'),
        actor=actor or env.get('actor') or getpass.getuser(),
    )
    project.site.update()
    project.site.restart()
    msg = '[%(hostname)s] *%(sitename)s* deployed by %(actor)s' % opts
    user = 'fabric'
    icon = ':shipit:'
    slack.chat.post_message('#general', msg, username=user, icon_emoji=icon)


@task
@roles('production')
def deploy_full(actor=None):
    """ Deploy current master to production and run buildout """
    opts = dict(
        sitename=env.get('sitename'),
        hostname=env.get('hostname'),
        actor=actor or env.get('actor') or getpass.getuser(),
    )
    project.site.update()
    project.site.build()
    project.site.restart()
    msg = '[%(hostname)s] *%(sitename)s* deployed by %(actor)s' % opts
    user = 'fabric'
    icon = ':shipit:'
    slack.chat.post_message('#general', msg, username=user, icon_emoji=icon)


@task
@roles('production')
def rebuild(actor=None):
    """ Deploy current master to production and force rebuild """
    opts = dict(
        sitename=env.get('sitename'),
        hostname=env.get('hostname'),
        actor=actor or env.get('actor') or getpass.getuser(),
    )
    project.site.update()
    project.site.build_full()
    project.site.restart()
    msg = '[%(hostname)s] *%(sitename)s* rebuild by %(actor)s' % opts
    user = 'fabric'
    icon = ':shipit:'
    slack.chat.post_message('#general', msg, username=user, icon_emoji=icon)


@task
@roles('production')
def develop():
    """ Update development packages under src directory """
    with cd(env.code_root):
        run('nice bin/develop up')


@task
def get_data():
    """ Copy live database for local development """
    project.db.download()


@task
@roles('production')
def ctl(*cmd):
    """Runs an arbitrary supervisorctl command."""
    with cd(env.webserver):
        run('nice bin/supervisorctl ' + ' '.join(cmd))


@task
@roles('staging')
def develop_staging():
    """ Update development eggs """
    with cd(env.code_root):
        run('nice bin/develop up')

@task
@roles('staging')
def restart_nginx():
    """ Restart Nginx """
    controls.restart_nginx()


@task
@roles('staging')
def restart_varnish():
    """ Restart Varnish """
    controls.restart_varnish()
