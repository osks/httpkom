# -*- coding: utf-8 -*-
# Copyright (C) 2012 Oskar Skoog. Released under GPL.

from __future__ import absolute_import
from pylyskom import komauxitems, datatypes, errors
from pylyskom.utils import decode_text, parse_content_type
from pylyskom.komsession import (
    KomAuxItem,
    KomConference,
    KomConferenceName,
    KomMembership,
    KomMembershipUnread,
    KomPerson,
    KomPersonName,
    KomText,
    KomUConference,
)


_ALLOWED_KOMTEXT_AUXITEMS = [
    komauxitems.AI_FAST_REPLY,
    komauxitems.AI_MX_DATE,
    komauxitems.AI_MX_AUTHOR,
    komauxitems.AI_FAQ_TEXT,
    komauxitems.AI_FAQ_FOR_CONF,

    komauxitems.AI_KOMFEEDER_URL,
    komauxitems.AI_KOMFEEDER_TITLE,
    komauxitems.AI_KOMFEEDER_AUTHOR,
    komauxitems.AI_KOMFEEDER_DATE,
]


MIRecipient_type_to_str = { datatypes.MIR_TO: 'to',
                            datatypes.MIR_CC: 'cc',
                            datatypes.MIR_BCC: 'bcc' }

MIRecipient_str_to_type = { 'to': datatypes.MIR_TO,
                            'cc': datatypes.MIR_CC,
                            'bcc': datatypes.MIR_BCC }

MICommentTo_type_to_str = { datatypes.MIC_COMMENT: 'comment',
                            datatypes.MIC_FOOTNOTE: 'footnote' }

MICommentTo_str_to_type = { 'comment': datatypes.MIC_COMMENT,
                            'footnote': datatypes.MIC_FOOTNOTE }

MICommentIn_type_to_str = { datatypes.MIC_COMMENT: 'comment',
                            datatypes.MIC_FOOTNOTE: 'footnote' }

MICommentIn_str_to_type = { 'comment': datatypes.MIC_COMMENT,
                            'footnote': datatypes.MIC_FOOTNOTE }



async def to_dict(obj, session=None):
    if obj is None:
        return None
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [ await to_dict(el, session) for el in obj ]
    elif isinstance(obj, KomPerson):
        return KomPerson_to_dict(obj)
    elif isinstance(obj, KomPersonName):
        return KomPersonName_to_dict(obj)
    elif isinstance(obj, KomText):
        return await KomText_to_dict(obj, session)
    elif isinstance(obj, datatypes.MIRecipient):
        return await MIRecipient_to_dict(obj, session)
    elif isinstance(obj, datatypes.MICommentTo):
        return await MICommentTo_to_dict(obj, session)
    elif isinstance(obj, datatypes.MICommentIn):
        return await MICommentIn_to_dict(obj, session)
    elif isinstance(obj, KomConferenceName):
        return KomConferenceName_to_dict(obj)
    elif isinstance(obj, KomConference):
        return KomConference_to_dict(obj)
    elif isinstance(obj, KomUConference):
        return KomUConference_to_dict(obj)
    elif isinstance(obj, datatypes.ConfType):
        return ConfType_to_dict(obj)
    elif isinstance(obj, KomMembership):
        return KomMembership_to_dict(obj)
    elif isinstance(obj, KomMembershipUnread):
        return KomMembershipUnread_to_dict(obj)
    elif isinstance(obj, datatypes.MembershipType):
        return MembershipType_to_dict(obj)
    elif isinstance(obj, datatypes.AuxItem):
        raise RuntimeError("Should use KomAuxItem")
    elif isinstance(obj, KomAuxItem):
        return KomAuxItem_to_dict(obj)
    elif isinstance(obj, datatypes.Mark):
        return Mark_to_dict(obj)
    elif isinstance(obj, datatypes.Time):
        return Time_to_dict(obj)
    else:
        #raise NotImplementedError("to_dict is not implemented for: %s" % type(obj))
        return obj

def KomPerson_to_dict(kom_person):
    if kom_person is None:
        return None
    return dict(pers_no=kom_person.pers_no, pers_name=kom_person.username)

def KomPersonName_to_dict(kom_person_name):
    if kom_person_name is None:
        return None
    return dict(pers_no=kom_person_name.pers_no, pers_name=kom_person_name.username)

# TODO: Replace usage of pers_to_dict with KomPersonName_to_dict
async def pers_to_dict(pers_no, session):
    if pers_no is None:
        return None
    person = await session.get_person_name(pers_no)
    return dict(pers_no=person.pers_no, pers_name=person.username)

def KomMembership_to_dict(membership):
    return dict(
        pers_no=membership.pers_no,
        position=membership.position,
        last_time_read=Time_to_dict(membership.last_time_read),
        conference=KomUConference_to_dict(membership.conference),
        priority=membership.priority,
        added_by=KomPersonName_to_dict(membership.added_by),
        added_at=Time_to_dict(membership.added_at),
        type=MembershipType_to_dict(membership.type))

def KomMembershipUnread_to_dict(membership_unread):
    return dict(
        pers_no=membership_unread.pers_no,
        conf_no=membership_unread.conf_no,
        no_of_unread=membership_unread.no_of_unread,
        unread_texts=membership_unread.unread_texts)

def MembershipType_to_dict(m_type):
    return dict(
        invitation=m_type.invitation,
        passive=m_type.passive,
        secret=m_type.secret,
        passive_message_invert=m_type.passive_message_invert)

def ConfType_to_dict(conf_type):
    return dict(
        rd_prot=conf_type.rd_prot,
        original=conf_type.original,
        secret=conf_type.secret,
        letterbox=conf_type.letterbox,
        allow_anonymous=conf_type.allow_anonymous,
        forbid_secret=conf_type.forbid_secret,
        reserved2=conf_type.reserved2,
        reserved3=conf_type.reserved3)

def KomConferenceName_to_dict(conf):
    if conf is None:
        return None
    return dict(
        conf_no=conf.conf_no,
        name=conf.name,
    )

def KomConference_to_dict(conf):
    d = dict(
        conf_no=conf.conf_no,
        name=conf.name,
        type=ConfType_to_dict(conf.type),
        creation_time=Time_to_dict(conf.creation_time),
        last_written=Time_to_dict(conf.last_written),
        creator=KomPersonName_to_dict(conf.creator),
        presentation=conf.presentation,
        supervisor=KomConferenceName_to_dict(conf.supervisor),
        permitted_submitters=KomConferenceName_to_dict(conf.permitted_submitters),
        super_conf=KomConferenceName_to_dict(conf.super_conf),
        msg_of_day=conf.msg_of_day,
        nice=conf.nice,
        keep_commented=conf.keep_commented,
        no_of_members=conf.no_of_members,
        first_local_no=conf.first_local_no,
        no_of_texts=conf.no_of_texts,
        expire=conf.expire
        )

    if conf.aux_items is None:
        d['aux_items'] = None
    else:
        aux_items = []
        for ai in [ai for ai in conf.aux_items if ai.tag in _ALLOWED_KOMTEXT_AUXITEMS]:
            aux_items.append(KomAuxItem_to_dict(ai))
        d['aux_items'] = aux_items

    return d

def KomUConference_to_dict(conf):
    if conf is None:
        return None
    return dict(
        conf_no=conf.conf_no,
        name=conf.name,
        type=ConfType_to_dict(conf.type),
        highest_local_no=conf.highest_local_no,
        nice=conf.nice
    )

async def KomText_to_dict(komtext, session):
    d = dict(
        text_no=komtext.text_no,
        author=KomPerson_to_dict(komtext.author),
        no_of_marks=komtext.no_of_marks,
        content_type=komtext.content_type,
        subject=komtext.subject)

    mime_type, encoding = parse_content_type(komtext.content_type)
    # Only add body if text
    if mime_type[0] == 'text':
        d['body'] = komtext.body
    elif mime_type[0] == 'x-kom' and mime_type[1] == 'user-area':
        d['body'] = komtext.body
    
    if komtext.recipient_list is None:
        d['recipient_list'] = None
    else:
        d['recipient_list'] = [ await MIRecipient_to_dict(r, session)
                                for r in komtext.recipient_list ]
    
    if komtext.comment_to_list is None:
        d['comment_to_list'] = None
    else:
        d['comment_to_list'] = [ await MICommentTo_to_dict(ct, session)
                                 for ct in komtext.comment_to_list ]
    
    if komtext.comment_in_list is None:
        d['comment_in_list'] = None
    else:
        d['comment_in_list'] = [ await MICommentIn_to_dict(ci, session)
                                 for ci in komtext.comment_in_list ]
    
    if komtext.aux_items is None:
        d['aux_items'] = None
    else:
        aux_items = []
        for ai in [ai for ai in komtext.aux_items if ai.tag in _ALLOWED_KOMTEXT_AUXITEMS]:
            aux_items.append(KomAuxItem_to_dict(ai))
        d['aux_items'] = aux_items
    
    if komtext.creation_time is None:
        d['creation_time'] = None
    else:
        d['creation_time'] = Time_to_dict(komtext.creation_time)
    
    return d

async def MIRecipient_to_dict(mir, session):
    if not mir.type in MIRecipient_type_to_str:
        raise KeyError("Unknown MIRecipient type: %s" % mir.type)

    if mir.rec_time is None:
        rec_time = None
    else:
        rec_time = Time_to_dict(mir.rec_time)

    if mir.sent_at is None:
        sent_at = None
    else:
        sent_at = Time_to_dict(mir.sent_at)

    recpt_conf = await session.get_conf_name(mir.recpt)
    d = dict(type=MIRecipient_type_to_str[mir.type],
             recpt=KomConferenceName_to_dict(recpt_conf),
             loc_no=mir.loc_no,
             sent_by=await pers_to_dict(mir.sent_by, session),
             sent_at=sent_at,
             rec_time=rec_time)

    return d

async def MICommentTo_to_dict(micto, session):
    if not micto.type in MICommentTo_type_to_str:
        raise KeyError("Unknown MICommentTo type: %s" % micto.type)
    
    author = None
    try:
        cts = await session.get_text_stat(micto.text_no)
        author = await pers_to_dict(cts.author, session)
    except (errors.NoSuchText, errors.TextZero):
        pass
    
    return dict(type=MICommentTo_type_to_str[micto.type],
                text_no=micto.text_no,
                author=author)

async def MICommentIn_to_dict(micin, session):
    if not micin.type in MICommentIn_type_to_str:
        raise KeyError("Unknown MICommentIn type: %s" % micin.type)
    
    author = None
    try:
        cts = await session.get_text_stat(micin.text_no)
        author = await pers_to_dict(cts.author, session)
    except (errors.NoSuchText, errors.TextZero):
        pass
    
    return dict(type=MICommentIn_type_to_str[micin.type],
                text_no=micin.text_no,
                author=author)

def KomAuxItem_to_dict(aux_item):
    return dict(aux_no=aux_item.aux_no,
                tag=komauxitems.aux_item_number_to_name[aux_item.tag],
                creator=KomPerson_to_dict(aux_item.creator),
                created_at=Time_to_dict(aux_item.created_at),
                flags=dict(deleted=aux_item.flags.deleted,
                           inherit=aux_item.flags.inherit,
                           secret=aux_item.flags.secret,
                           hide_creator=aux_item.flags.hide_creator,
                           dont_garb=aux_item.flags.dont_garb),
                inherit_limit=aux_item.inherit_limit,

                # aux-items are always latin-1 it seems like, but we
                # can afford to try with utf-8 first anyway.
                data=decode_text(aux_item.data, 'utf-8', backup_encoding='latin-1'))

def Mark_to_dict(mark):
    return dict(text_no=mark.text_no, type=mark.type)

def Time_to_dict(time):
    return time.to_iso_8601()
