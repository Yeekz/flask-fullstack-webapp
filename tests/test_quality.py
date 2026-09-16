"""API contracts, atomic validation and authorization regression coverage."""
import pytest
from tests.conftest import register_and_login


@pytest.fixture
def owner(client):
    register_and_login(client, 'qualityuser')
    project = client.post('/api/projects', json={'name':'Qualité'}).json['data']
    task = client.post(f"/api/projects/{project['id']}/tasks", json={'title':'Original', 'due_date':'2026-10-01'}).json['data']
    return client, project['id'], task['id']


@pytest.mark.parametrize('body', [[], ['x'], True, 12, 'value', None])
def test_requires_json_object(owner, body):
    client, project, task = owner
    for url in ['/api/projects', f'/api/projects/{project}/tasks']:
        res = client.post(url, json=body)
        assert res.status_code == 400
        assert res.json['success'] is False


@pytest.mark.parametrize('body', [{'title':None}, {'title':['bad']}, {'title':'x'*201}, {'due_date':20261001}, {'due_date':True}, {'due_date':'20261001'}, {'due_date':'2026-02-30'}])
def test_bad_update_does_not_mutate_task(owner, body):
    client, project, task = owner
    url = f'/api/projects/{project}/tasks/{task}'
    response = client.put(url, json={'description':'SHOULD NOT CHANGE', **body})
    assert response.status_code == 400
    current = client.get(url).json['data']
    assert current['title'] == 'Original'
    assert current['description'] == ''
    assert current['due_date'] == '2026-10-01'


@pytest.mark.parametrize('body', [{'name':None}, {'name':False}, {'name':'x'*129}, {'color':[]}, {'description':{}}])
def test_project_fields_are_typed(owner, body):
    client, project, _ = owner
    assert client.put(f'/api/projects/{project}', json=body).status_code == 400
    assert client.get(f'/api/projects/{project}').json['data']['name'] == 'Qualité'


def test_null_date_clears_due_date(owner):
    client, project, task = owner
    result = client.put(f'/api/projects/{project}/tasks/{task}', json={'due_date':None})
    assert result.status_code == 200
    assert result.json['data']['due_date'] is None


def test_unknown_status_is_not_silently_ignored(owner):
    client, project, _ = owner
    assert client.get(f'/api/projects/{project}/tasks?status=broken').status_code == 400


def test_stale_session_returns_401_or_login(client):
    with client.session_transaction() as session:
        session['user_id'] = 999999999
    assert client.get('/api/projects').status_code == 401
    with client.session_transaction() as session:
        session['user_id'] = 999999999
    assert client.get('/dashboard').status_code == 302


def test_other_user_cannot_read_modify_or_delete_tasks(owner):
    client, project, task = owner
    client.get('/logout')
    register_and_login(client, 'qualityintruder')
    url = f'/api/projects/{project}/tasks/{task}'
    assert client.get(url).status_code == 404
    assert client.put(url, json={'title':'Intrusion'}).status_code == 404
    assert client.delete(url).status_code == 404
