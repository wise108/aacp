from __future__ import annotations

import base64
import json

from aacp.message_store import CanonicalState, CasConflict, GitHubMessageStore

CONVERSATION = "C-test"
STREAM = "S-test"


def msg(mid: str, seq: int) -> dict[str, object]:
    return {"type": "event", "message_id": mid, "conversation_id": CONVERSATION, "stream_id": STREAM, "sequence": seq, "payload": {"value": mid}}


def test_read_list_and_publish_cas_against_git_data_api() -> None:
    state = {"sha": "h0", "ref": "refs/heads/main"}
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
                    return json.dumps([{"sha": objects["publication"]}]).encode()
                if method == "POST" and path.endswith("/git/blobs"):
                    counter["n"] += 1; sha = f"b{counter['n']}"; objects[sha] = msg("M-1", 1); return json.dumps({"sha": sha}).encode()
                if method == "POST" and path.endswith("/git/trees"):
                    counter["n"] += 1; sha = f"t{counter['n']}"; objects[sha] = {"tree": []}; return json.dumps({"sha": sha}).encode()
                if method == "POST" and path.endswith("/git/commits"):
                    counter["n"] += 1; sha = f"c{counter['n']}"; objects[sha] = {"tree": {"sha": "t1"}}; objects["publication"] = sha; return json.dumps({"sha": sha}).encode()
                if method == "PATCH" and path.endswith("/git/refs/heads/main"):
                    refs["main"] = json.loads(request.data.decode())["sha"]; return b"{}"
                raise AssertionError(f"unexpected {method} {path}")
        return Response()

    store = GitHubMessageStore(owner="o", repo="r", target_ref="refs/heads/main", conversation_id=CONVERSATION, stream_id=STREAM, token="test", api_base="https://api.github.test", opener=opener)
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
    store = GitHubMessageStore(owner="o", repo="r", target_ref="refs/heads/main", conversation_id=CONVERSATION, stream_id=STREAM, token="test", api_base="https://api.github.test", opener=opener)
    state = CanonicalState("h1", "refs/heads/main", STREAM)
    result = store.publish_cas(state, store.prepare_publication(state, msg("M-1", 1)))
    assert isinstance(result, CasConflict)
    assert result.reason == "head_moved"
    assert calls == 1
