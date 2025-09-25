"""
Auto-generated client for Legit Social API (dynamic from OpenAPI spec).

Features:
- Dynamic namespaced endpoints, e.g., client.auth.login(...)
- Multi-user session support via SessionStore (per-user tokens/cookies)
- Cursor-based pagination helper
- Built-in retry/backoff for 429/5xx
- Type hints for common call arguments

This file was generated from /mnt/data/legit-social-api.json.
"""
from __future__ import annotations

import time
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, Optional, Callable
import requests


class APIError(Exception):
    def __init__(self, status_code: int, message: str, payload: Optional[dict] = None):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.payload = payload or {}


@dataclass
class Endpoint:
    operation_id: str
    method: str
    path: str
    summary: str
    path_params: list[str]
    query_params: list[str]
    has_body: bool
    secure: bool
    ns: str
    name: str


class SessionStore:
    """
    Keeps separate requests.Session per user_key.
    You can set bearer tokens or cookies per user.
    """

    def __init__(self):
        self._sessions: dict[str, requests.Session] = {}
        self._tokens: dict[str, str] = {}  # bearer tokens
        self._cookies: dict[str, dict] = {}  # cookie dicts

    def get(self, user_key: str) -> requests.Session:
        if user_key not in self._sessions:
            s = requests.Session()
            # Optional: set default headers
            s.headers.update({
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "legit-social-client/1.0",
            })
            self._sessions[user_key] = s
        return self._sessions[user_key]

    def set_bearer(self, user_key: str, token: str):
        self._tokens[user_key] = token
        sess = self.get(user_key)
        sess.headers["Authorization"] = f"Bearer {token}"

    def clear_bearer(self, user_key: str):
        self._tokens.pop(user_key, None)
        sess = self.get(user_key)
        if "Authorization" in sess.headers:
            del sess.headers["Authorization"]

    def set_cookies(self, user_key: str, cookies: dict):
        self._cookies[user_key] = cookies
        sess = self.get(user_key)
        sess.cookies.update(cookies)

    def clear_cookies(self, user_key: str):
        self._cookies.pop(user_key, None)
        sess = self.get(user_key)
        sess.cookies.clear()


class LegitSocialAPI:
    def __init__(self, base_url: str, session_store: Optional[SessionStore] = None, default_user: str = "default"):
        self.base_url = base_url.rstrip("/")
        self.sessions = session_store or SessionStore()
        self.default_user = default_user
        self._endpoints: dict[str, Endpoint] = {}
        self._namespaces: dict[str, APINamespace] = {}

    def register_endpoint(self, ep: Endpoint):
        self._endpoints[ep.operation_id] = ep
        if ep.ns not in self._namespaces:
            self._namespaces[ep.ns] = APINamespace(self, ep.ns)
        self._namespaces[ep.ns]._register(ep)

    def __getattr__(self, item: str) -> "APINamespace":
        # allow access like client.auth.login
        if item in self._namespaces:
            return self._namespaces[item]
        raise AttributeError(item)

    # --- Core request machinery with simple retry/backoff ---
    def _request(self, op_id: str, *, user_key: Optional[str] = None,
                 path_params: Optional[dict] = None, query: Optional[dict] = None,
                 json_body: Optional[dict] = None, headers: Optional[dict] = None,
                 allow_redirects: bool = True, timeout: int = 90) -> dict:
        if op_id not in self._endpoints:
            raise ValueError(f"Unknown operation_id: {op_id}")
        ep = self._endpoints[op_id]
        user = user_key or self.default_user
        sess = self.sessions.get(user)

        # Build URL with path params
        path_params = path_params or {}
        url_path = ep.path
        for name in ep.path_params:
            if name not in path_params:
                raise ValueError(f"Missing path param '{name}' for {op_id}")
            url_path = url_path.replace(
                "{" + name + "}", str(path_params[name]))
        url = self.base_url + url_path

        # Prepare request
        req_headers = dict(sess.headers)
        if headers:
            req_headers.update(headers)

        params = {k: v for k, v in (query or {}).items() if v is not None}

        data = None
        json_payload = None
        if ep.has_body:
            json_payload = json_body or {}

        # Retry policy: up to 3 retries on 429/5xx with exponential backoff
        backoff = 1.0
        for attempt in range(4):
            resp = sess.request(
                ep.method,
                url,
                params=params,
                json=json_payload,
                data=data,
                headers=req_headers,
                allow_redirects=allow_redirects,
                timeout=timeout,
            )
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(backoff)
                backoff *= 2
                continue

            if resp.status_code >= 400:
                try:
                    payload = resp.json()
                except Exception:
                    payload = {}
                message = payload.get("message") or resp.text
                raise APIError(resp.status_code, message, payload)

            try:
                return resp.json()
            except Exception:
                return {"raw": resp.text}

    # Helper for cursor-based pagination common in this API
    def paginate(self, op: Callable[..., dict], *, user_key: Optional[str] = None,
                 path_params: Optional[dict] = None, query: Optional[dict] = None,
                 json_body: Optional[dict] = None) -> Iterator[dict]:
        q = dict(query or {})
        cursor_key = "cursor"
        while True:
            payload = op(user_key=user_key, path_params=path_params,
                         query=q, json_body=json_body)
            data = payload.get("data", [])
            paging = payload.get("paging") or {}
            for item in (data or []):
                yield item
            has_next = paging.get("has_next")
            next_cursor = paging.get("next_cursor")
            if has_next and next_cursor:
                q[cursor_key] = next_cursor
            else:
                break


class APINamespace:
    def __init__(self, client: LegitSocialAPI, name: str):
        self._client = client
        self._name = name
        self._ops: dict[str, Endpoint] = {}

    def _register(self, ep: Endpoint):
        self._ops[ep.name] = ep

    def __getattr__(self, item: str) -> Callable[..., dict]:
        if item not in self._ops:
            raise AttributeError(item)
        ep = self._ops[item]

        def caller(*, user_key: Optional[str] = None,
                   path_params: Optional[dict] = None,
                   query: Optional[dict] = None,
                   json_body: Optional[dict] = None,
                   headers: Optional[dict] = None,
                   allow_redirects: bool = True,
                   timeout: int = 90) -> dict:
            return self._client._request(
                ep.operation_id,
                user_key=user_key,
                path_params=path_params,
                query=query,
                json_body=json_body,
                headers=headers,
                allow_redirects=allow_redirects,
                timeout=timeout,
            )

        caller.__name__ = ep.name
        caller.__doc__ = f"{ep.method} {ep.path}\nSummary: {ep.summary}\nOperationId: {ep.operation_id}"
        return caller


def build_client(base_url: str) -> LegitSocialAPI:
    client = LegitSocialAPI(base_url)
    # Namespace: auth
    client.register_endpoint(Endpoint(operation_id='auth.change_password', method='POST', path='/api/auth/change-password',
                             summary="change_password", path_params=[], query_params=[], has_body=True, secure=True, ns='auth', name='change_password'))
    client.register_endpoint(Endpoint(operation_id='auth.login', method='POST', path='/api/auth/login',
                             summary="login", path_params=[], query_params=[], has_body=True, secure=False, ns='auth', name='login'))
    client.register_endpoint(Endpoint(operation_id='auth.logout', method='POST', path='/api/auth/logout',
                             summary="logout", path_params=[], query_params=[], has_body=False, secure=True, ns='auth', name='logout'))
    client.register_endpoint(Endpoint(operation_id='auth.register', method='POST', path='/api/auth/register',
                             summary="register", path_params=[], query_params=[], has_body=True, secure=False, ns='auth', name='register'))
    client.register_endpoint(Endpoint(operation_id='auth.register_team', method='POST', path='/api/auth/register-team',
                             summary="register_team", path_params=[], query_params=[], has_body=True, secure=False, ns='auth', name='register_team'))

    # Namespace: feeds
    client.register_endpoint(Endpoint(operation_id='feeds.list', method='GET', path='/api/feeds/', summary="list",
                             path_params=[], query_params=[], has_body=False, secure=False, ns='feeds', name='list'))
    client.register_endpoint(Endpoint(operation_id='feeds.get', method='GET', path='/api/feeds/{key}', summary="get", path_params=[
    ], query_params=['cursor'], has_body=False, secure=False, ns='feeds', name='get'))

    # Namespace: globals
    client.register_endpoint(Endpoint(operation_id='globals.get', method='GET', path='/api/globals/',
                             summary="get", path_params=[], query_params=[], has_body=False, secure=False, ns='globals', name='get'))

    # Namespace: notifications
    client.register_endpoint(Endpoint(operation_id='notifications.all', method='GET', path='/api/notifications/', summary="all",
                             path_params=[], query_params=['cursor'], has_body=False, secure=True, ns='notifications', name='all'))
    client.register_endpoint(Endpoint(operation_id='notifications.clear_notifications', method='DELETE', path='/api/notifications/clear',
                             summary="clear_notifications", path_params=[], query_params=[], has_body=False, secure=True, ns='notifications', name='clear_notifications'))
    client.register_endpoint(Endpoint(operation_id='notifications.count_all', method='GET', path='/api/notifications/count',
                             summary="count_all", path_params=[], query_params=[], has_body=False, secure=True, ns='notifications', name='count_all'))
    client.register_endpoint(Endpoint(operation_id='notifications.unread', method='GET', path='/api/notifications/unread',
                             summary="unread", path_params=[], query_params=['cursor'], has_body=False, secure=True, ns='notifications', name='unread'))
    client.register_endpoint(Endpoint(operation_id='notifications.count_unread', method='GET', path='/api/notifications/unread/count',
                             summary="count_unread", path_params=[], query_params=[], has_body=False, secure=True, ns='notifications', name='count_unread'))
    client.register_endpoint(Endpoint(operation_id='notifications.delete_notification', method='DELETE', path='/api/notifications/{notification}', summary="delete_notification", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='notifications', name='delete_notification'))
    client.register_endpoint(Endpoint(operation_id='notifications.mark_as_read', method='POST', path='/api/notifications/{notification}/mark-read', summary="mark_as_read", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='notifications', name='mark_as_read'))
    client.register_endpoint(Endpoint(operation_id='notifications.mark_as_unread', method='POST', path='/api/notifications/{notification}/mark-unread', summary="mark_as_unread", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='notifications', name='mark_as_unread'))

    # Namespace: search
    client.register_endpoint(Endpoint(operation_id='search.get', method='GET', path='/api/search', summary="get",
                             path_params=[], query_params=['query', 'cursor'], has_body=False, secure=False, ns='search', name='get'))

    # Namespace: tags
    client.register_endpoint(Endpoint(operation_id='tags.get', method='GET', path='/api/tags/lookup/{name}', summary="get", path_params=[
    ], query_params=[], has_body=False, secure=False, ns='tags', name='get'))
    client.register_endpoint(Endpoint(operation_id='tags.latest', method='GET', path='/api/tags/lookup/{name}/latest', summary="latest", path_params=[
    ], query_params=['cursor'], has_body=False, secure=False, ns='tags', name='latest'))
    client.register_endpoint(Endpoint(operation_id='tags.trending', method='GET', path='/api/tags/trending',
                             summary="trending", path_params=[], query_params=[], has_body=False, secure=False, ns='tags', name='trending'))

    # Namespace: posts
    client.register_endpoint(Endpoint(operation_id='posts.create', method='POST', path='/api/twoots/',
                             summary="create", path_params=[], query_params=[], has_body=True, secure=True, ns='posts', name='create'))
    client.register_endpoint(Endpoint(operation_id='posts.delete', method='DELETE', path='/api/twoots/{post}/', summary="delete", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='posts', name='delete'))
    client.register_endpoint(Endpoint(operation_id='posts.get', method='GET', path='/api/twoots/{post}/', summary="get", path_params=[
    ], query_params=[], has_body=False, secure=False, ns='posts', name='get'))
    client.register_endpoint(Endpoint(operation_id='posts.get_embed', method='GET', path='/api/twoots/{post}/embed', summary="get_embed", path_params=[
    ], query_params=[], has_body=False, secure=False, ns='posts', name='get_embed'))
    client.register_endpoint(Endpoint(operation_id='posts.undo_like', method='DELETE', path='/api/twoots/{post}/like', summary="undo_like", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='posts', name='undo_like'))
    client.register_endpoint(Endpoint(operation_id='posts.like', method='POST', path='/api/twoots/{post}/like', summary="like", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='posts', name='like'))
    client.register_endpoint(Endpoint(operation_id='posts.set_prompt_injection', method='POST', path='/api/twoots/{post}/prompt-injection', summary="set_prompt_injection", path_params=[
    ], query_params=[], has_body=True, secure=False, ns='posts', name='set_prompt_injection'))
    client.register_endpoint(Endpoint(operation_id='posts.get_replies', method='GET', path='/api/twoots/{post}/replies', summary="get_replies", path_params=[
    ], query_params=['cursor'], has_body=False, secure=False, ns='posts', name='get_replies'))
    client.register_endpoint(Endpoint(operation_id='posts.report_post', method='POST', path='/api/twoots/{post}/report', summary="report_post", path_params=[
    ], query_params=[], has_body=True, secure=True, ns='posts', name='report_post'))
    client.register_endpoint(Endpoint(operation_id='posts.undo_repost', method='DELETE', path='/api/twoots/{post}/repost', summary="undo_repost", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='posts', name='undo_repost'))
    client.register_endpoint(Endpoint(operation_id='posts.repost', method='POST', path='/api/twoots/{post}/repost', summary="repost", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='posts', name='repost'))
    client.register_endpoint(Endpoint(operation_id='posts.set_post_visibility', method='POST', path='/api/twoots/{post}/visibility', summary="set_post_visibility", path_params=[
    ], query_params=[], has_body=True, secure=False, ns='posts', name='set_post_visibility'))

    # Namespace: users
    client.register_endpoint(Endpoint(operation_id='users.me', method='GET', path='/api/users/me',
                             summary="me", path_params=[], query_params=[], has_body=False, secure=False, ns='users', name='me'))
    client.register_endpoint(Endpoint(operation_id='users.update_profile', method='POST', path='/api/users/me',
                             summary="update_profile", path_params=[], query_params=[], has_body=True, secure=True, ns='users', name='update_profile'))
    client.register_endpoint(Endpoint(operation_id='users.get', method='GET', path='/api/users/{user}/', summary="get", path_params=[
    ], query_params=[], has_body=False, secure=False, ns='users', name='get'))
    client.register_endpoint(Endpoint(operation_id='users.get_activity', method='GET', path='/api/users/{user}/activity', summary="get_activity", path_params=[
    ], query_params=['cursor'], has_body=False, secure=False, ns='users', name='get_activity'))
    client.register_endpoint(Endpoint(operation_id='users.undo_follow', method='DELETE', path='/api/users/{user}/follow', summary="undo_follow", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='users', name='undo_follow'))
    client.register_endpoint(Endpoint(operation_id='users.follow', method='POST', path='/api/users/{user}/follow', summary="follow", path_params=[
    ], query_params=[], has_body=False, secure=True, ns='users', name='follow'))
    client.register_endpoint(Endpoint(operation_id='users.get_followers', method='GET', path='/api/users/{user}/followers', summary="get_followers", path_params=[
    ], query_params=['cursor'], has_body=False, secure=False, ns='users', name='get_followers'))
    client.register_endpoint(Endpoint(operation_id='users.get_follows', method='GET', path='/api/users/{user}/follows', summary="get_follows", path_params=[
    ], query_params=['cursor'], has_body=False, secure=False, ns='users', name='get_follows'))

    return client


# ---------------- Convenience helpers ----------------

def login_user(client: LegitSocialAPI, user_key: str, username: str, password: str) -> dict:
    """
    Logs in and captures bearer token (if returned in a cookie or in the payload).
    """
    payload = client.auth.login(user_key=user_key, json_body={
                                "username": username, "password": password})
    # If server issues tokens via cookies, nothing to do (requests.Session keeps them).
    # If token is returned in payload, set it here (adjust key if API returns differently).
    # Example (uncomment if applicable):
    # token = payload.get("data", {}).get("token")
    # if token:
    #     client.sessions.set_bearer(user_key, token)
    return payload


def logout_user(client: LegitSocialAPI, user_key: str) -> dict:
    payload = client.auth.logout(user_key=user_key)
    # Clear local auth
    client.sessions.clear_bearer(user_key)
    client.sessions.clear_cookies(user_key)
    return payload


def create_post(client: LegitSocialAPI, user_key: str, content: str, parent_id: int | None = None,
                embed: str | None = None, media: list[str] | None = None) -> dict:
    body = {"content": content, "parent_id": parent_id}
    if embed is not None:
        body["embed"] = embed
    if media is not None:
        body["media"] = media
    return client.posts.create(user_key=user_key, json_body=body)


def like_post(client: LegitSocialAPI, user_key: str, post_id: int) -> dict:
    return client.posts.like(user_key=user_key, path_params={"post": post_id})


def unlike_post(client: LegitSocialAPI, user_key: str, post_id: int) -> dict:
    return client.posts.undo_like(user_key=user_key, path_params={"post": post_id})


def repost(client: LegitSocialAPI, user_key: str, post_id: int) -> dict:
    return client.posts.repost(user_key=user_key, path_params={"post": post_id})


def undo_repost(client: LegitSocialAPI, user_key: str, post_id: int) -> dict:
    return client.posts.undo_repost(user_key=user_key, path_params={"post": post_id})


def get_user_feed(client: LegitSocialAPI, user_key: str, feed_key: str, cursor: str | None = None) -> dict:
    q = {}
    if cursor is not None:
        q["cursor"] = cursor
    return client.feeds.get(user_key=user_key, path_params={"key": feed_key}, query=q)


def paginate_user_feed(client: LegitSocialAPI, user_key: str, feed_key: str):
    return client.paginate(
        client.feeds.get,
        user_key=user_key,
        path_params={"key": feed_key},
        query={},
    )


def update_profile(client: LegitSocialAPI, user_key: str, display_name: str, bio: str) -> dict:
    return client.users.update_profile(user_key=user_key, json_body={"display_name": display_name, "bio": bio})


def follow_user(client: LegitSocialAPI, user_key: str, target: int | str) -> dict:
    return client.users.follow(user_key=user_key, path_params={"user": target})


def unfollow_user(client: LegitSocialAPI, user_key: str, target: int | str) -> dict:
    return client.users.undo_follow(user_key=user_key, path_params={"user": target})
