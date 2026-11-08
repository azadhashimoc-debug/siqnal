from radar import bot, lock


def run_locked(volume, votes, lock_dict, ttl, open_conn, job):
    """lock -> reload -> read votes/dashboard actions -> apply -> job -> volume.commit -> pop drained votes -> unlock.
    Votes are popped only after the volume commit, and only if unchanged since they were read."""
    if not lock.acquire(lock_dict, ttl=ttl):
        print("skipped: another run holds the lock")
        return None
    try:
        volume.reload()
        items = dict(votes.items())
        ok = False
        try:
            conn = open_conn()
            try:
                bot.drain_votes(conn, items)
                bot.drain_status(conn, items)
                result = job(conn)
            finally:
                conn.close()
            ok = True
        finally:
            volume.commit()  # keep paid work even when the job failed
        if ok:
            for k, v in items.items():
                if votes.get(k) == v:
                    try:
                        votes.pop(k)
                    except KeyError:
                        pass
        return result
    finally:
        lock.release(lock_dict)
