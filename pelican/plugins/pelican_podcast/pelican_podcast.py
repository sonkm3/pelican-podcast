"""
iTunes Feed Generator for Pelican.
"""
from collections.abc import Iterable
import logging
import os

from feedgenerator import Rss201rev2Feed
from feedgenerator.django.utils.feedgenerator import rfc2822_date
from jinja2 import Markup
import mutagen
import six

from pelican import signals
from pelican.generators import Generator
from pelican.utils import set_date_tzinfo
from pelican.writers import Writer

logger = logging.getLogger(__name__)

ITEM_ELEMENTS = (
    "title",
    "itunes:author",
    "itunes:subtitle",
    "itunes:summary",
    "itunes:image",
    "enclosure",
    "description",
    "link",
    "guid",
    "pubDate",
    "itunes:duration",
)
DEFAULT_ITEM_ELEMENTS = {k: None for k in ITEM_ELEMENTS}

SUPPORTED_MIME_TYPES = [
    "audio/x-m4a",
    "audio/mpeg",
    "video/quicktime",
    "video/mp4",
    "video/x-m4v",
    "application/pdf ",
]


class PodcastFeed(Rss201rev2Feed):
    """Helper class which generates the XML based in the global settings"""

    def __init__(self, *args, **kwargs):
        super(PodcastFeed, self).__init__(*args, **kwargs)
        self.settings = kwargs.get("settings")

    def rss_attributes(self):
        """Returns the podcast feed's attributes.

        :return: A dictionary containing the feed's attributes.
        """
        attrs = {}
        attrs["xmlns:itunes"] = "http://www.itunes.com/dtds/podcast-1.0.dtd"
        attrs["version"] = "2.0"
        attrs["xmlns:content"] = "http://purl.org/rss/1.0/modules/content/"
        return attrs

    def add_root_elements(self, handler):
        """Adds some basic but useful attributes for an iTunes feed.

        :param handler: A SimplerXMLGenerator instance.
        """
        super(PodcastFeed, self).add_root_elements(handler)

        def add_element(handler, *args):
            if len(args) == 2:
                args = args + (None,)
            element_name, _key, attr = args
            if _key in self.settings:
                if attr is None:
                    handler.addQuickElement(element_name, self.settings[_key])
                else:
                    handler.addQuickElement(
                        element_name, attrs={attr: self.settings[_key]}
                    )

        settings_map = [
            ["itunes:author", "PODCAST_FEED_AUTHOR"],
            ["itunes:explicit", "PODCAST_FEED_EXPLICIT"],
            ["itunes:subtitle", "PODCAST_FEED_SUBTITLE"],
            ["itunes:summary", "PODCAST_FEED_SUMMARY"],
            ["language", "PODCAST_FEED_LANGUAGE"],
            ["copyright", "PODCAST_FEED_COPYRIGHT"],
            ["itunes:image", "PODCAST_FEED_IMAGE", "href"],
        ]

        for setting_map in settings_map:
            add_element(handler, *setting_map)

        # Adds a feed owner root tag an some child tags. Ex:
        #  <itunes:owner>
        #    <itunes:name>John Doe</itunes:name>
        #    <itunes:email>john.doe@example.com</itunes:email>
        #  </itunes:owner>
        if "PODCAST_FEED_OWNER_NAME" and "PODCAST_FEED_OWNER_EMAIL" in self.settings:
            handler.startElement("itunes:owner", {})
            handler.addQuickElement(
                "itunes:name", self.settings["PODCAST_FEED_OWNER_NAME"]
            )
            handler.addQuickElement(
                "itunes:email", self.settings["PODCAST_FEED_OWNER_EMAIL"]
            )
            handler.endElement("itunes:owner")

        # Adds a show category root tag and some child tags. Ex:
        #  <itunes:category text="Technology">
        #   <itunes:category text="Gadgets"/>
        #  </itunes:category>
        if "PODCAST_FEED_CATEGORY" in self.settings:

            def category_element(categories, is_top=True):
                if isinstance(categories, str):
                    return handler.addQuickElement(
                        "itunes:category", attrs={"text": categories}
                    )
                elif isinstance(categories, Iterable):
                    if len(categories) <= 0:
                        return
                    category = categories.pop(0)
                    if is_top and len(categories) > 0:
                        handler.startElement(
                            "itunes:category", attrs={"text": category}
                        )
                        _ = category_element(categories, is_top=False)
                        handler.endElement("itunes:category")
                    else:
                        handler.addQuickElement(
                            "itunes:category", attrs={"text": category}
                        )
                        _ = category_element(categories, is_top=False)

            categories = self.settings["PODCAST_FEED_CATEGORY"]
            category_element(categories)

    def add_item_elements(self, handler, item):
        """Adds a new element to the iTunes feed, using information from
        ``item`` to populate it with relevant information about the article.

        :param handler: A SimplerXMLGenerator instance
        :param item: The dict generated by iTunesWriter._add_item_to_the_feed

        """
        for key in DEFAULT_ITEM_ELEMENTS:
            # empty attributes will be ignored.
            if item[key] is None:
                continue
            if key == "description":
                content = item[key]
                handler.startElement("description", {})
                if not isinstance(content, six.text_type):
                    content = six.text_type(content, handler._encoding)
                content = content.replace("<html><body>", "")
                handler._write(content)
                handler.endElement("description")
            elif isinstance(item[key], six.text_type):
                handler.addQuickElement(key, item[key])
            elif type(item[key]) is dict:
                handler.addQuickElement(key, attrs=item[key])


class iTunesWriter(Writer):
    """Writer class for our iTunes feed.  This class is responsible for
    invoking the PodcastFeed and writing the feed itself (using it's superclass
    methods)."""

    def _create_new_feed(self, *args):
        """Helper function (called by the super class) which will initialize
        the PodcastFeed object."""
        self.context = args[-1]

        description = self.settings.get("PODCAST_FEED_SUMMARY", "")
        title = self.settings.get("PODCAST_FEED_TITLE", "") or self.context["SITENAME"]

        feed = PodcastFeed(
            title=title,
            link=("{0}/".format(self.site_url)),
            feed_url=None,
            description=description,
            settings=self.settings,
        )

        return feed

    def _add_item_to_the_feed(self, feed, item):
        """Performs an 'in-place' update of existing 'published' articles
        in ``feed`` by creating a new entry using the contents from the
        ``item`` being passed.
        This method is invoked by pelican's core.

        :param feed: A PodcastFeed instance.
        :param item: An article (pelican's Article object).

        """
        # Local copy of iTunes attributes to add to the feed.
        article = DEFAULT_ITEM_ELEMENTS.copy()

        article_values_map = [
            [
                "link",
                lambda calee, item, article: "{0}/{1}".format(calee.site_url, item.url),
            ],
            [
                "title",
                lambda calee, item, article: Markup(item.title).striptags(),
            ],  # NOQA E231
            [
                "itunes:summary",
                lambda calee, item, article: item.description
                if hasattr(item, "description")
                else Markup(item.summary).striptags(),
            ],
            [
                "description",
                lambda calee, item, article: "<![CDATA[{}]]>".format(
                    Markup(item.summary)
                ),
            ],
            [
                "pubDate",
                lambda calee, item, article: rfc2822_date(
                    set_date_tzinfo(
                        item.modified if hasattr(item, "modified") else item.date,
                        self.settings.get("TIMEZONE", None),
                    )
                ),
            ],
            ["itunes:author", lambda calee, item, article: item.author.name],
            [
                "itunes:subtitle",
                lambda calee, item, article: Markup(item.subtitle).striptags()
                if hasattr(item, "subtitle")
                else None,
            ],
            [
                "itunes:image",
                lambda calee, item, article: {
                    "href": "{0}{1}".format(self.site_url, item.image)
                }
                if hasattr(item, "image")
                else None,
            ],
            [
                "guid",
                lambda calee, item, article: item.guid
                if hasattr(item, "guid")
                else article["link"],
            ],
        ]

        def update_article(item, article, *args):
            if len(args) == 2:
                args = args + (None,)
            _key, value, default = args
            try:
                val = value(self, item, article)
                if val:
                    article[_key] = val
            except Exception as e:
                logger.warning("Exception %s", e)

        for article_value_map in article_values_map:
            update_article(item, article, *article_value_map)

        # get file path to podcast attachment file.
        def get_attachment_filepath(settings):
            siteurl = self.settings.get("SITEURL", None)
            content_path = self.settings.get("PATH", None)
            if item.podcast.startswith(siteurl):
                return f"{content_path}/{item.podcast[len(siteurl):]}"

        def get_attachment_url(settings):
            return item.podcast

        enclosure = {"url": get_attachment_url(self.settings)}

        if hasattr(item, "length"):
            enclosure["length"] = item.length
        if hasattr(item, "duration"):
            article["itunes:duration"] = item.duration

        filepath = get_attachment_filepath(self.settings)

        if filepath and os.path.exists(filepath):
            enclosure["length"] = str(os.path.getsize(filepath))
            audiofile = mutagen.File(filepath)

            (enclosure["type"],) = set(audiofile.mime) & set(SUPPORTED_MIME_TYPES)

            article["itunes:duration"] = str(int(audiofile.info.length))

        article["enclosure"] = enclosure

        # Add the new article to the feed.
        feed.add_item(**article)


class PodcastFeedGenerator(Generator):
    """Generates an iTunes content by inspecting all articles and invokes the
    iTunesWriter object, which will write the itunes Feed."""

    def __init__(self, *args, **kwargs):
        """Starts a brand new feed generator."""
        super(PodcastFeedGenerator, self).__init__(*args, **kwargs)
        # Initialize the number of episodes and where to save the feed.
        self.episodes = []
        self.podcast_episodes = {}
        self.feed_path = self.settings.get("PODCAST_FEED_PATH", None)

    def generate_context(self):
        """Looks for all 'published' articles and add them to the episodes
        list."""
        if self.feed_path:
            for article in self.context["articles"]:
                # Only 'published' articles with the 'podcast' metatag.
                if article.status == "published" and hasattr(article, "podcast"):
                    self.episodes.append(article)

    def generate_output(self, writer):
        """Write out the iTunes feed to a file.

        :param writer: A ``Pelican Writer`` instance.
        """
        writer = iTunesWriter(self.output_path, self.settings)
        writer.write_feed(self.episodes, self.context, self.feed_path)


def get_generators(generators):
    """Module function invoked by the signal 'get_generators'."""
    return PodcastFeedGenerator


def register():
    """Registers the module function `get_generators`."""
    signals.get_generators.connect(get_generators)
