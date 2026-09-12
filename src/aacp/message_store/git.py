"""Git CLI Message Store backend for the GitHub transport profile.

This backend implements the transport-neutral MessageStore contract using a
canonical Git ref as the CAS token. It never force-updates the canonical ref.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from aacp.message_store.models import (
    CanonicalState,
    CasConflict,
    CasResult,
    CasSuccess,
    CasUncertain,
    PreparedPublication,
    PublicationEvidence,
    VerificationResult,
)


class GitMessageStore:
    """Race-safe Git-backed MessageStore for one conversation/stream target."""

    def __init__(self, repo_path: str | Path, *, remote: str = "origin", target_ref: str,
                 conversation_id: str, stream_id: str) -> None:
        if not target_ref.startswith("refs/heads/"):
            raise ValueError("GitMessageStore requires refs/heads/<branch> target_ref")
        if not conversation_id or not stream_id:
            raise ValueError("conversation_id and stream_id are required")
        self.root = Path(repo_path)
        self.remote = remote
        self.target_ref = target_ref
        self.conversation_id = conversation_id
        self.stream_id = stream_id
        self.messages_prefix = f".aacp/conversations/{conversation_id}/messages"

    def _run(self, *args: str, check: bool = True,
             env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(["git", *args], cwd=self.root, check=check,
                              text=True, capture_output=True, env=merged)

    @property
    def branch(self) -> str:
        return self.target_ref.removeprefix("refs/heads/")

    def _fetch(self) -> None:
        result = self._run("fetch", self.remote, self.branch, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "git fetch failed")

    def _remote_head(self) -> str:
        self._fetch()
        result = self._run("rev-parse", f"{self.remote}/{self.branch}", check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "canonical branch does not exist")
        return result.stdout.strip()

    def read_canonical_state(self) -> CanonicalState:
        return CanonicalState(self._remote_head(), self.target_ref, self.stream_id)

    def _validate_state(self, state: CanonicalState) -> None:
        if state.target_ref != self.target_ref:
            raise ValueError("canonical target_ref does not match MessageStore binding")
        if state.stream_id != self.stream_id:
            raise ValueError("canonical stream_id does not match MessageStore binding")

    @staticmethod
    def _decode_message(body: str) -> dict[str, Any]:
        value = json.loads(body)
        if not isinstance(value, dict):
            raise ValueError("message artifact must contain a JSON object")
        return value

    def list_messages(self, state: CanonicalState) -> list[dict[str, Any]]:
        self._validate_state(state)
        listing = self._run("ls-tree", "-r", "--name-only", state.token, "--", self.messages_prefix)
        messages: list[dict[str, Any]] = []
        for path in listing.stdout.splitlines():
            if path.endswith(".json"):
                message = self._decode_message(self._run("show", f"{state.token}:{path}").stdout)
                if message.get("stream_id") == self.stream_id:
                    messages.append(message)
        return messages

    def find_by_message_id(self, state: CanonicalState, message_id: str) -> dict[str, Any] | None:
        return next((m for m in self.list_messages(state) if m.get("message_id") == message_id), None)

    def _message_path(self, message: dict[str, Any]) -> str:
        sequence = int(message["sequence"])
        return f"{self.messages_prefix}/{sequence:06d}-{message['message_id']}.json"

    @staticmethod
    def _serialize(message: dict[str, Any]) -> str:
        return json.dumps(message, ensure_ascii=False, indent=2) + "\n"

    def prepare_publication(self, state: CanonicalState, message: dict[str, Any]) -> PreparedPublication:
        self._validate_state(state)
        if message.get("conversation_id") != self.conversation_id:
            raise ValueError("message conversation_id does not match MessageStore binding")
        if message.get("stream_id") != self.stream_id:
            raise ValueError("message stream_id does not match MessageStore binding")
        if "sequence" not in message or int(message["sequence"]) <= 0:
            raise ValueError("ordered publication requires a positive sequence")
        if not message.get("message_id"):
            raise ValueError("message_id is required")
        return PreparedPublication(state, dict(message))

    def _commit_with_temp_index(self, expected_state: CanonicalState,
                                publication: PreparedPublication) -> str:
        fd, index_path = tempfile.mkstemp(prefix="aacp-index-")
        os.close(fd)
        try:
            env = {"GIT_INDEX_FILE": index_path}
            self._run("read-tree", expected_state.token, env=env)
            blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=self.root,
                                  input=self._serialize(publication.message), text=True,
                                  capture_output=True, check=True, env={**os.environ, **env})
            blob_sha = blob.stdout.strip()
            self._run("update-index", "--add", "--cacheinfo",
                      f"100644,{blob_sha},{self._message_path(publication.message)}", env=env)
            tree_sha = self._run("write-tree", env=env).stdout.strip()
            commit = self._run("commit-tree", tree_sha, "-p", expected_state.token, "-m",
                               f"aacp: publish {publication.message.get('type', 'message')} "
                               f"{publication.message['message_id']} seq={int(publication.message['sequence'])}")
            return commit.stdout.strip()
        finally:
            try:
                os.unlink(index_path)
            except FileNotFoundError:
                pass

    def publish_cas(self, expected_state: CanonicalState,
                    publication: PreparedPublication) -> CasResult:
        self._validate_state(expected_state)
        if publication.expected_state != expected_state:
            raise ValueError("publication was prepared against a different canonical state")
        if self.read_canonical_state().token != expected_state.token:
            return CasConflict("head_moved")
        try:
            new_commit = self._commit_with_temp_index(expected_state, publication)
        except (subprocess.CalledProcessError, OSError) as exc:
            return CasUncertain(f"commit_failed:{type(exc).__name__}")
        push = self._run("push", self.remote, f"{new_commit}:{self.target_ref}", check=False)
        if push.returncode:
            stderr = push.stderr.lower()
            if "non-fast-forward" in stderr or "rejected" in stderr or "fetch first" in stderr:
                return CasConflict("head_moved")
            return CasUncertain("push_outcome_unknown")
        verified = self.read_canonical_state()
        if verified.token != new_commit:
            return CasUncertain("verify_head_mismatch")
        evidence = self.find_publication_evidence(verified, str(publication.message["message_id"]))
        if evidence is None or evidence.publication_commit != new_commit:
            return CasUncertain("verify_publication_missing")
        return CasSuccess(new_state=verified, message=publication.message, publication_commit=new_commit)

    def find_publication_evidence(self, state: CanonicalState, message_id: str) -> PublicationEvidence | None:
        self._validate_state(state)
        message = self.find_by_message_id(state, message_id)
        if message is None:
            return None
        log = self._run("log", "--format=%H", "--diff-filter=A", state.token, "--",
                        self._message_path(message)).stdout.splitlines()
        return PublicationEvidence(message, log[0]) if log else None

    def verify_publication(self, state: CanonicalState, message_id: str,
                           sequence: int | None = None) -> VerificationResult:
        self._validate_state(state)
        message = self.find_by_message_id(state, message_id)
        if message is None:
            return VerificationResult(False, reason="message_missing")
        if sequence is not None and int(message.get("sequence", -1)) != sequence:
            return VerificationResult(False, message=message, reason="sequence_mismatch")
        evidence = self.find_publication_evidence(state, message_id)
        if evidence is None:
            return VerificationResult(False, message=message, reason="publication_provenance_missing")
        return VerificationResult(True, message=message, publication_commit=evidence.publication_commit)
