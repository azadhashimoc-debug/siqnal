import argparse
import logging
import sys

from radar import bot, config, db, pipeline


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="radar")
    ap.add_argument("command", choices=["collect", "weekly"])
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    conn = db.connect(config.DB_PATH)
    db.migrate(conn)
    if args.command == "collect":
        result = pipeline.run_collect(conn)
        for name, n in result.items():
            print(f"{name}: {n}")
    else:
        pipeline.run_weekly(conn, pipeline.make_client(), bot.telegram_post)
    return 0


if __name__ == "__main__":
    sys.exit(main())
