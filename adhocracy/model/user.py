import hashlib
import os
import logging
from datetime import datetime

from sqlalchemy import Table, Column, Integer, Unicode, UnicodeText, Boolean, DateTime, func, or_

from babel import Locale

import meta
import filter as ifilter
import group

log = logging.getLogger(__name__)

user_table = Table('user', meta.data,
    Column('id', Integer, primary_key=True),
    Column('user_name', Unicode(255), nullable=False, unique=True, index=True),
    Column('display_name', Unicode(255), nullable=True, index=True),
    Column('bio', UnicodeText(), nullable=True),
    Column('email', Unicode(255), nullable=True, unique=False),
    Column('email_priority', Integer, default=3),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('reset_code', Unicode(255), nullable=True, unique=False),
    Column('password', Unicode(80), nullable=False),
    Column('locale', Unicode(7), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime)
    )

class User(object):
    
    def __init__(self, user_name, email, password, locale, display_name=None, bio=None):
        self.user_name = user_name
        self.email = email
        self.password = password
        self.locale = locale
        self.display_name = display_name
        self.bio = bio
           
    def _get_name(self):
        return self.display_name.strip() \
            if self.display_name and len(self.display_name.strip()) > 0 \
            else self.user_name
    
    name = property(_get_name)
    
    def _get_locale(self):
        if not self._locale:
            return None
        return Locale.parse(self._locale)
    
    def _set_locale(self, locale):
        self._locale = unicode(locale)
        
    locale = property(_get_locale, _set_locale)
        
    def _get_email(self):
        return self._email
    
    def _set_email(self, email):
        import adhocracy.lib.util as util 
        if not self._email == email:
            self.activation_code = util.random_token()
        self._email = email
        
    email = property(_get_email, _set_email)
    
    def _get_email_hash(self):
        return hashlib.sha1(self.email).hexdigest()
    
    email_hash = property(_get_email_hash)
    
    def _get_context_groups(self):
        groups = []
        for membership in self.memberships: 
            if membership.is_expired():
                continue
            if not membership.instance or \
                membership.instance == ifilter.get_instance():
                groups.append(membership.group)
        return groups
     
    groups = property(_get_context_groups)
    
    def _has_permission(self, permission_name):
        for group in self.groups:
            for perm in group.permissions:
                if perm.permission_name == permission_name:
                    return True
        return False
    
    def is_member(self, instance):
        for membership in self.memberships:
            if (not membership.is_expired()) and \
                membership.instance == instance:
                return True
        return False
    
    def _get_instances(self):
        instances = []
        for membership in self.memberships:
            if (not membership.is_expired()) and \
                (membership.instance is not None):
                instances.append(membership.instance)
        return list(set(instances))
    
    instances = property(_get_instances)
    
    def _get_twitter(self):
        for twitter in self.twitters:
            if not twitter.is_deleted():
                return twitter
        return None
    
    twitter = property(_get_twitter)
    
    def _set_password(self, password):
        """Hash password on the fly."""
        
        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password
        
        salt = hashlib.sha1(os.urandom(60))
        hash = hashlib.sha1(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()
        
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')
        
        self._password = hashed_password
    
    def _get_password(self):
        """Return the password hashed"""
        return self._password
    
    def validate_password(self, password):
        """
        Check the password against existing credentials.
        
        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool
        """
        hashed_pass = hashlib.sha1(password + self.password[:40])
        return self.password[40:] == hashed_pass.hexdigest()
    
    password = property(_get_password, _set_password)
    
    def current_agencies(self, instance_filter=True):
        ds = filter(lambda d: not d.is_revoked(), self.agencies)
        if ifilter.has_instance() and instance_filter:
            ds = filter(lambda d: d.scope.instance == ifilter.get_instance(), ds)
        return ds
    
    def current_delegated(self, instance_filter=True):
        ds = filter(lambda d: not d.is_revoked(), self.delegated)
        if ifilter.has_instance() and instance_filter:
            ds = filter(lambda d: d.scope.instance == ifilter.get_instance(), ds)
        return ds
    
    @classmethod
    def complete(cls, prefix, limit=5, instance_filter=True):
        q = meta.Session.query(User)
        prefix = prefix.lower()
        q = q.filter(or_(func.lower(User.user_name).like(prefix + "%"),
                         func.lower(User.display_name).like(prefix + "%")))
        q = q.limit(limit)
        completions = q.all()
        if ifilter.has_instance() and instance_filter:
            inst = ifilter.get_instance()
            completions = filter(lambda u: u.is_member(inst), completions)
        return completions 
    
    @classmethod
    def find(cls, user_name, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(User)
            try:
                q = q.filter(User.id==int(user_name))
            except ValueError:
                q = q.filter(User.user_name==unicode(user_name))
            if not include_deleted:
                q = q.filter(or_(User.delete_time==None,
                                 User.delete_time>datetime.utcnow()))
            user = q.limit(1).first()
            if ifilter.has_instance() and instance_filter:
                user = user.is_member(ifilter.get_instance()) and user or None
            return user
        except Exception, e: 
            log.warn("find(%s): %s" % (user_name, e))
            return None
    
    @classmethod
    def find_by_email(cls, email):
        try:
            q = meta.Session.query(User)
            q = q.filter(User.email==unicode(email).lower())
            return q.limit(1).first()
        except Exception, e: 
            log.warn("find_by_email(%s): %s" % (email, e))
            return None
    
    def _index_id(self):
        return self.user_name
    
    @classmethod
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(User)
        if not include_deleted:
            q = q.filter(or_(User.delete_time==None,
                             User.delete_time>datetime.utcnow()))
        users = q.all()
        if instance is not None:
            users = filter(lambda user: user.is_member(instance), 
                           users)
        return users
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    
    def revoke_delegations(self, instance=None):
        from delegation import Delegation
        q = meta.Session.query(Delegation)
        q = q.filter(or_(Delegation.agent==self,
                         Delegation.principal==self))
        q = q.filter(or_(Delegation.revoke_time == None,
                         Delegation.revoke_time > datetime.utcnow()))
        for delegation in q:
            if instance is None or delegation.scope.instance == instance:
                delegation.revoke()
        
               
    def is_email_activated(self):
        return self.email is not None and self.activation_code is None
    
    
    def delegation_node(self, scope):
        from adhocracy.lib.democracy import DelegationNode
        return DelegationNode(self, scope)
    
    
    def number_of_votes_in_scope(self, scope):
        """
        May be a bit too much as multiple delegations are counted for each user
        they are delegated to. (This is the safety net delegation)
        """
        return self.delegation_node(scope).number_of_delegations() + 1
    
    
    def delegate_to_user_in_scope(self, target_user, scope):
        from adhocracy.lib.democracy import DelegationNode
        return DelegationNode.create_delegation(from_user=self, to_user=target_user, scope=scope)
    
    
    # REFACT: rename: orientation doesn't really ring a bell. decision seems better but isn't
    def vote_for_proposal(self, proposal, orientation):
        # REFACT: proposals don't automatically have a poll - this is dangeorus
        from adhocracy.lib.democracy.decision import Decision
        return Decision(self, proposal.poll).make(orientation)
    
    
    @classmethod
    def create(cls, user_name, email, password=None, locale=None, 
               openid_identity=None, global_admin=False):
        from group import Group
        from membership import Membership
        from openid import OpenID
        
        import adhocracy.lib.util as util
        if password is None:
            password = util.random_token()
        
        import adhocracy.lib.text.i18n as i18n
        if locale is None: 
            locale = i18n.DEFAULT
        
        user = User(unicode(user_name), email, 
                    unicode(password), locale)
        meta.Session.add(user)
        default_group = Group.by_code(Group.CODE_DEFAULT)
        default_membership = Membership(user, None, default_group)
        meta.Session.add(default_membership)
        
        if global_admin:
            admin_group = Group.by_code(Group.CODE_ADMIN)
            admin_membership = Membership(user, None, admin_group)
            meta.Session.add(admin_membership)
        
        if openid_identity is not None:
            openid = OpenID(unicode(openid_identity), user)
            meta.Session.add(openid)
        
        meta.Session.flush()
        return user
    
    
    def to_dict(self):
        d = dict(id=self.id,
                 user_name=self.user_name,
                 locale=self._locale,
                 create_time=self.create_time,
                 mbox=self.email_hash)
        if self.display_name:
            d['display_name'] = self.display_name
        if self.bio:
            d['bio'] = self.bio
        #d['memberships'] = map(lambda m: m.instance.key, 
        #                       self.memberships)
        return d
    
    
    def __repr__(self):
        return u"<User(%s,%s)>" % (self.id, self.user_name)
    

