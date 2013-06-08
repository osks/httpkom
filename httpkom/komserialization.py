# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from pylyskom import kom, komauxitems
from pylyskom.utils import decode_text, mime_type_tuple_to_str, parse_content_type
from pylyskom.komsession import (KomSession, KomPerson, KomText, KomConference, KomUConference,
                                 KomMembership, KomMembershipUnread)


_ALLOWED_KOMTEXT_AUXITEMS = [
    komauxitems.AI_FAST_REPLY,
    komauxitems.AI_MX_DATE,
    komauxitems.AI_MX_AUTHOR
]


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



def to_dict(obj, lookups=False, session=None):
    if isinstance(obj, list):
        return [ to_dict(el, lookups, session) for el in obj ]
    elif isinstance(obj, KomSession):
        return KomSession_to_dict(obj, lookups, session)
    elif isinstance(obj, KomPerson):
        return KomPerson_to_dict(obj, lookups, session)
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
    elif isinstance(obj, KomMembershipUnread):
        return KomMembershipUnread_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.MembershipType):
        return MembershipType_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.AuxItem):
        return AuxItem_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.Mark):
        return Mark_to_dict(obj, lookups, session)
    elif isinstance(obj, kom.Time):
        return Time_to_dict(obj, lookups, session)
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
        pers_no = ksession.get_person_no()
        person = KomPerson_to_dict(KomPerson(pers_no), lookups, session)
    
    session_no = None
    if lookups:
        session_no = ksession.who_am_i()
    
    return dict(person=person, session_no=session_no)

def KomPerson_to_dict(kom_person, lookups, session):
    pers_name = None
    if lookups:
        pers_name = session.get_conf_name(kom_person.pers_no)
    return dict(pers_no=kom_person.pers_no, pers_name=pers_name)

def KomMembership_to_dict(membership, lookups, session):
    return dict(
        pers_no=membership.pers_no,
        position=membership.position,
        last_time_read=Time_to_dict(membership.last_time_read, lookups, session),
        conference=conf_to_dict(membership.conference, lookups, session),
        priority=membership.priority,
        added_by=pers_to_dict(membership.added_by, lookups, session),
        added_at=Time_to_dict(membership.added_at, lookups, session),
        type=to_dict(membership.type, lookups, session))

def KomMembershipUnread_to_dict(membership_unread, lookups, session):
    return dict(
        pers_no=membership_unread.pers_no,
        conf_no=membership_unread.conf_no,
        no_of_unread=membership_unread.no_of_unread,
        unread_texts=to_dict(membership_unread.unread_texts, lookups, session))

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
        creation_time=Time_to_dict(conf.creation_time, lookups, session),
        last_written=Time_to_dict(conf.last_written, lookups, session),
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
        d['creation_time'] = Time_to_dict(komtext.creation_time, lookups, session)
    
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
        rec_time = Time_to_dict(mir.rec_time, lookups, session)
    
    
    if mir.sent_at is None:
        sent_at = None
    else:
        sent_at = Time_to_dict(mir.sent_at, lookups, session)
    
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
                created_at=Time_to_dict(aux_item.created_at, lookups, session),
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

def Time_to_dict(time, lookups, session):
    return int(time.to_python_time())
