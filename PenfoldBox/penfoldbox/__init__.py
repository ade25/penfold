from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    # velruse requires session support
    session_factory = UnencryptedCookieSessionFactoryConfig(
        settings['session.secret'],
    )

    config = Configurator(settings=settings)
    config.set_session_factory(session_factory)
    config.include('pyramid_jinja2')
    config.include('.models')
    config.include('.routes')
    config.include('velruse.providers.github')
    config.add_github_login_from_settings(prefix='velruse.github.')
    config.scan()
    return config.make_wsgi_app()
