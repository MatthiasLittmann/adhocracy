""" Automatically log in an invited user """

import urlparse
import re

import adhocracy.model as model
from adhocracy.lib.auth.authorization import has

from paste.deploy.converters import asbool
import pylons
from repoze.who.interfaces import IAuthenticator, IIdentifier
from webob.exc import HTTPFound
from zope.interface import implements


def welcome_url(user, code):
    from adhocracy.lib.helpers import base_url
    return base_url("/welcome/%s/%s" % (user.user_name, code),
                    absolute=True)


def welcome_enabled(config=pylons.config):
    return asbool(config.get('adhocracy.enable_welcome', 'False'))


def can_welcome():
    """ Can the current user set welcome codes? """
    return welcome_enabled() and has('global.admin')


class WelcomeRepozeWho(object):
    implements(IAuthenticator, IIdentifier)

    def __init__(self, config, rememberer_name, prefix='/welcome/'):
        self.config = config
        self.rememberer_name = rememberer_name
        self.url_rex = re.compile(r'^' + re.escape(prefix) +
                                  r'(?P<id>[^/]+)/(?P<code>[^/]+)$')

    def identify(self, environ):
        path_info = environ['PATH_INFO']
        m = self.url_rex.match(path_info)
        if not m:
            return None
        u = model.User.find(m.group('id'))
        if not u:
            return None
        is_correct = False
        if u.welcome_code:
            if u.welcome_code == m.group('code'):
                is_correct = True
        if not is_correct and (
                u.reset_code and u.reset_code.startswith(u'welcome!')):
            correct_code = u.reset_code.partition(u'welcome!')[2]
            if m.group('code') == correct_code:
                # At this point, we're sure the user really wanted to reset her
                # password, so set the actual welcome code.
                u.welcome_code = correct_code
                u.reset_code = None
                model.meta.Session.add(u)
                model.meta.Session.commit()
                is_correct = True
        if not is_correct:
            return None

        qs = urlparse.parse_qs(environ['QUERY_STRING'])
        if 'came_from' in qs:
            redirect_url = qs['came_from'][0]
        else:
            from adhocracy.lib.helpers import base_url
            redirect_url = base_url('/', instance=None, config=self.config)
        environ['repoze.who.application'] = HTTPFound(location=redirect_url)

        return {
            'repoze.who.plugins.welcome.userid': u.user_name,
        }

    def forget(self, environ, identity):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer.forget(environ, identity)

    def remember(self, environ, identity):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer.remember(environ, identity)

    def authenticate(self, environ, identity):
        userid = identity.get('repoze.who.plugins.welcome.userid')
        if userid is None:
            return None
        identity['repoze.who.userid'] = userid
        return userid


def setup_auth(config, identifiers, authenticators):
    if not welcome_enabled(config):
        return

    welcome_rwho = WelcomeRepozeWho(config, 'auth_tkt')
    identifiers.append(('welcome', welcome_rwho))
    authenticators.append(('welcome', welcome_rwho))
