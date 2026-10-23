"""Guard contracts; full data/rollback rehearsal uses a restored private backup."""
from copy import deepcopy

import pytest

from app.services.flood_data_reset import DELETE_ORDER,REVISION,verify_preserved


def snapshots():
    before={'revision':REVISION,'rows':{name:{'count':2,'sha256':'before'} for name in DELETE_ORDER},
        'triggers':['enabled'],'constraints':['enforced'],'sequences':['unchanged'],
        'notification_ids':[2],'detach_post_ids':[3]}
    before['rows'].update({name:{'count':1,'sha256':'protected'} for name in
        ('users','community_posts','news_articles','news_article_versions','notifications')})
    after=deepcopy(before)
    for name in DELETE_ORDER:after['rows'][name]={'count':0,'sha256':'empty'}
    after.update(notification_ids=[],detach_post_ids=[])
    return before,after


def test_complete_clear_accepts_exact_preservation():
    before,after=snapshots();verify_preserved(before,after)


@pytest.mark.parametrize('table',['users','community_posts','news_articles','news_article_versions','notifications'])
def test_any_preserved_content_change_rejects_commit(table):
    before,after=snapshots();after['rows'][table]['sha256']='changed'
    with pytest.raises(ValueError,match='preserved_rows_changed'):verify_preserved(before,after)


@pytest.mark.parametrize('section',['triggers','constraints','sequences'])
def test_schema_or_identity_state_change_rejects_commit(section):
    before,after=snapshots();after[section]=['changed']
    with pytest.raises(ValueError,match='schema_or_sequence_changed'):verify_preserved(before,after)


@pytest.mark.parametrize('section',['notification_ids','detach_post_ids'])
def test_dangling_links_reject_commit(section):
    before,after=snapshots();after[section]=[1]
    with pytest.raises(ValueError,match='link_cleanup_incomplete'):verify_preserved(before,after)


def test_nonempty_flood_table_rejects_commit():
    before,after=snapshots();after['rows']['flood_reports']['count']=1
    with pytest.raises(ValueError,match='target_not_empty'):verify_preserved(before,after)
