# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

import socket
import uuid
import json
import mimeparse

import kom
import komauxitems
import version

class KomSessionError(Exception): pass
class AmbiguousName(KomSessionError): pass
class NameNotFound(KomSessionError): pass
class NoRecipients(KomSessionError): pass


MIRecipient_type_to_str = { kom.MIR_TO: 'to',
                            kom.MIR_CC: 'cc',
                            kom.MIR_BCC: 'bcc' }

MIRecipient_str_to_type = { 'to': kom.MIR_TO,
                            'cc': kom.MIR_CC,
                            'bcc': kom.MIR_BCC }

MICommentTo_type_to_str = { kom.MIC_COMMENT: 'comment',
                            kom.MIC_FOOTNOTE: 'footnote' }

MICommentTo_str_to_type = { 'comment': kom.MIC_COMMENT,
                            'footnote': kom.MIC_FOOTNOTE }

MICommentIn_type_to_str = { kom.MIC_COMMENT: 'comment',
                            kom.MIC_FOOTNOTE: 'footnote' }

MICommentIn_str_to_type = { 'comment': kom.MIC_COMMENT,
                            'footnote': kom.MIC_FOOTNOTE }

_ALLOWED_KOMTEXT_AUXITEMS = [
    komauxitems.AI_FAST_REPLY
]


class KomSession(object):
    """ A LysKom session. """
    def __init__(self, host, port=4894):
        self.host = host
        self.port = port
        self.conn = None
        self.session_no = None
        self.client_name = None
        self.client_version = None
        self.pers_no = 0
    
    def connect(self, client_name, client_version):
        httpkom_user = "httpkom%" + socket.getfqdn()
        self.conn = kom.CachedConnection()
        self.conn.connect(self.host, self.port, user=httpkom_user)
        kom.ReqSetClientVersion(self.conn, client_name, client_version)
        self.client_name = client_name
        self.client_version = client_version
        self.session_no = self.who_am_i()
    
    def disconnect(self, session_no=0):
        """Session number 0 means this session (a logged in user can
        disconnect its other sessions).
        """
        kom.ReqDisconnect(self.conn, session_no).response()
        
        # Check if we disconnected our own session
        if session_no == 0 or session_no == self.session_no:
            self.conn.socket.close()
            self.conn = None
            self.client_name = None
            self.client_version = None
            self.session_no = None
    
    def is_connected(self):
        return self.conn is None
    
    def login(self, pers_no, password):
        kom.ReqLogin(self.conn, pers_no, password, invisible=0).response()
        self.pers_no = pers_no
        
    def logout(self):
        kom.ReqLogout(self.conn).response()
        self.pers_no = 0
    
    def who_am_i(self):
        return kom.ReqWhoAmI(self.conn).response()

    def user_is_active(self):
        kom.ReqUserActive(self.conn).response()

    def is_logged_in(self):
        return self.pers_no != 0

    def change_conference(self, conf_no):
        kom.ReqChangeConference(self.conn, conf_no).response()
        
    def create_person(self, name, passwd):
        flags = kom.PersonalFlags()
        pers_no = kom.ReqCreatePerson(
            self.conn, name.encode('latin1'), passwd.encode('latin1'), flags).response()
        return pers_no
    
    def lookup_name(self, name, want_pers, want_confs):
        return self.conn.lookup_name(name, want_pers, want_confs)

    def lookup_name_exact(self, name, want_pers, want_confs):
        matches = self.lookup_name(name, want_pers, want_confs)
        if len(matches) == 0:
            raise NameNotFound("recipient not found: %s" % name)
        elif len(matches) <> 1:
            raise AmbiguousName("ambiguous recipient: %s" % name)
        return matches[0][0]

    def get_text_stat(self, text_no):
        return self.conn.textstats[text_no]
    
    def add_membership(self, pers_no, conf_no, priority, where):
        mtype = kom.MembershipType()
        kom.ReqAddMember(self.conn, conf_no, pers_no, priority, where, mtype).response()
    
    def delete_membership(self, pers_no, conf_no):
        kom.ReqSubMember(self.conn, conf_no, pers_no).response()

    def get_membership(self, pers_no, conf_no, want_unread):
        want_read_ranges = 1 if want_unread else 0
        membership = kom.ReqQueryReadTexts11(
            self.conn, pers_no, conf_no, want_read_ranges, 0).response()
        if want_unread:
            unread_texts = self.conn.get_unread_texts_from_membership(membership)
            no_of_unread = len(unread_texts)
            return KomMembership(membership, no_of_unread, unread_texts)
        else:
            return KomMembership(membership, None, None)
    
    def get_memberships(self, pers_no, unread, want_unread):
        if unread:
            conf_nos = kom.ReqGetUnreadConfs(self.conn, pers_no).response()
        else:
            # http://www.lysator.liu.se/lyskom/protocol/11.1/protocol-a.html#get-membership
            raise NotImplementedError()
        
        memberships = [ self.get_membership(pers_no, conf_no, want_unread)
                        for conf_no in conf_nos ]
        
        if unread:
            # Filter out unread conferences with 0 unread in, can happen
            # for some conferences, like "Ryd, Bastu" (conf_no: 9700).
            return [ membership for membership in memberships
                     if membership.no_of_unread is None or membership.no_of_unread > 0 ]
        else:
            #return memberships
            raise NotImplementedError()        
    
    def get_conf_name(self, conf_no):
        return self.conn.conf_name(conf_no)
    
    def get_conference(self, conf_no, micro=True):
        if micro:
            return KomUConference(conf_no, self.conn.uconferences[conf_no])
        else:
            return KomConference(conf_no, self.conn.conferences[conf_no])

    def get_text(self, text_no):
        text_stat = self.get_text_stat(text_no)
        text = kom.ReqGetText(self.conn, text_no).response()
        return KomText(text_no=text_no, text=text, text_stat=text_stat)
    
    def create_text(self, komtext):
        misc_info = kom.CookedMiscInfo()
        
        if komtext.recipient_list is not None:
            for rec in komtext.recipient_list:
                if rec is not None:
                    misc_info.recipient_list.append(rec)
        
        if komtext.comment_to_list is not None:
            for ct in komtext.comment_to_list:
                if ct is not None:
                    misc_info.comment_to_list.append(ct)
        
        #print misc_info.to_string()
        
        mime_type = mimeparse.parse_mime_type(komtext.content_type)
        # Because a text consists of both a subject and body, and you
        # can have a text subject in combination with an image, a
        # charset is needed to specify the encoding of the subject.
        mime_type[2]['charset'] = 'utf-8'
        content_type = mime_type_tuple_to_str(mime_type)
        
        # TODO: how would this work with images?
        fulltext = str()
        fulltext += komtext.subject.encode('utf-8') + "\n"
        if (mime_type[0] == 'text'):
            fulltext += komtext.body.encode('utf-8')
        else:
            fulltext += komtext.body
        
        aux_items = []
        aux_items.append(kom.AuxItem(kom.AI_CREATING_SOFTWARE,
                                     data="%s %s" % (self.client_name, self.client_version)))
        aux_items.append(kom.AuxItem(kom.AI_CONTENT_TYPE,
                                     data=content_type))
        
        text_no = kom.ReqCreateText(self.conn, fulltext, misc_info, aux_items).response()
        return text_no

    def mark_as_read_local(self, local_text_no, conf_no):
        try:
            kom.ReqMarkAsRead(self.conn, conf_no, [local_text_no]).response()
        except kom.NotMember:
            pass

    def mark_as_unread_local(self, local_text_no, conf_no):
        try:
            kom.ReqMarkAsUnread(self.conn, conf_no, local_text_no).response()
        except kom.NotMember:
            pass
    
    def mark_as_read(self, text_no):
        text_stat = self.get_text_stat(text_no)
        for mi in text_stat.misc_info.recipient_list:
            self.mark_as_read_local(mi.loc_no, mi.recpt)

    def mark_as_unread(self, text_no):
        text_stat = self.get_text_stat(text_no)
        for mi in text_stat.misc_info.recipient_list:
            self.mark_as_unread_local(mi.loc_no, mi.recpt)

    def set_unread(self, conf_no, no_of_unread):
        kom.ReqSetUnread(self.conn, conf_no, no_of_unread).response()

    def get_marks(self):
        return kom.ReqGetMarks(self.conn).response()

    def mark_text(self, text_no, mark_type):
        self.conn.mark_text(text_no, mark_type)

    def unmark_text(self, text_no):
        self.conn.unmark_text(text_no)



class KomMembership(object):
    def __init__(self, membership, no_of_unread, unread_texts=None):
        self.position = membership.position
        self.last_time_read = membership.last_time_read
        self.conference = membership.conference
        self.priority = membership.priority
        self.added_by = membership.added_by
        self.added_at = membership.added_at
        self.type = membership.type
        self.no_of_unread = no_of_unread
        
        if unread_texts:
            self.unread_texts = unread_texts
        else:
            self.unread_texts = None


class KomConference(object):
    def __init__(self, conf_no=None, conf=None):
        self.conf_no = conf_no
        
        if conf is not None:
            self.name = conf.name.decode('latin1')
            self.type = conf.type
            self.creation_time = conf.creation_time
            self.last_written = conf.last_written
            self.creator = conf.creator
            self.presentation = conf.presentation
            self.supervisor = conf.supervisor
            self.permitted_submitters = conf.permitted_submitters
            self.super_conf = conf.super_conf
            self.msg_of_day = conf.msg_of_day
            self.nice = conf.nice
            self.keep_commented = conf.keep_commented
            self.no_of_members = conf.no_of_members
            self.first_local_no = conf.first_local_no
            self.no_of_texts = conf.no_of_texts
            self.expire = conf.expire
            # auxitems?


class KomUConference(object):
    """U stands for micro"""
    def __init__(self, conf_no=None, uconf=None):
        self.conf_no = conf_no
        
        if uconf is not None:
            self.name = uconf.name.decode('latin1')
            self.type = uconf.type
            self.highest_local_no = uconf.highest_local_no
            self.nice = uconf.nice


class KomText(object):
    def __init__(self, text_no=None, text=None, text_stat=None):
        self.text_no = text_no
        
        if text_stat is None:
            self.content_type = None
            self.creation_time = None
            self.author = None
            self.no_of_marks = 0
            self.recipient_list = None
            self.comment_to_list = None
            self.comment_in_list = None
            self.subject = None
            self.body = None
            self.aux_items = None
        else:
            mime_type, encoding = parse_content_type(
                self._get_content_type_from_text_stat(text_stat))
            self.content_type = mime_type_tuple_to_str(mime_type)
            
            self.creation_time = text_stat.creation_time
            self.author = text_stat.author
            self.no_of_marks = text_stat.no_of_marks
            self.recipient_list = text_stat.misc_info.recipient_list
            self.comment_to_list = text_stat.misc_info.comment_to_list
            self.comment_in_list = text_stat.misc_info.comment_in_list
            self.aux_items = text_stat.aux_items
            
            # text_stat is required for this
            if text is not None:
                # If a text has no linefeeds, it only has a body
                if text.find('\n') == -1:
                    self.subject = "" # Should probably be None instead?
                    rawbody = text
                else:
                    rawsubject, rawbody = text.split('\n', 1)
                    # TODO: should we always decode the subject?
                    self.subject = decode_text(rawsubject, encoding)
                
                if mime_type[0] == 'text':
                    # Only decode body if media type is text, and not
                    # an image, for example.  Also, if the subject is
                    # empty, everything becomes the subject, which
                    # will get decoded.  Figure out how to handle all
                    # this. Assume empty subject means everything in
                    # body?
                    self.body = decode_text(rawbody, encoding)
                else:
                    self.body = rawbody
    
    def _get_content_type_from_text_stat(self, text_stat):
        try:
            contenttype = kom.first_aux_items_with_tag(
                text_stat.aux_items, komauxitems.AI_CONTENT_TYPE).data.decode('latin1')
        except AttributeError:
            contenttype = 'text/plain'
        return contenttype
        


def to_dict(obj, lookups=False, session=None):
    if isinstance(obj, list):
        return [ to_dict(el, lookups, session) for el in obj ]
    elif isinstance(obj, KomSession):
        return KomSession_to_dict(obj, lookups, session)
    elif isinstance(obj, KomText):
        return KomText_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.MIRecipient):
        return MIRecipient_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.MICommentTo):
        return MICommentTo_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.MICommentIn):
        return MICommentIn_to_dict(obj, lookups, session)
    elif isinstance(obj, KomConference):
        return KomConference_to_dict(obj, lookups, session)
    elif isinstance(obj, KomUConference):
        return KomUConference_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.ConfType):
        return ConfType_to_dict(obj, lookups, session)
    elif isinstance(obj, KomMembership):
        return KomMembership_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.MembershipType):
        return MembershipType_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.AuxItem):
        return AuxItem_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.Mark):
        return Mark_to_dict(obj, lookups, session)
    else:
        #raise NotImplementedError("to_dict is not implemented for: %s" % type(obj))
        return obj

def from_dict(d, cls, lookups=False, session=None):
    if cls == KomText:
        return KomText_from_dict(d, lookups, session)
    elif cls == kom.MIRecipient:
        return MIRecipient_from_dict(d, lookups, session)
    elif cls == kom.MICommentTo:
        return MICommentTo_from_dict(d, lookups, session)
    elif cls == kom.MICommentIn:
        return MICommentIn_from_dict(d, lookups, session)
    else:
        raise NotImplementedError("from_dict is not implemented for: %s" % cls)

def KomSession_to_dict(ksession, lookups, session):
    person = None
    if ksession.is_logged_in():
        pers_no = ksession.pers_no
        if lookups:
            pers_name = session.get_conf_name(pers_no)
        else:
            pers_name = None
        person = dict(pers_no=pers_no, pers_name=pers_name)
    
    session_no = None
    if lookups:
        session_no = ksession.who_am_i()
    
    return dict(person=person, session_no=session_no)

def KomMembership_to_dict(membership, lookups, session):
    return dict(
        position=membership.position,
        last_time_read=membership.last_time_read.to_date_and_time(),
        conference=conf_to_dict(membership.conference, lookups, session),
        priority=membership.priority,
        added_by=pers_to_dict(membership.added_by, lookups, session),
        added_at=membership.added_at.to_date_and_time(),
        type=to_dict(membership.type, lookups, session),
        no_of_unread=membership.no_of_unread,
        unread_texts=to_dict(membership.unread_texts, lookups, session))

def MembershipType_to_dict(m_type, lookups, session):
    return dict(
        invitation=m_type.invitation,
        passive=m_type.passive,
        secret=m_type.secret,
        passive_message_invert=m_type.passive_message_invert)

def ConfType_to_dict(conf_type, lookups, session):
    return dict(
        rd_prot=conf_type.rd_prot,
        original=conf_type.original,
        secret=conf_type.secret,
        letterbox=conf_type.letterbox,
        allow_anonymous=conf_type.allow_anonymous,
        forbid_secret=conf_type.forbid_secret,
        reserved2=conf_type.reserved2,
        reserved3=conf_type.reserved3)

def KomConference_to_dict(conf, lookups, session):
    return dict(
        conf_no=conf.conf_no,
        name=conf.name,
        type=to_dict(conf.type, lookups, session),
        creation_time=conf.creation_time.to_date_and_time(),
        last_written=conf.last_written.to_date_and_time(),
        creator=pers_to_dict(conf.creator, lookups, session),
        presentation=conf.presentation,
        supervisor=conf_to_dict(conf.supervisor, lookups, session),
        permitted_submitters=conf_to_dict(conf.permitted_submitters, lookups, session),
        super_conf=conf_to_dict(conf.super_conf, lookups, session),
        msg_of_day=conf.msg_of_day,
        nice=conf.nice,
        keep_commented=conf.keep_commented,
        no_of_members=conf.no_of_members,
        first_local_no=conf.first_local_no,
        no_of_texts=conf.no_of_texts,
        expire=conf.expire
        #aux-items
        )

def KomUConference_to_dict(conf, lookups, session):
    return dict(
        conf_no=conf.conf_no,
        name=conf.name,
        type=to_dict(conf.type, lookups, session),
        highest_local_no=conf.highest_local_no,
        nice=conf.nice
        )

def KomText_to_dict(komtext, lookups, session):
    d = dict(
        text_no=komtext.text_no,
        author=pers_to_dict(komtext.author, lookups, session),
        no_of_marks=komtext.no_of_marks,
        content_type=komtext.content_type,
        subject=komtext.subject)
    
    mime_type, encoding = parse_content_type(komtext.content_type)
    # Only add body if text
    if mime_type[0] == 'text':
        d['body'] = komtext.body
    
    if komtext.recipient_list is None:
        d['recipient_list'] = None
    else:
        d['recipient_list'] = [ to_dict(r, lookups, session)
                                for r in komtext.recipient_list ]
    
    if komtext.comment_to_list is None:
        d['comment_to_list'] = None
    else:
        d['comment_to_list'] = [ to_dict(ct, lookups, session)
                                 for ct in komtext.comment_to_list ]
    
    if komtext.comment_in_list is None:
        d['comment_in_list'] = None
    else:
        d['comment_in_list'] = [ to_dict(ci, lookups, session)
                                 for ci in komtext.comment_in_list ]
    
    if komtext.aux_items is None:
        d['aux_items'] = None
    else:
        aux_items = []
        for ai in filter(lambda ai: ai.tag in _ALLOWED_KOMTEXT_AUXITEMS,
                         komtext.aux_items):
            aux_items.append(to_dict(ai, lookups, session))
        d['aux_items'] = aux_items
    
    if komtext.creation_time is None:
        d['creation_time'] = None
    else:
        d['creation_time'] = komtext.creation_time.to_date_and_time()
    
    return d

def KomText_from_dict(d, lookups, session):
    kt = KomText()
    
    # Parse the content_type for some kind of basic test. Remove
    # charset / encoding param if it exist, and keep the rest. The subject
    # and body will not be encoded here.
    mime_type, encoding = parse_content_type(d['content_type'])
    kt.content_type = mime_type_tuple_to_str(mime_type)
    kt.subject = d['subject']
    kt.body = d['body']
    
    if 'recipient_list' in d and d['recipient_list'] is not None:
        kt.recipient_list = []
        for r in d['recipient_list']:
            kt.recipient_list.append(from_dict(r, kom.MIRecipient, lookups, session))
    else:
        kt.recipient_list = None
    
    if 'comment_to_list' in d and d['comment_to_list'] is not None:
        kt.comment_to_list = []
        for ct in d['comment_to_list']:
            kt.comment_to_list.append(from_dict(ct, kom.MICommentTo, lookups, session))
    else:
        kt.comment_to_list = None
    
    # comment_in typically makes no sense here, but we add them anyway
    # for sake of completeness. The reason it makes little sense is
    # because the primary usage for this function is when creating a
    # new text, and you cannot decide which texts that should be
    # comments to your new text. However, we don't know for sure here
    # what the purpose is, so we leave it to KomSession.create_text to not
    # make use of kt.comment_in_list.
    if 'comment_in_list' in d and d['comment_in_list'] is not None:
        kt.comment_in_list = []
        for ci in d['comment_in_list']:
            kt.comment_in_list.append(from_dict(ci, kom.MICommentIn, lookups, session))
    else:
        kt.comment_in_list = None
    
    return kt

def pers_to_dict(pers_no, lookups, session):
    if pers_no is None:
        return None
    
    if lookups:
        return dict(pers_no=pers_no, pers_name=session.get_conf_name(pers_no))
    else:
        return dict(pers_no=pers_no)

def conf_to_dict(conf_no, lookups, session):
    if conf_no is None:
        return None
    
    if lookups:
        return dict(conf_no=conf_no, conf_name=session.get_conf_name(conf_no))
    else:
        return dict(conf_no=conf_no)

def MIRecipient_to_dict(mir, lookups, session):
    if not mir.type in MIRecipient_type_to_str:
        raise KeyError("Unknown MIRecipient type: %s" % mir.type)
    
    if mir.rec_time is None:
        rec_time = None
    else:
        rec_time = mir.rec_time.to_date_and_time()
    
    
    if mir.sent_at is None:
        sent_at = None
    else:
        sent_at = mir.sent_at.to_date_and_time()
    
    d = dict(type=MIRecipient_type_to_str[mir.type],
             recpt=conf_to_dict(mir.recpt, lookups, session),
             loc_no=mir.loc_no,
             sent_by=pers_to_dict(mir.sent_by, lookups, session),
             sent_at=sent_at,
             rec_time=rec_time)
    
    return d

def MIRecipient_from_dict(d, lookups, session):
    """ Example dict: { "type": "to", "recpt": { "conf_no": 14506 } }
    """
    if d['type'] not in MIRecipient_str_to_type:
        raise KeyError("Unknown MIRecipient type str: %s" % d['type'])
    
    return kom.MIRecipient(type=MIRecipient_str_to_type[d['type']],
                           recpt=d['recpt']['conf_no'])

def MICommentTo_to_dict(micto, lookups, session):
    if not micto.type in MICommentTo_type_to_str:
        raise KeyError("Unknown MICommentTo type: %s" % micto.type)
    
    author = None
    if lookups:
        try:
            cts = session.get_text_stat(micto.text_no)
            author = pers_to_dict(cts.author, lookups, session)
        except (kom.NoSuchText, kom.TextZero):
            pass
    
    return dict(type=MICommentTo_type_to_str[micto.type],
                text_no=micto.text_no,
                author=author)

def MICommentTo_from_dict(d, lookups, session):
    if d['type'] not in MICommentTo_str_to_type:
        raise KeyError("Unknown MICommentTo type str: %s" % d['type'])
    
    return kom.MICommentTo(type=MICommentTo_str_to_type[d['type']], text_no=d['text_no'])

def MICommentIn_to_dict(micin, lookups, session):
    if not micin.type in MICommentIn_type_to_str:
        raise KeyError("Unknown MICommentIn type: %s" % micin.type)
    
    author = None
    if lookups:
        try:
            cts = session.get_text_stat(micin.text_no)
            author = pers_to_dict(cts.author, lookups, session)
        except (kom.NoSuchText, kom.TextZero):
            pass
    
    return dict(type=MICommentIn_type_to_str[micin.type],
                text_no=micin.text_no,
                author=author)

def MICommentIn_from_dict(d, lookups, session):
    if d['type'] not in MICommentIn_str_to_type:
        raise KeyError("Unknown MICommentIn type str: %s" % d['type'])
    
    return kom.MICommentTo(type=MICommentIn_str_to_type[d['type']], text_no=d['text_no'])

def AuxItem_to_dict(aux_item, lookups, session):
    return dict(aux_no=aux_item.aux_no,
                tag=komauxitems.aux_item_number_to_name[aux_item.tag],
                creator=pers_to_dict(aux_item.creator, lookups, session),
                created_at=aux_item.created_at.to_date_and_time(),
                flags=dict(deleted=aux_item.flags.deleted,
                           inherit=aux_item.flags.inherit,
                           secret=aux_item.flags.secret,
                           hide_creator=aux_item.flags.hide_creator,
                           dont_garb=aux_item.flags.dont_garb),
                inherit_limit=aux_item.inherit_limit,
                
                # aux-items are always latin-1 it seems like, but we
                # can afford to try with utf-8 first anyway.
                data=decode_text(aux_item.data, 'utf-8', backup_encoding='latin-1'))

def Mark_to_dict(mark, lookups, session):
    return dict(text_no=mark.text_no, type=mark.type)


# Misc functions

def decode_text(text, encoding, backup_encoding='latin1'):
    if encoding is None:
        encoding = backup_encoding
    
    try:
        decoded_text = text.decode(encoding)
    except UnicodeDecodeError:
        # (from iKOM) Fscking clients that can't detect coding...
        decoded_text = text.decode(backup_encoding)
    
    return decoded_text

def parse_content_type(contenttype):
    mime_type = mimeparse.parse_mime_type(contenttype)
    
    if mime_type[0] == 'x-kom' and mime_type[1] == 'text':
        mime_type = ('text', 'x-kom-basic', mime_type[2])
    
    if "charset" in mime_type[2]:
        # Remove charset from mime_type, if we have it
        encoding = mime_type[2].pop("charset")
    else:
        encoding = None
    
    if encoding == 'x-ctext':
        encoding = 'latin1'
    
    return mime_type, encoding

def mime_type_tuple_to_str(mime_type):
    params = [ "%s=%s" % (k, v) for k, v in mime_type[2].items() ]
    t = "%s/%s" % (mime_type[0], mime_type[1])
    l = [t]
    l.extend(params)
    return ";".join(l)
