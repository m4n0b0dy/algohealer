import click

from algohealer.db.conn import SQLiteManager
from algohealer.manager import DataManager


@click.command()
@click.argument("site", required=True, type=str)
def cli(site: str) -> None:
    db_conn = SQLiteManager()

    manager = DataManager(site=site, db_conn=db_conn)
    if not manager.check_site():
        return

    manager.interact()
    db_conn.close()


if __name__ == "__main__":
    cli()
