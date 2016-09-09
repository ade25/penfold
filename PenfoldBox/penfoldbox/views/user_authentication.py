# -*- coding: utf-8 -*-
"""Module providing velruse authentication views"""
from pyramid.view import view_config

from velruse import login_url


@view_config(
    name='login',
    renderer='penfoldbox:templates/login.jinja2',
)
def login_view(request):
    return {
        'login_url': login_url,
    }


@view_config(
    context='velruse.providers.facebook.GithubAuthenticationComplete',
    renderer='penfoldbox:templates/result.jinja2',
)
def github_login_complete_view(request):
    pass


@view_config(
    context='velruse.AuthenticationDenied',
    renderer='myapp:templates/result.mako',
)
def login_denied_view(request):
    return {
        'result': 'denied',
}
