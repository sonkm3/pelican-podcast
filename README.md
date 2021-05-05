pelican-podcast: Podcast Plugin for Pelican
====================================================

[![Build Status](https://img.shields.io/github/workflow/status/sonkm3/pelican-podcast/build)](https://github.com/sonkm3/pelican-podcast/actions)
[![PyPI Version](https://img.shields.io/pypi/v/pelican-podcast)](https://pypi.org/project/pelican-podcast/)
![License](https://img.shields.io/pypi/l/pelican-podcast?color=blue)

pelican-podcast
---------------
- Plugin for Pelican, Podcast publishing will be supported with this plugin.
- Fork of [pelican-podcast-feed](https://github.com/magnunleno/pelican-podcast-feed)

What I changed / new features
---------------------------------

1. add a feature to omit `Length` and `Dulation` field.
1. refactoring.
1. add test.
1. apply pelican plugin template.
1. remove multiple podcast setup.

Installation
------------

This plugin can be installed via:

    python -m pip install pelican-podcast

Usage
-----

### Setup

add podcast settings to `pelican.conf` file.
#### example
```python
# podcast settings
PODCAST_FEED_PATH = 'feeds/podcasts.atom.xml'
PODCAST_FEED_TITLE = SITENAME
PODCAST_FEED_EXPLICIT = 'No'
PODCAST_FEED_LANGUAGE = 'en'
PODCAST_FEED_COPYRIGHT = AUTHOR
PODCAST_FEED_SUBTITLE = ''
PODCAST_FEED_AUTHOR = AUTHOR
PODCAST_FEED_SUMMARY = 'This podcast is published with pelican.'
PODCAST_FEED_IMAGE = SITEURL + '/images/artwork.jpg'
PODCAST_FEED_OWNER_NAME = AUTHOR
PODCAST_FEED_OWNER_EMAIL = 'example@example.com'
PODCAST_FEED_CATEGORY = ['Leisure','Hobbies']
```

### Writing podcast article

Add `Podcast`, `Length` and `duration` field to article header.
- `Podcast` field represents filepath or url to audio/video attachment file.
- `Length` field represnts attachment file length(file size). (You can omit if attachment can accessed as local file)
- `dulation` field represents attachment duration(playback time). (You can omit if attachment can accessed as local file)

#### example
```markdown
Title: My first podcast episode
Date: 2021-01-01 00:00
Tags: podcast-episode, 2021
Category: podcast
Slug: episode/episode1-my-first-podcast
Podcast: https://example.com/casts/20210101-podcast.mp3
Description: My first podcast episode.

My first podcast episode text part.
```

Contributing
------------

Contributions are welcome and much appreciated. Every little bit helps. You can contribute by improving the documentation, adding missing features, and fixing bugs. You can also help out by reviewing and commenting on [existing issues][].

To start contributing to this plugin, review the [Contributing to Pelican][] documentation, beginning with the **Contributing Code** section.

[existing issues]: https://github.com/sonkm3/pelican-podcast/issues
[Contributing to Pelican]: https://docs.getpelican.com/en/latest/contribute.html

License
-------

This project is licensed under the AGPL-3.0 license.
