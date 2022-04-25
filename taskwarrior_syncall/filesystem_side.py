from pathlib import Path
from typing import MutableMapping, Optional, Sequence

from item_synchronizer.types import ID
from loguru import logger

from taskwarrior_syncall.concrete_item import ConcreteItem, ItemKey
from taskwarrior_syncall.filesystem_file import FilesystemFile
from taskwarrior_syncall.sync_side import ItemType, SyncSide


class FilesystemSide(SyncSide):
    """Integration for managing files in a local filesystem.

    - Embed the UUID as an extended attribute of each file.
    """

    @classmethod
    def id_key(cls) -> str:
        return "id"

    @classmethod
    def summary_key(cls) -> str:
        return "title"

    def __init__(self, filesystem_root: Path) -> None:
        pass
        self._filesystem_root = filesystem_root

        all_items = self.get_all_items()
        self._items_cache: MutableMapping[str, FilesystemFile] = {
            item.id: item for item in all_items
        }

    def start(self):
        pass

    def finish(self):
        for item in self._items_cache.values():
            item.flush()
        pass

    def get_all_items(self, **kargs) -> Sequence[FilesystemFile]:
        return tuple(FilesystemFile(path=p) for p in self._filesystem_root.iterdir())

    def get_item(self, item_id: ID, use_cached: bool = False) -> Optional[FilesystemFile]:
        if use_cached is True:
            return self._get_item_refresh(item_id=item_id)

        return self._items_cache.get(item_id, None)

    def _get_item_refresh(self, item_id: ID) -> Optional[FilesystemFile]:
        """Search for the FilesystemFile in the root directory given its ID."""
        all_paths = self._filesystem_root.iterdir()
        matching_paths = [
            path for path in all_paths if FilesystemFile.get_id_of_path(path) == item_id
        ]
        if len(matching_paths) > 1:
            logger.warning(
                f"Found {len(matching_paths)} paths with the item ID [{item_id}]."
                "Arbitrarily returning the first item."
            )
        elif len(matching_paths) == 0:
            return None

        return FilesystemFile(matching_paths[0])

    def delete_single_item(self, item_id: ID):
        raise NotImplementedError("Should be implemented in derived")

    def update_item(self, item_id: ID, **changes):
        raise NotImplementedError("Should be implemented in derived")

    def add_item(self, item: FilesystemFile) -> FilesystemFile:
        raise NotImplementedError("Implement this")

    @classmethod
    def items_are_identical(
        cls, item1: ConcreteItem, item2: ConcreteItem, ignore_keys: Sequence[str] = []
    ) -> bool:
        ignore_keys_ = ["last_edited_time"]
        ignore_keys_.extend(ignore_keys)
        return item1.compare(item2, ignore_keys=ignore_keys_)
        return True
