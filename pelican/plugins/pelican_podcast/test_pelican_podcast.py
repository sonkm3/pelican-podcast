# -*- coding: utf-8 -*-
import datetime
import os
from shutil import rmtree
from tempfile import mkdtemp
import unittest
from unittest import mock
from unittest.mock import MagicMock

from pelican_podcast import PodcastFeedGenerator, iTunesWriter

from pelican.contents import Category
from pelican.tests.support import get_article, get_context, get_settings

CUR_DIR = os.path.dirname(__file__)
CONTENT_DIR = os.path.join(CUR_DIR, "content")

SITEURL = "http://example.com/"
PATH = 'testdata'

PODCAST_FEED_PATH = "feeds/podcasts.atom.xml"
PODCAST_FEED_TITLE = "SITENAME"
PODCAST_FEED_EXPLICIT = "No"
PODCAST_FEED_LANGUAGE = "ja"
PODCAST_FEED_COPYRIGHT = "COPYRIGHT STRING"
PODCAST_FEED_SUBTITLE = "SUBTITLE STRING"
PODCAST_FEED_AUTHOR = "AUTHOR STRING"
PODCAST_FEED_SUMMARY = "SUMMERY STRING"
PODCAST_FEED_IMAGE = SITEURL + "/images/common/artwork.jpg"
PODCAST_FEED_OWNER_NAME = "OWNER STRING"
PODCAST_FEED_OWNER_EMAIL = "example@example.com"
PODCAST_FEED_CATEGORY = ["Leisure", "Hobbies"]


class TestPodcast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.temp_cache = mkdtemp(prefix="pelican_cache.")
        self.settings = get_settings()
        self.settings["CACHE_CONTENT"] = False

    def tearDown(self):
        rmtree(self.temp_cache)

    @mock.patch.object(iTunesWriter, "write_feed")
    @mock.patch.object(iTunesWriter, "__init__")
    def test_generate_output(self, itunes_writer_init, write_feed):
        itunes_writer_init.return_value = None
        write_feed.return_value = None

        settings = self.settings.copy()
        settings["PODCAST_FEED_PATH"] = PODCAST_FEED_PATH

        generator = PodcastFeedGenerator(
            context=settings,
            settings=settings,
            path=None,
            theme=settings["THEME"],
            output_path=None,
        )
        writer = MagicMock()
        generator.generate_output(writer)
        self.assertFalse(writer.write_feed.called)
        self.assertTrue(itunes_writer_init.called)

    def test_generate_context(self):
        settings = self.settings.copy()
        settings["PODCAST_FEED_PATH"] = PODCAST_FEED_PATH

        article = get_article("title", "cocntent")
        podcast_article = get_article(
            "podcast title", "podcast cocntent", podcast="aaa.mp3"
        )

        context = get_context(settings)
        context["articles"] = [article, podcast_article]

        generator = PodcastFeedGenerator(
            settings=settings,
            context=context,
            path=None,
            theme=settings["THEME"],
            output_path=None,
        )

        generator.generate_context()
        self.assertEqual(1, len(generator.episodes))


class TestiTunesWriter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.temp_cache = mkdtemp(prefix="pelican_cache.")

        settings = {}
        settings["CACHE_CONTENT"] = False
        settings["PODCAST_FEED_PATH"] = PODCAST_FEED_PATH
        settings["SITEURL"] = SITEURL
        settings["PATH"] = PATH
        settings["FEED_DOMAIN"] = SITEURL

        self.settings = get_settings(**settings)

        self.temp_content = mkdtemp(prefix="pelicantests.")
        self.temp_output = mkdtemp(prefix="pelicantests.")

    def tearDown(self):
        rmtree(self.temp_cache)

    def test_generate_output(self):
        category = Category("misc", self.settings)
        podcast_article = get_article(
            "podcast title",
            "podcast cocntent",
            podcast="http://example.com/audio/test.mp3",
            category=category,
            date=datetime.datetime.now(),
            length='120',
            duration='120',
        )

        context = get_context(**self.settings)
        context["articles"] = [
            podcast_article,
        ]

        generator = PodcastFeedGenerator(
            context=context,
            settings=self.settings,
            path=self.temp_content,
            theme="",
            output_path=self.temp_output,
        )
        generator.generate_context()

        writer = iTunesWriter(self.temp_output, settings=self.settings)
        generator.generate_output(writer)

        output_path = os.path.join(self.temp_output, self.settings["PODCAST_FEED_PATH"])

        self.assertTrue(os.path.exists(output_path))

        with open(output_path) as output_file:
            output_containts = output_file.read()
            self.assertIn('<?xml version="1.0" encoding="utf-8"?>', output_containts)
            # self.assertIn(
            #     '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">',
            #     output_containts,
            # )
            self.assertIn("<title>A Pelican Blog</title>", output_containts)
            self.assertIn("<title>podcast title</title>", output_containts)
            # self.assertIn(
            #     '<enclosure type="audio/mpeg" url="aaa.mp3"></enclosure>',
            #     output_containts,
            # )
            self.assertIn(
                "<link>http://example.com//podcast-title.html</link>", output_containts
            )
            self.assertIn(
                "<guid>http://example.com//podcast-title.html</guid>", output_containts
            )
