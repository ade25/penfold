from fabric import api as fab
from functools import wraps
import os, re


#########################################################################################################
# Init / Settings

# Set the working directory to the build/ directory. This is necessary if you
# run "fab ..." in a subdirectory or with "fab ... -f build/fabfile.py"
BUILD_PATH = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
os.chdir(BUILD_PATH)

fab.env.use_ssh_config = True
fab.env.forward_agent = True

#########################################################################################################
# Utils

def _env_path():
    return os.path.realpath(os.path.join(BUILD_PATH, '..', 'env'))


def _env_bin(executable):
    return os.path.join(_env_path(), 'bin', executable)


def _env_choose_bin(*executables):
    for executable in executables:
        path = _env_bin(executable)
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    raise ValueError(
        'There is none of the given executables available in the '
        'virtualenv: {0}.'.format(', '.join(executables)))


def _env_python_bin():
    return _env_choose_bin('python2', 'python')


def _env_pip_bin():
    return _env_choose_bin('pip2', 'pip')


def _web_path():
    return os.path.realpath(os.path.join(BUILD_PATH, '..', 'web'))


def _docs_path():
    return os.path.realpath(os.path.join(BUILD_PATH, '..', 'docs'))


def _goto_web(func):
    @wraps(func)
    def goto_func(*args, **kwargs):
        with fab.lcd(_web_path()):
            return func(*args, **kwargs)
    return goto_func


def _goto_docs(func):
    @wraps(func)
    def goto_func(*args, **kwargs):
        with fab.lcd(_docs_path()):
            return func(*args, **kwargs)
    return goto_func


def _project_name():
    return os.path.basename(_project_path())


def _project_path():
    for dir in os.listdir(_web_path()):
        fulldir = os.path.join(_web_path(), dir)
        if os.path.isdir(fulldir):
            if os.path.exists(os.path.join(fulldir, 'manage.py')):  # older Django installs
                return fulldir
            if os.path.exists(os.path.join(fulldir, 'wsgi.py')):  # newer Django installs
                return fulldir
    raise RuntimeError('Could not find project path')


def _create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


def _static_path():
    return os.path.realpath(os.path.join(_web_path(), 'static'))


def _scss_path():
    return os.path.realpath(os.path.join(_static_path(), 'scss'))


def _app_static_paths():
    for dir, dirnames, filenames in os.walk(_project_path()):
        for dirname in dirnames:
            if dirname == 'static':
                yield os.path.join(dir, dirname)


def _app_scss_paths():
    for static_path in _app_static_paths():
        for dir, dirnames, filenames in os.walk(static_path):
            for dirname in dirnames:
                if dirname == 'scss':
                    scss_path = os.path.join(dir, dirname)
                    yield scss_path


def _merge_dict(defaults, options=None):
    if options is None:
        return defaults
    result = defaults.copy()
    result.update(options)
    return result


@_goto_web
def _run_django_manage_command(command, args=None, kwargs=None):
    params = []
    if kwargs:
        for k, v in kwargs.iteritems():
            if v in ('True', 'true', 'y', 'yes'):
                v = True
            if v is True:
                if len(k) == 1:
                    params.append('-%s' % k)
                else:
                    params.append('--%s' % k)
            else:
                if len(k) == 1:
                    params.append('-%s %s' % (k, v))
                else:
                    params.append('--%s=%s' % (k, v))
    if isinstance(args, (list, tuple)):
        params += args
    elif args is not None:
        params.append(args)
    fab.local('%s manage.py %s %s' % (
        _env_python_bin(),
        command,
        ' '.join(params),
    ))


def _filtered_files(paths, pattern):
    if not isinstance(paths, (list, tuple)):
        paths = [paths]
    for path in paths:
        for dir, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dir, filename)
                if pattern.match(filepath):
                    yield filepath


def _execute_watch(paths, func, **event_handler_kwargs):
    from watchdog.observers import Observer
    from watchdog.events import RegexMatchingEventHandler
    import time

    class FuncEventHandler(RegexMatchingEventHandler):
        def on_any_event(self, event):
            func(event)

    if not isinstance(paths, (list, tuple)):
        paths = [paths]
    event_handler = FuncEventHandler(**event_handler_kwargs)
    observer = Observer()
    for path in paths:
        observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def _execute_bg(func):
    from multiprocessing import Process

    bg_process = Process(target=func)
    bg_process.start()


#########################################################################################################
# Tasks


# Setup / Install

@fab.task
def env():
    fab.local('virtualenv-3.4 %s' % _env_path())


@fab.task
def install():
    fab.local('%s install -Ur PYTHON_REQUIREMENTS' % _env_pip_bin())


@fab.task
def freeze():
    fab.local('%s freeze -r PYTHON_REQUIREMENTS > PYTHON_REQUIREMENTS.new' % _env_pip_bin())
    fab.local('mv -f PYTHON_REQUIREMENTS.new PYTHON_REQUIREMENTS')


@fab.task
def install_js():
    fab.local('npm install')


@fab.task
def setup():
    fab.execute(env)
    fab.execute(install)
    fab.execute(install_js)


# Asset management (CSS / JS)

@fab.task
def css():
    for filepath in _filtered_files([_scss_path()] + list(_app_scss_paths()), re.compile('.*/[^_/][^/]*\.scss$')):
        output_filepath = filepath.replace('scss', 'css')
        _create_path(os.path.dirname(output_filepath))
        fab.local('sassc -lm %s %s' % (filepath, output_filepath))


@fab.task
@_goto_docs
def docs():
    for filepath in _filtered_files(_docs_path(), re.compile('.*/[^_/][^/]*\.rst$')):
        fab.local('make html')


@fab.task
@_goto_web
def watch():
    def handle_event(event):
        with fab.settings(warn_only=True):
            fab.execute(css)

    fab.execute(css)
    _execute_watch(
        [_scss_path()] + list(_app_scss_paths()),
        handle_event,
        regexes=['^.*\.(scss)$'],
        ignore_directories=True,
        )

@fab.task
def gulp():
    fab.local('gulp')


@fab.task
@_goto_web
def watch_docs():
    def handle_event(event):
        with fab.settings(warn_only=True):
            fab.execute(docs)

    fab.execute(docs)
    _execute_watch(
        [_docs_path()],
        handle_event,
        regexes=['^.*\.(rst)$'],
        ignore_directories=True,
    )


@fab.task
def static(*args, **kwargs):
    fab.execute(css)
    _run_django_manage_command('collectstatic', args, kwargs)


# Django commands

@fab.task
def manage(command='help', *args, **kwargs):
    _run_django_manage_command(command, args, kwargs)


@fab.task
def shell(*args, **kwargs):
    _run_django_manage_command('shell_plus', args, kwargs)


@fab.task
def syncdb(*args, **kwargs):
    _run_django_manage_command('syncdb', args, kwargs)


@fab.task
def migrate(*args, **kwargs):
    _run_django_manage_command('migrate', args, kwargs)


@fab.task
def run(*args, **kwargs):
    if not args:
        args = ['0.0.0.0:8000']
    _run_django_manage_command('runserver', args, kwargs)


@fab.task
def rundev(*args, **kwargs):
    _execute_bg(lambda: fab.execute(watch))
    fab.execute(run, *args, **kwargs)


@fab.task
def makemessages(*args, **kwargs):
    # raise Exception("I'm sorry, I'm so so sorry")
    args = list(args)
    args.append('-a')
    # args.append('-i')
    # args.append("'models.py'")
    args.append('-i')
    args.append("'admin.py'")
    # args.append('-i')
    # args.append("'backend.py'")
    # args.append('-i')
    # args.append("'*utils/*'")
    # args.append('-i')
    # args.append("'*utils/*/*'")
    _run_django_manage_command('makemessages', args, kwargs)


@fab.task
def compilemessages(*args, **kwargs):
    _run_django_manage_command('compilemessages', args, kwargs)


# Deployment

def _deploy_git_factory():
    import fabdeploit

    class GitFilter(fabdeploit.GitFilter):
        def filter(self):
            for obj in self.filtered_tree:
                if obj.path not in ('web', 'build', 'serverboot', 'serverconfig'):
                    self.remove(obj.name)

            fab.execute(css)
            # TODO: Automatically find all CSS files necessary to deployment
            for filename in (
                    'web/static/css/main.css',
                    'web/static/css/email.css',
                    'web/static/css/override_backend.css',
            ):
                if os.path.exists(os.path.join(self.repo.working_tree_dir, filename)):
                    self.add(filename)
                else:
                    raise RuntimeError('File %s does not exist?' % filename)

    class Git(fabdeploit.Git):
        local_repository_path = os.path.dirname(BUILD_PATH)
        # remote_repository_path = None
        release_author = 'Team23 GmbH & Co. KG <info@team23.de>'
        # release_branch = None
        release_commit_filter_class = GitFilter

    return Git


def _deploy_virtualenv_factory(_git):
    import fabdeploit

    class Virtualenv(fabdeploit.Virtualenv2):
        virtualenv_path = '%s/env' % _git.remote_repository_path
        requirements_file = '%s/build/PYTHON_REQUIREMENTS' % _git.remote_repository_path

    return Virtualenv


def _deploy_django_factory(_git):
    import fabdeploit

    class Django(fabdeploit.Django):
        manage_path = '%s/web/manage.py' % _git.remote_repository_path

    return Django


def _deploy_base_env():
    fab.require('git')

    fab.env.use_ssh_config = True
    fab.env.virtualenv = _deploy_virtualenv_factory(fab.env.git)()
    fab.env.django = _deploy_django_factory(fab.env.git)(fab.env.virtualenv)


@fab.task
def production():
    fab.env.git = _deploy_git_factory()(
        remote_repository_path='/opt/penfold/production',
        release_branch='production',
    )

    fab.env.hosts = ['s1']
    fab.env.deploy_initscript = '/opt/webserver/buildout.webserver/supervisorctl'
    _deploy_base_env()


@fab.task
def staging():
    fab.env.git = _deploy_git_factory()(
        remote_repository_path='/home/penfold/staging',
        release_branch='staging',
    )

    fab.env.hosts = ['s1']
    fab.env.deploy_initscript = '/opt/webserver/buildout.webserver/supervisorctl'
    _deploy_base_env()


@fab.task
def deploy_push_files():
    fab.require('git')

    fab.env.git.pull()
    fab.env.git.create_release_commit()
    fab.env.git.push()


@fab.task
def deploy_apply_files():
    fab.require('git')

    fab.env.git.switch_release()


@fab.task
def deploy_virtualenv_files():
    fab.require('virtualenv')

    fab.env.virtualenv.init()
    fab.env.virtualenv.update()
    if fab.env.git.release_commit:
        fab.env.virtualenv.git.commit(tag='release/%s' % fab.env.git.release_commit.hexsha)


@fab.task
def deploy_files():
    fab.execute(deploy_push_files)
    fab.execute(deploy_apply_files)
    fab.execute(deploy_virtualenv_files)


@fab.task
def deploy_static():
    fab.require('django')
    fab.env.django.collectstatic()
    fab.env.django.run('assets', 'build')


@fab.task
def deploy_migrate():
    fab.require('django')
    fab.env.django.syncdb()
    fab.env.django.migrate()


@fab.task
def deploy_stop():
    fab.run('%s stop' % fab.env.deploy_initscript)


@fab.task
def deploy_start():
    fab.run('%s start' % fab.env.deploy_initscript)


@fab.task
def deploy_restart():
    fab.run('%s restart' % fab.env.deploy_initscript)


@fab.task
def deploy_status():
    fab.run('%s status' % fab.env.deploy_initscript)


@fab.task
def deploy(*args):
    fab.require('git')

    # prepare
    fab.execute(deploy_push_files)
    # The 'git status' is done so the virtualenv.create_commit later will not need to
    # scan all files first. Scanning files may be bad for performance and we want to
    # keep the downtime to a minimum.
    if 'virtualenv' in fab.env and fab.env.virtualenv.virtualenv_path:
        with fab.cd(fab.env.virtualenv.virtualenv_path):
            fab.run('git status')
    with fab.cd(fab.env.git.remote_repository_path):
        fab.run('git status')
    fab.execute(deploy_stop)

    # run upgrade
    fab.execute(deploy_apply_files)
    if not 'novirtualenv' in args:
        fab.execute(deploy_virtualenv_files)
    elif 'virtualenv' in fab.env:
        fab.env.virtualenv.git.commit(tag='release/%s' % fab.env.git.release_commit.hexsha)
    if not 'nostatic' in args:
        fab.execute(deploy_static)
    if not 'nomigrate' in args:
        fab.execute(deploy_migrate)

    # start server again
    fab.execute(deploy_start)


@fab.task
def deploy_setup(*args):
    fab.execute(deploy_push_files)
    fab.execute(deploy_apply_files)
    fab.execute(deploy_virtualenv_files)
    fab.execute(deploy_static)
    print "-" * 70
    print "Next: Setup the local_settings.py and initialize the database"
    print "-" * 70
