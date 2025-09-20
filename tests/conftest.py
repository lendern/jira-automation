from __future__ import annotations

import types
import pytest


class _Attr:
    def __init__(self, **attrs):
        for k, v in attrs.items():
            setattr(self, k, v)


def _wrap_value(v):
    # Promote simple dicts to objects with attribute access (name/key/value)
    if isinstance(v, dict):
        if 'name' in v:
            return _Attr(name=v['name'])
        if 'key' in v:
            return _Attr(key=v['key'])
        if 'value' in v:
            return _Attr(value=v['value'])
        return v
    if isinstance(v, list):
        out = []
        for x in v:
            out.append(_wrap_value(x))
        return out
    return v


class FakeFields:
    def __init__(self, raw: dict[str, object]):
        self._raw = raw

    def __getattr__(self, item):
        if item in self._raw:
            return _wrap_value(self._raw[item])
        raise AttributeError(item)


class FakeIssue:
    def __init__(self, key: str, fields: dict[str, object] | None = None):
        self.key = key
        self.fields = FakeFields(fields or {})


class FakeRepo:
    """In-memory Repository-like double for tests.

    Stores per-issue field state as python values (close to Jira REST shapes):
    - priority: {"name": "High"}
    - components: [{"name": "Network"}, ...]
    - labels: ["FY26Q1", ...]
    - story points: integer under "customfield_10006"
    - LVL2: pu -> {"value": ...}, blfnt -> {"value": ...}
    """

    def __init__(self):
        self.state: dict[str, dict[str, object]] = {}
        self.updates: list[tuple[str, dict[str, object]]] = []

    # Minimal API used by tests and services
    def get_issue(self, key: str):
        return FakeIssue(key, self.state.get(key, {}))

    def get_fields(self, key: str, fields: list[str]) -> dict[str, object]:
        cur = self.state.get(key, {})
        # Wrap values to emulate jira objects with attribute access
        return {f: _wrap_value(cur.get(f)) for f in fields}

    def update_fields(self, key: str, fields: dict[str, object]) -> None:
        box = self.state.setdefault(key, {})
        box.update(fields)
        self.updates.append((key, fields))


@pytest.fixture()
def repo():
    return FakeRepo()
