import logging

logger = logging.getLogger(__name__)


class WeeklyFeedCreation:
    def __init__(self, feed_name, items):
        self.feed_name = feed_name
        self.items = items

    def create_feed(self):
        logger.info(f"Creating weekly feed: {self.feed_name}")
        feed_content = f"Weekly Feed: {self.feed_name}\n"
        feed_content += "\n".join(self.items)
        logger.info("Feed created successfully")
        return feed_content
