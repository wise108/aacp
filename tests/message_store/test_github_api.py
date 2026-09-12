from __future__ import annotations

import base64
import json
from io import BytesIO
from urllib.error import HTTPError

from aacp.message_store import (
    CanonicalState,
    CasConflict,
    GitHubAPIError,
    GitHubMessageStore,
)

CONVERSATION = "C-test"
STREAM = "S-test"


def msg(mid: str, seq: int) -> dict[str, object]:
    return {
        "type": "event",
        "message_id": mid,
        "conversation_id": CONVERSATION,
        "stream_id": STREAM,
        "sequence": seq,
        "payload": {"value": mid},
    }


def test_read_list_and_publish_cas_against_git_data_api() -> None:
    objects: dict[str, object] = {
        "h0": {"tree": {"sha": "t0"}},
        "t0": {"tree": []},
    }
    refs = {"main": "h0"}
    counter = {"n": 0}

    def opener(request):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self):
                path = request.full_url.split("/api.github.test", 1)[-1]
                method = request.method
                if method == "GET" and path == "/repos/o/r/git/ref/heads/main":
                    return json.dumps({"object": {"sha": refs["main"]}}).encode()
                if method == "GET" and path.startswith("/repos/o/r/git/commits/"):
                    sha = path.rsplit("/", 1)[-1]
                    return json.dumps(objects[sha]).encode()
                if method == "GET" and path.startswith("/repos/o/r/git/trees/"):
                    sha = path.split("/git/trees/", 1)[1].split("?", 1)[0]
                    return json.dumps(objects[sha]).encode()
                if method == "GET" and path.startswith("/repos/o/r/git/blobs/"):
                    sha = path.rsplit("/", 1)[-1]
                    return json.dumps({"content": base64.b64encode(json.dumps(objects[sha]).encode()).decode()}).encode()
                if method == "GET" and path.startswith("/repos/o/r/commits?"):
                    return json.dumps([{"sha": "publication"}]).encode()
                if method == "POST" and path.endswith("/git/blobs"):
                    counter["n"] += 1
                    sha = f"b{counter['n']}"
                    objects[sha] = msg("M-1", 1)
                    return json.dumps({"sha": sha}).encode()
                if method == "POST" and path.endswith("/git/trees"):
                    counter["n"] += 1
                    sha = f"t{counter['n']}"
                    objects[sha] = {"tree": []}
                    return json.dumps({"sha": sha}).encode()
                if method == "POST" and path.endswith("/git/commits"):
                    counter["n"] += 1
                    sha = f"c{counter['n']}"
                    objects[sha] = {"tree": {"sha": "t1"}}
                    return json.dumps({"sha": sha}).encode()
                if method == "PATCH" and path.endswith("/git/refs/heads/main"):
                    refs["main"] = json.loads(request.data.decode())["sha"]
                    return b"{}"
                raise AssertionError(f"unexpected {method} {path}")
        return Response()

    store = GitHubMessageStore(
        owner="o", repo="r", target_ref="refs/heads/main",
        conversation_id=CONVERSATION, stream_id=STREAM, token="test",
        api_base="https://api.github.test", opener=opener,
    )
    state0 = store.read_canonical_state()
    assert state0.token == "h0"
    publication = store.prepare_publication(state0, msg("M-1", 1))
    result = store.publish_cas(state0, publication)
    assert result.kind == "success"
    assert result.publication_commit


def test_stale_github_ref_is_cas_conflict() -> None:
    calls = 0

    def opener(request):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"object":{"sha":"h2"}}'
        nonlocal calls
        calls += 1
        return Response()

    store = GitHubMessageStore(
        owner="o", repo="r", target_ref="refs/heads/main",
        conversation_id=CONVERSATION, stream_id=STREAM, token="test",
        api_base="https://api.github.test", opener=opener,
    )
    state = CanonicalState("h1", "refs/heads/main", STREAM)
    result = store.publish_cas(state, store.prepare_publication(state, msg("M-1", 1)))
    assert isinstance(result, CasConflict)
    assert result.reason == "head_moved"
    assert calls == 1


def test_http_422_is_not_cas_conflict() -> None:
    def opener(request):
        raise HTTPError(
            request.full_url, 422, "validation failed", {}, BytesIO(b'{"message":"bad request"}'))

    store = GitHubMessageStore(
        owner="o", repo="r", target_ref="refs/heads/main",
        conversation_id=CONVERSATION, stream_id=STREAM, token="test",
        api_base="https://api.github.test", opener=opener,
    )
    try:
        store.read_canonical_state()
    except GitHubAPIError as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("HTTP 422 must remain a GitHub API error")


def test_http_409_during_ref_update_is_cas_conflict() -> None:
    calls = {"ref": 0}

    def opener(request):
        path = request.full_url.split("/api.github.test", 1)[-1]

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self):
                if request.method == "GET" and path == "/repos/o/r/git/ref/heads/main":
                    return b'{"object":{"sha":"h0"}}'
                if request.method == "GET" and path.startswith("/repos/o/r/git/commits/"):
                    return b'{"tree":{"sha":"t0"}}'
                if request.method == "POST" and path.endswith("/git/blobs"):
                    return b'{"sha":"b1"}'
                if request.method == "POST" and path.endswith("/git/trees"):
                    return b'{"sha":"t1"}'
                if request.method == "POST" and path.endswith("/git/commits"):
                    return b'{"sha":"c1"}'
                raise AssertionError(f"unexpected {request.method} {path}")

        if request.method == "PATCH" and path.endswith("/git/refs/heads/main"):
            calls["ref"] += 1
            raise HTTPError(
                request.full_url, 409, "conflict", {}, BytesIO(b'{"message":"conflict"}'))
        return Response()

    store = GitHubMessageStore(
        owner="o", repo="r", target_ref="refs/heads/main",
        conversation_id=CONVERSATION, stream_id=STREAM, token="test",
        api_base="https://api.github.test", opener=opener,
    )
    state = store.read_canonical_state()
    result = store.publish_cas(state, store.prepare_publication(state, msg("M-1", 1)))
    assert isinstance(result, CasConflict)
    assert result.reason == "head_moved"
    assert calls["ref"] == 1


def test_publication_provenance_uses_newest_path_commit() -> None:
    message = msg("M-1", 1)
    calls = []

    def opener(request):
        path = request.full_url.split("/api.github.test", 1)[-1]
        calls.append((request.method, path))

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self):
                if request.method == "GET" and path == "/repos/o/r/git/ref/heads/main":
                    return b'{"object":{"sha":"h2"}}'
                if request.method == "GET" and path.startswith("/repos/o/r/git/commits/"):
                    return b'{"tree":{"sha":"t2"}}'
                if request.method == "GET" and path.startswith("/repos/o/r/git/trees/"):
                    return json.dumps({"tree": [{"path": ".aacp/conversations/C-test/messages/000001-M-1.json", "sha": "b1"}]}).encode()
                if request.method == "GET" and path.startswith("/repos/o/r/git/blobs/"):
                    return json.dumps({"content": base64.b64encode(json.dumps(message).encode()).decode()}).encode()
                if request.method == "GET" and path.startswith("/repos/o/r/commits?"):
                    return b'[{"sha":"h2"},{"sha":"c1"}]'
                raise AssertionError(f"unexpected {request.method} {path}")
        return Response()

    store = GitHubMessageStore(
        owner="o", repo="r", target_ref="refs/heads/main",
        conversation_id=CONVERSATION, stream_id=STREAM, token="test",
        api_base="https://api.github.test", opener=opener,
    )
    state = CanonicalState("h2", "refs/heads/main", STREAM)
    evidence = store.find_publication_evidence(state, "M-1")
    assert evidence is not None
    assert evidence.publication_commit == "h2"
