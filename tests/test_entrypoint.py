from scripts import entrypoint


def test_entrypoint_waits_after_cli_error(monkeypatch):
    waits: list[bool] = []

    def fail() -> int:
        raise SystemExit(2)

    monkeypatch.setattr(entrypoint, "main", fail)
    monkeypatch.setattr(entrypoint, "_wait_for_key", lambda: waits.append(True))

    assert entrypoint.run() == 2
    assert waits == [True]


def test_entrypoint_displays_unexpected_error_and_waits(monkeypatch, capsys):
    waits: list[bool] = []

    def fail() -> int:
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(entrypoint, "main", fail)
    monkeypatch.setattr(entrypoint, "_wait_for_key", lambda: waits.append(True))

    assert entrypoint.run() == 1
    assert waits == [True]
    assert "RuntimeError: unexpected failure" in capsys.readouterr().err


def test_entrypoint_does_not_wait_after_success(monkeypatch):
    waits: list[bool] = []
    monkeypatch.setattr(entrypoint, "main", lambda: 0)
    monkeypatch.setattr(entrypoint, "_wait_for_key", lambda: waits.append(True))

    assert entrypoint.run() == 0
    assert waits == []
