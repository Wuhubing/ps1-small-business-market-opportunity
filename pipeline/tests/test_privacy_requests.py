from unittest.mock import Mock, patch
import pytest
from pipeline import fetch_cambridge as cambridge
from pipeline import fetch_boston_licenses as boston


def response(payload):
    return Mock(json=Mock(return_value=payload))


def test_cambridge_projects_only_approved_fields():
    with patch.object(cambridge.requests, 'get', side_effect=[response([{'count': '1'}]), response([{'status': 'Issued'}])]) as get:
        frame, count = cambridge.soda('q9yz-5w2v')
    assert count == 1
    assert get.call_args.kwargs['params']['$select'] == ','.join(cambridge.SAFE_FIELDS['q9yz-5w2v'])
    assert set(frame.columns) == set(cambridge.SAFE_FIELDS['q9yz-5w2v'])
    with pytest.raises(KeyError):
        cambridge.soda('unreviewed')


def test_boston_projection_survives_pagination():
    payloads = [response({'success': True, 'result': {'total': 2, 'records': [{'licensecat': 'FS'}]}}),
                response({'success': True, 'result': {'total': 2, 'records': [{'licensecat': 'FT'}]}})]
    with patch.object(boston.requests, 'get', side_effect=payloads) as get:
        frame = boston.fetch_licenses()
    assert len(frame) == 2
    assert [c.kwargs['params']['offset'] for c in get.call_args_list] == [0, 1]
    assert all(c.kwargs['params']['fields'] == ','.join(boston.SAFE_FIELDS) for c in get.call_args_list)


def test_boston_fails_closed_on_extra_fields():
    with patch.object(boston.requests, 'get', return_value=response({'success': True, 'result': {'total': 1, 'records': [{'dayphn_cleaned': 'not retained'}]}})):
        with pytest.raises(ValueError, match='approved projection'):
            boston.fetch_licenses()
