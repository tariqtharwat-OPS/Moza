import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from moza_orchestrator.orchestrator import MozaOrchestrator


def _config(**overrides):
    cfg = {
        "ranking": [
            {"rank": 1, "provider": "groq", "model": "llama-3.3-70b-versatile",
             "ctx": 128000, "rpm": 30, "tpm": 5000},
            {"rank": 2, "provider": "github", "model": "gpt-4o-mini",
             "ctx": 128000, "rpm": 30, "tpm": 5000},
        ],
        "apiKeys": {"groq": "sk-test", "github": "sk-test2"},
        "baseURLs": {"groq": "https://api.groq.com/openai/v1",
                     "github": "https://models.github.ai/inference"},
        "routing_rules": [],
        "fallback_chain": [],
    }
    cfg.update(overrides)
    return cfg


@pytest.fixture
def orch(tmp_path):
    with patch.dict(os.environ, {}, clear=True):
        return MozaOrchestrator(ranking_config=_config())


class FakeResponse:
    def __init__(self, ip):
        self._ip = ip
        self.status_code = 200

    def json(self):
        return {"ip": self._ip}


class FakeClock:
    """Controllable clock so timeout loops terminate instantly in tests."""

    def __init__(self, start=0.0):
        self.now = start

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def _patch_clock():
    clock = FakeClock()
    return clock, [
        patch("moza_orchestrator.orchestrator.time.time", side_effect=clock.time),
        patch("moza_orchestrator.orchestrator.time.sleep", side_effect=clock.sleep),
    ]


class TestGetPublicIp:
    def test_returns_ip_on_success(self, orch):
        with patch("moza_orchestrator.orchestrator.httpx.get", return_value=FakeResponse("1.2.3.4")):
            assert orch._get_public_ip() == "1.2.3.4"

    def test_returns_none_on_http_error(self, orch):
        resp = FakeResponse("x")
        resp.status_code = 500
        with patch("moza_orchestrator.orchestrator.httpx.get", return_value=resp):
            assert orch._get_public_ip() is None

    def test_returns_none_on_network_error(self, orch):
        with patch("moza_orchestrator.orchestrator.httpx.get", side_effect=RuntimeError("boom")):
            assert orch._get_public_ip() is None

    def test_returns_none_when_ip_missing(self, orch):
        resp = FakeResponse("x")
        resp.json = lambda: {}
        with patch("moza_orchestrator.orchestrator.httpx.get", return_value=resp):
            assert orch._get_public_ip() is None


class TestWaitForIpChange:
    def test_returns_new_ip_when_changed(self, orch):
        clock, patches = _patch_clock()
        with patches[0], patches[1]:
            with patch(
                "moza_orchestrator.orchestrator.httpx.get",
                return_value=FakeResponse("9.9.9.9"),
            ):
                assert orch._wait_for_ip_change("1.2.3.4") == "9.9.9.9"

    def test_returns_none_on_timeout(self, orch):
        clock, patches = _patch_clock()
        with patches[0], patches[1]:
            with patch(
                "moza_orchestrator.orchestrator.httpx.get",
                return_value=FakeResponse("1.2.3.4"),
            ):
                assert orch._wait_for_ip_change("1.2.3.4") is None

    def test_returns_new_ip_only_after_some_polls(self, orch):
        clock, patches = _patch_clock()
        responses = [FakeResponse("1.2.3.4"), FakeResponse("1.2.3.4"), FakeResponse("5.6.7.8")]
        with patches[0], patches[1]:
            with patch(
                "moza_orchestrator.orchestrator.httpx.get",
                side_effect=responses,
            ):
                assert orch._wait_for_ip_change("1.2.3.4") == "5.6.7.8"


class TestMaybeRotateVpn:
    def _block_two(self, orch):
        now = time.time() + 300
        orch.blocked_providers = {"groq": now, "github": now}

    def test_no_rotation_when_fewer_than_two_blocked(self, orch):
        orch.blocked_providers = {"groq": time.time() + 300}
        with patch("moza_orchestrator.orchestrator.subprocess.Popen") as popen:
            assert orch._maybe_rotate_vpn() is False
            popen.assert_not_called()

    def test_returns_false_when_script_missing(self, orch):
        self._block_two(orch)
        with patch("moza_orchestrator.orchestrator.ROTATE_VPN_SCRIPT", Path("nonexistent") / "rotate_vpn.py"):
            with patch("moza_orchestrator.orchestrator.subprocess.Popen") as popen:
                assert orch._maybe_rotate_vpn() is False
                popen.assert_not_called()

    def test_triggers_rotation_and_confirms_ip_change(self, orch):
        self._block_two(orch)
        clock, patches = _patch_clock()
        responses = [FakeResponse("1.2.3.4"), FakeResponse("9.9.9.9")]
        with patches[0], patches[1]:
            with patch("moza_orchestrator.orchestrator.httpx.get", side_effect=responses):
                with patch("moza_orchestrator.orchestrator.subprocess.Popen") as popen:
                    assert orch._maybe_rotate_vpn() is True
                    popen.assert_called_once()

    def test_returns_false_on_timeout(self, orch):
        self._block_two(orch)
        clock, patches = _patch_clock()
        with patches[0], patches[1]:
            with patch(
                "moza_orchestrator.orchestrator.httpx.get",
                return_value=FakeResponse("1.2.3.4"),
            ):
                with patch("moza_orchestrator.orchestrator.subprocess.Popen"):
                    assert orch._maybe_rotate_vpn() is False

    def test_assumes_worked_when_ip_check_fails_before_rotation(self, orch):
        self._block_two(orch)
        clock, patches = _patch_clock()
        with patches[0], patches[1]:
            with patch(
                "moza_orchestrator.orchestrator.httpx.get",
                side_effect=RuntimeError("no network"),
            ):
                with patch("moza_orchestrator.orchestrator.subprocess.Popen") as popen:
                    assert orch._maybe_rotate_vpn() is True
                    popen.assert_not_called()

    def test_returns_false_when_rotation_trigger_fails(self, orch):
        self._block_two(orch)
        with patch(
            "moza_orchestrator.orchestrator.httpx.get",
            return_value=FakeResponse("1.2.3.4"),
        ):
            with patch(
                "moza_orchestrator.orchestrator.subprocess.Popen",
                side_effect=RuntimeError("popen failed"),
            ):
                assert orch._maybe_rotate_vpn() is False
