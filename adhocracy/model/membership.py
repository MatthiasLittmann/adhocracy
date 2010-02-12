from datetime import datetime
import logging 

from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime, func, Boolean

import filter as ifilter
import meta
import user

log = logging.getLogger(__name__)


membership_table = Table('membership', meta.data, 
    Column('id', Integer, primary_key=True),
    Column('approved', Boolean, nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('expire_time', DateTime, nullable=True),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False)
    )


class Membership(object):
    
    def __init__(self, user, instance, group, approved=True):
        self.user = user
        self.instance = instance
        self.group = group
        self.approved = approved
        
    def expire(self, expire_time=None):
        if expire_time is None:
            expire_time = datetime.utcnow()
        if not self.is_expired(at_time=expire_time):
            self.expire_time = expire_time
        #if not self.user.is_member(self.instance):
        #    self.user.revoke_delegations(self.instance)
        
    def is_expired(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.expire_time is not None) and \
               self.expire_time<=at_time
    
    def delete(self, delete_time=None):
        return self.expire(expire_time=delete_time)
        
    def is_deleted(self, at_time=None):
        return self.is_expired(at_time=at_time)
        
    def __repr__(self):
        return u"<Membership(%d,%s,%s,%s)>" % (self.id, 
                                               self.user.user_name,
                                               self.instance and self.instance.key or "",
                                               self.group.code)
