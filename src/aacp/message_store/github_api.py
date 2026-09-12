"""GitHub Git Data API Message Store backend.

Implements the same transport-neutral MessageStore semantics as the Git CLI
backend, using GitHub's Git Data API and an optimistic ref update as CAS.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

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


class GitHubAPIError(RuntimeError):
    """GitHub API request failed."""


class GitHubMessageStore:
    """GitHub Git Data API implementation of the MessageStore contract."""

    def __init__(
        self,
        *,
        owner: str,
        repo: str,
        target_ref: str,
        conversation_id: str,
        stream_id: str,
        token: str,
        api_base: str = "https://api.github.com",
        opener: Callable[..., Any] | None = None,
    ) -> None:
        if not target_ref.startswith("refs/heads/"):
            raise ValueError("GitHubMessageStore requires refs/heads/<branch> target_ref")
        if not owner or not repo or not conversation_id or not stream_id or not token:
            raise ValueError("owner, repo, conversation_id, stream_id and token are required")
        self.owner = owner
        self.repo = repo
        self.target_ref = target_ref
        self.conversation_id = conversation_id
        self.stream_id = stream_id
        self.token = token
        self.api_base = api_base.rstrip("/")
        self._opener = opener or urlopen
        self.messages_prefix = f".aacp/conversations/{conversation_id}/messages"

    @property
    def branch(self) -> str:
        return self.target_ref.removeprefix("refs/heads/")

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
        request = Request(
            f"{self.api_base}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with self._opener(request) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            if exc.code in (409, 422):
                raise CasConflict(f"github_http_{exc.code}:{detail}") from exc
            raise GitHubAPIError(f"github_http_{exc.code}:{detail}") from exc
        return json.loads(raw.decode("utf-8")) if raw else None

    def _ref(self) -> dict[str, Any]:
        return self._request("GET", f"/repos/{self.owner}/{self.repo}/git/ref/{self.target_ref.removeprefix('refs/')}")

    def read_canonical_state(self) -> CanonicalState:
        ref = self._ref()
        return CanonicalState(ref["object"]["sha"], self.target_ref, self.stream_id)

    def _validate_state(self, state: CanonicalState) -> None:
        if state.target_ref != self.target_ref:
            raise ValueError("canonical target_ref does not match MessageStore binding")
        if state.stream_id != self.stream_id:
            raise ValueError("canonical stream_id does not match MessageStore binding")

    @staticmethod
    def _decode(value: str) -> dict[str, Any]:
        return json.loads(base64.b64decode(value).decode("utf-8"))

    def _tree(self, commit_sha: str) -> list[dict[str, Any]]:
        commit = self._request("GET", f"/repos/{self.owner}/{self.repo}/git/commits/{commit_sha}")
        tree_sha = commit["tree"]["sha"]
        tree = self._request("GET", f"/repos/{self.owner}/{self.repo}/git/trees/{tree_sha}?recursive=1")
        return tree.get("tree", [])

    def list_messages(self, state: CanonicalState) -> list[dict[str, Any]]:
        self._validate_state(state)
        messages: list[dict[str, Any]] = []
        prefix = self.messages_prefix + "/"
        for item in self._tree(state.token):
            path = item.get("path", "")
            if not path.startswith(prefix) or not path.endswith(".json"):
                continue
            blob = self._request("GET", f"/repos/{self.owner}/{self.repo}/git/blobs/{item['sha']}")
            message = self._decode(blob["content"])
            if message.get("stream_id") == self.stream_id:
                messages.append(message)
        return messages

    def find_by_message_id(self, state: CanonicalState, message_id: str) -> dict[str, Any] | None:
        return next((m for m in self.list_messages(state) if m.get("message_id") == message_id), None)

    def _message_path(self, message: dict[str, Any]) -> str:
        return f"{self.messages_prefix}/{int(message['sequence']):06d}-{message['message_id']}.json"

    @staticmethod
    def _serialize(message: dict[str, Any]) -> str:
        return json.dumps(message, ensure_ascii=False, indent=2) + "\n"

    def prepare_publication(self, state: CanonicalState, message: dict[str, Any]) -> PreparedPublication:
        self._validate_state(state)
        if message.get("conversation_id") != self.conversation_id:
            raise ValueError("message conversation_id does not match MessageStore binding")
        if message.get("stream_id") != self.stream_id:
            raise ValueError("message stream_id does not match MessageStore binding")
        if int(message.get("sequence", 0)) <= 0:
            raise ValueError("ordered publication requires a positive sequence")
        if not message.get("message_id"):
            raise ValueError("message_id is required")
        return PreparedPublication(state, dict(message))

    def publish_cas(self, expected_state: CanonicalState, publication: PreparedPublication) -> CasResult:
        self._validate_state(expected_state)
        if publication.expected_state != expected_state:
            raise ValueError("publication was prepared against a different canonical state")
        try:
            current = self.read_canonical_state()
        except Exception:
            return CasUncertain("read_before_publish_failed")
        if current.token != expected_state.token:
            return CasConflict("head_moved")
        path = self._message_path(publication.message)
        content = base64.b64encode(self._serialize(publication.message).encode()).decode()
        try:
            blob = self._request("POST", f"/repos/{self.owner}/{self.repo}/git/blobs", {"content": content, "encoding": "base64"})
            commit = self._request("GET", f"/repos/{self.owner}/{self.repo}/git/commits/{expected_state.token}")
            tree = self._request("POST", f"/repos/{self.owner}/{self.repo}/git/trees", {
                "base_tree": commit["tree"]["sha"],
                "tree": [{"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]}],
            })
            new_commit = self._request("POST", f"/repos/{self.owner}/{self.repo}/git/commits", {
                "message": f"aacp: publish {publication.message.get('type', 'message')} {publication.message['message_id']} seq={int(publication.message['sequence'])}",
                "tree": tree["sha"],
                "parents": [expected_state.token],
            })
        except CasConflict:
            return CasConflict("head_moved")
        except Exception as exc:
            return CasUncertain(f"object_creation_failed:{type(exc).__name__}")
        try:
            self._request("PATCH", f"/repos/{self.owner}/{self.repo}/git/refs/{self.target_ref.removeprefix('refs/')}", {
                "sha": new_commit["sha"],
                "force": False,
            })
        except CasConflict:
            return CasConflict("head_moved")
        except Exception:
            return CasUncertain("ref_update_outcome_unknown")
        try:
            verified = self.read_canonical_state()
        except Exception:
            return CasUncertain("verify_head_failed")
        if verified.token != new_commit["sha"]:
            return CasUncertain("verify_head_mismatch")
        evidence = self.find_publication_evidence(verified, str(publication.message["message_id"]))
        if evidence is None or evidence.publication_commit != new_commit["sha"]:
            return CasUncertain("verify_publication_missing")
        return CasSuccess(new_state=verified, message=publication.message, publication_commit=new_commit["sha"])

    def find_publication_evidence(self, state: CanonicalState, message_id: str) -> PublicationEvidence | None:
        self._validate_state(state)
        message = self.find_by_message_id(state, message_id)
        if message is None:
            return None
        commits = self._request("GET", f"/repos/{self.owner}/{self.repo}/commits?path={self._message_path(message)}&sha={state.token}")
        if not commits:
            return None
        return PublicationEvidence(message, commits[-1]["sha"])

    def verify_publication(self, state: CanonicalState, message_id: str, sequence: int | None = None) -> VerificationResult:
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
