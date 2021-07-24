import traceback

import click

from taskw_gcal_sync.logger import logger, setup_logger
from taskw_gcal_sync.TWGCalAggregator import ItemType, TWGCalAggregator


@click.command()
@click.option(
    "-c",
    "--gcal-calendar",
    required=True,
    type=str,
    help="Name of the Google Calendar to sync (will be created if not there)",
)
@click.option(
    "--gcal-secret",
    required=False,
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help="Override the client secret used for the communication with the Google Calendar API",
)
@click.option(
    "-t",
    "--taskwarrior-tag",
    "tw_tags",
    required=True,
    type=str,
    help="Taskwarrior tags to sync",
    multiple=True,
)
@click.option(
    "-o",
    "--order-by",
    type=click.Choice(["description", "end", "entry", "id", "modified", "status", "urgency"]),
    help="Sort the tasks, based on this key and then register/modify/delete them",
)
@click.option(
    "--ascending-order/--descending-order",
    default=True,
    help="Specify ascending/descending order for the order-by option",
)
@click.option(
    "--oauth-port",
    default=8081,
    type=int,
    help="Port to use for oAuth Authentication with Google Calendar",
)
@click.option("-v", "--verbose", count=True, default=0)
def main(gcal_calendar, gcal_secret, tw_tags, order_by, ascending_order, verbose, oauth_port):
    """Main."""
    setup_logger(verbosity=verbose)
    if len(tw_tags) != 1:
        raise RuntimeError("Trying with multiple tags hasn't been tested yet. Exiting...")

    logger.info("Initialising...")
    tw_config = {"tags": list(tw_tags)}

    gcal_config = {"calendar_summary": gcal_calendar, "oauth_port": oauth_port}
    if gcal_secret:
        gcal_config["client_secret"] = gcal_secret

    try:
        with TWGCalAggregator(tw_config=tw_config, gcal_config=gcal_config) as aggregator:
            aggregator.start()

            # Check and potentially register items
            # tw
            tw_items = aggregator.tw_side.get_all_items(
                order_by=order_by, use_ascending_order=ascending_order
            )
            aggregator.register_items(tw_items, ItemType.TW)

            # gcal
            gcal_items = aggregator.gcal_side.get_all_items(
                order_by=order_by, use_ascending_order=ascending_order
            )
            aggregator.register_items(gcal_items, ItemType.GCAL)

            # Synchronise deleted items
            aggregator.synchronise_deleted_items(ItemType.TW)
            aggregator.synchronise_deleted_items(ItemType.GCAL)
    except KeyboardInterrupt:
        logger.info("Exiting...")
    except:
        logger.info(traceback.format_exc())
        logger.error(
            "Application failed, above you can find the error message, which you can use to"
            " create an issue at https://github.com/bergercookie/taskw_gcal_sync/issues."
        )


if __name__ == "__main__":
    main()