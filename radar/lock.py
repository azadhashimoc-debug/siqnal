import time


def acquire(d, now=None, ttl=3600) -> bool:
    """d is dict-like (modal.Dict in prod). Held locks younger than ttl block."""
    now = time.time() if now is None else now
    try:
        held = d["running"]
    except KeyError:
        held = None
    if held is not None and now - held < ttl:
        return False
    d["running"] = now
    return True


def release(d) -> None:
    try:
        d.pop("running")
    except KeyError:
        pass
