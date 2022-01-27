"""Music to notion."""

import os

import my_chrome_bookmarks
import notion_client


class NotionAPI:
    """Notion API."""

    def __init__(self) -> None:
        self._notion = notion_client.Client(
            auth=os.environ["NOTION_TOKEN"],
            # log_level=logging.DEBUG,
        )


class Database:
    def __init__(self) -> None:
        pass


def main():
    bookmarks = my_chrome_bookmarks.bookmark_bar()
    songs = bookmarks["Songs"].urls_flat
    print(f"Extracted {len(songs)} songs")

    notion = NotionAPI()
    # print(songs)


if __name__ == "__main__":
    main()
