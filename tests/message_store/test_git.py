from __future__ import annotations

import subprocess
from pathlib import Path

from aacp.message_store import CanonicalState, CasConflict, GitMessageStore

CONVERSATION = "C-test"
STREAM = "S-test"


def git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)
    return result.stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(remote), str(work)], check=True, capture_output=True)
    git(work, "config", "user.name", "AACP Test")
    git(work, "config", "user.email", "aacp-test@example.invalid")
    (work / ".gitkeep").write_text("init\n", encoding="utf-8")
    git(work, "add", ".gitkeep")
    git(work, "commit", "init")
    git(work, "branch", "-M", "main")
    git(work, "push", "origin", "main")
    return work


def message(message_id: str, sequence: int) -> dict[str, object]:
    return {
        "type": "event",
        "message_id": message_id,
        "conversation_id": CONVERSATION,
        "stream_id": STREAM,
        "sequence": sequence,
        "payload": {"value": message_id},
    }


def store(work: Path) -> GitMessageStore:
    return GitMessageStore(work, target_ref="refs/heads/main", conversation_id=CONVERSATION, stream_id=STREAM)


def test_publish_and_preserve_original_provenance(tmp_path: Path) -> None:
    s = store(make_repo(tmp_path))
    state = s.read_canonical_state()
    result = s.publish_cas(state, s.prepare_publication(state, message("M-1", 1)))
    assert result.kind == "success"
    assert result.publication_commit

    current = s.read_canonical_state()
    evidence = s.find_publication_evidence(current, "M-1")
    assert evidence is not None
    assert evidence.publication_commit == result.publication_commit

    result2 = s.publish_cas(current, s.prepare_publication(current, message("M-2", 2)))
    assert result2.kind == "success"
    later = s.read_canonical_state()
    evidence_again = s.find_publication_evidence(later, "M-1")
    assert evidence_again is not None
    assert evidence_again.publication_commit == result.publication_commit


def test_stale_state_is_cas_conflict(tmp_path: Path) -> None:
    s = store(make_repo(tmp_path))
    state = s.read_canonical_state()
    first = s.publish_cas(state, s.prepare_publication(state, message("M-1", 1)))
    assert first.kind == "success"
    result = s.publish_cas(state, s.prepare_publication(state, message("M-2", 2)))
    assert isinstance(result, CasConflict)
    assert result.reason == "head_moved"


def test_target_and_stream_binding_are_enforced(tmp_path: Path) -> None:
    s = store(make_repo(tmp_path))
    state = s.read_canonical_state()
    try:
        s.list_messages(CanonicalState(state.token, state.target_ref, "other-stream"))
    except ValueError as exc:
        assert "stream_id" in str(exc)
    else:
        raise AssertionError("stream mismatch must be rejected")
