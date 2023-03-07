"""
Represent base data classes
"""
from glob import glob
import os
from xml.etree import ElementTree as ET

import frontmatter
import requests

from rss2hugo.log import get_logger
from rss2hugo.markdown import HugoFeedDocument
from rss2hugo.pandoc import normalize_markup
from rss2hugo.util import get_filename
from rss2hugo.util import get_image
from rss2hugo.util import mkdir
from rss2hugo.util import parse_datetime


logger = get_logger(__name__)
NS = {
    'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
}


class Parser:
    """
    Create a base Parser interface,
    to be implemented by subclasses
    """
    # pylint: disable=too-few-public-methods

    @classmethod
    def _parse_element(cls, element, key, alias=None):
        logger.debug("Parse element: %s", key)
        if alias is None:
            alias = key
        method = '_clean_' + alias.replace(':', '_')
        method = getattr(cls, method, None)
        value = element.find(key, NS)
        if method is not None:
            value = method(value)
        elif value is not None:
            value = value.text
        return value


    @classmethod
    def _clean_owner(cls, value):
        email = None
        name = None
        if value is not None:
            email = email.find('itunes:email', NS)
            name = name.find('itunes:name', NS)
            if email is not None:
                email = email.text
            if name is not None:
                name = name.text
        value = {
            'email': email or '',
            'name': name or '',
        }
        return value

    @classmethod
    def _clean_title(cls, value):
        if value is not None:
            value = value.text
        if value is not None:
            value = value.replace('', '')
            value = value.replace('', '')
            value = value.replace('', '')
            value = value.replace('', '')
            # item_title = ''.join([i if ord(i) < 128 else '' for i in item_title])
        return value

    @classmethod
    def _clean_subtitle(cls, value):
        return cls._clean_title(value)

    @classmethod
    def _clean_pub_date(cls, value):
        if value is not None:
            value = value.text
        value = parse_datetime(value)
        return value

    @classmethod
    def _clean_explicit(cls, value):
        if value is not None:
            value = value.text
        if value is None:
            value = False
        value = str(value).lower()
        if value in [
            'yes',
            'true',
        ]:
            value = True
        elif value in [
            'no',
            'false',
        ]:
            value = False
        else:
            value = None
        return value

    @classmethod
    def _clean_duration(cls, value):
        if value is not None:
            value = value.text
        if value is None:
            value = 0
        value = str(value)
        return value

    @classmethod
    def _clean_description(cls, value):
        if value is not None:
            value = value.text
        value = normalize_markup(value)
        return value

    @classmethod
    def _clean_season(cls, value):
        if value is not None:
            value = value.text
        try:
            value = int(value)
        except TypeError: # ValueError:
            value = 0
        return value

    @classmethod
    def _clean_episode_type(cls, value):
        if value is not None:
            value = value.text
        value = value or ''
        return value

    @classmethod
    def _clean_enclosure(cls, value):
        if hasattr(value, 'attrib'):
            value = dict(value.attrib)
        else:
            value = {}
        return value

    @classmethod
    def _clean_itunes_image(cls, value):
        if value is not None:
            value = value.attrib.get('href')
        value = value or ''
        return value

    @classmethod
    def _clean_image(cls, value):
        if value is not None:
            value = value.find('url')
            if value is not None:
                value = value.text
        value = value or ''
        return value

    # pylint: disable=too-few-public-methods


class Episode(Parser):
    """
    Model a podcast episode
    """

    def __init__(self, data, feed_directory):
        logger.debug("Initialize episode: %s", data['title'])
        self.data = data
        self.feed_directory = feed_directory

    @property
    def static_directory(self):
        """
        This is where the episode's static content is stored
        """
        item = self.data
        item_title_safe = get_filename(item['title'])
        directory = os.path.join(
            self.feed_directory.static_directory,
            "{item['pub_date'].year:04d}",
            "{item['pub_date'].month:02d}",
            "{item['pub_date'].day:02d}",
            item_title_safe,
        )
        return directory

    @property
    def content_directory(self):
        """
        This is where the episode's text content is stored
        """
        item = self.data
        item_title_safe = get_filename(item['title'])
        directory = os.path.join(
            self.feed_directory.content_directory,
            f"{item['pub_date'].year:04d}",
            f"{item['pub_date'].month:02d}",
            f"{item['pub_date'].day:02d}",
            item_title_safe,
        )
        return directory

    @property
    def filename(self):
        """
        This is where the episode's Markdown file is stored
        """
        filename = os.path.join(
            self.content_directory,
            'index.markdown',
        )
        return filename

    @property
    def enclosure(self):
        """
        This is the attached media, if any
        """
        enclosure = self.data.get('enclosure') or {}
        _file = enclosure.get('url') or ''
        _file = os.path.basename(_file)
        _file = _file.split('?')[0]
        extension = os.path.splitext(_file)
        if len(extension) == 2:
            extension = extension[-1]
            if extension not in [
                '.wav',
                '.mp3',
                '.mp4',
                '.m4a',
                '.mpa',
                '.mpg',
                '.mpeg',
            ]:
                extension = '.mp3'
        else:
            extension = '.mp3'
        filename = os.path.join(
            self.static_directory,
            'HEARME' + extension,
        )
        return filename

    @property
    def image(self):
        """
        This is the remote image, if any
        """
        image = self.data.get('image') or ''
        image = image.split('?')[0]
        extension = os.path.splitext(image)
        if len(extension) == 2:
            extension = extension[-1]
            if extension not in [
                '.jpg',
                '.jpeg',
                '.gif',
                '.bmp',
                '.png',
            ]:
                extension = '.jpg'
        else:
            extension = '.jpg'
        filename = os.path.join(
            self.static_directory,
            'folder' + extension,
        )
        return filename

    def __str__(self):
        """
        Serialize the object as a Hugo-compliant Markdown document
        """
        front_matter = {
            key: value
            for key, value in self.data.items()
            if key in [
                'title',
                'subtitle',
                'pub_date',
                'duration',
                'explicit',
                'season',
                'episode_type',
                'enclosure',
                'description',
                # 'image',
            ]
        }
        contents = HugoFeedDocument(front_matter)
        contents = str(contents)
        return contents

    def save(self):
        """
        Save the episode to disk
        """
        logger.info("Save episode: %s", self.filename)
        mkdir(self.content_directory, recursive=True)
        with open(self.filename, 'w', encoding='utf-8') as _file:
            _file.write(str(self))
        url = self.data.get('image') or ''
        url = url.split('?')[0]
        if url != '':
            filename = self.image
            if not self.feed_directory.feeds_directory.args.get('skip_images'):
                if (
                    self.feed_directory.feeds_directory.args.get('overwrite_images')
                    or
                    not os.path.exists(filename)
                ):
                    mkdir(self.static_directory, recursive=True)

                    get_image(url, filename)
            self.data['folder'] = os.path.dirname(filename)
        url = self.data.get('enclosure') or {}
        url = url.get('url') or ''
        if url != '':
            filename = self.enclosure
            if not self.feed_directory.feeds_directory.args.get('skip_media'):
                if (
                    self.feed_directory.feeds_directory.args.get('overwrite_media')
                    or
                    not os.path.exists(filename)
                ):
                    mkdir(self.static_directory, recursive=True)

                    get_image(url, filename)
            self.data['enclosure-local'] = os.path.dirname(filename)

    # pylint: disable=too-many-locals
    @classmethod
    def from_item(cls, item, feed_directory):
        """
        Create a new object from an XML node
        """
        item_title = cls._parse_element(item, 'title')
        logger.debug("Parse episode: %s", item_title)
        image = cls._parse_element(item, 'image')
        image = image or cls._parse_element(item, 'itunes:image')
        image = image or ''
        image = image.split('?')[0]
        enclosure = cls._parse_element(item, 'enclosure')
        pub_date = cls._parse_element(item, 'pubDate', 'pub_date')
        explicit = cls._parse_element(item, 'itunes:explicit', 'explicit')
        subtitle = cls._parse_element(item, 'itunes:subtitle', 'subtitle')
        duration = cls._parse_element(item, 'itunes:duration', 'duration')
        description = cls._parse_element(item, 'description')
        season = cls._parse_element(item, 'itunes:season', 'season')
        summary = cls._parse_element(item, 'itunes:summary', 'description')
        if season == 0:
            season = pub_date.year
        episode_type = cls._parse_element(item, 'itunes:episodeType', 'episode_type')
        link = cls._parse_element(item, 'link')
        episode_data = {
            'title': item_title.replace('"', '\\"'),
            'pub_date': pub_date,
            'description': description,
            'subtitle': subtitle,
            'duration': duration,
            'explicit': explicit,
            'season': season,
            'episode_type': episode_type,
            'enclosure': enclosure,
            'summary': summary,
            'image': image,
            'link': link,
            # guid
            # content:encoded
            # itunes:keywords
        }
        episode = cls(episode_data, feed_directory)
        return episode
    # pylint: enable=too-many-locals


class FeedDirectory(Parser):
    """
    Model a directory of an RSS feed
    """

    def __init__(self, title, url, index_file, feeds_directory):
        logger.debug("Initialize feed: %s", title)
        self.title = title
        self.url = url
        self.index_file = index_file
        self.feeds_directory = feeds_directory
        self.episodes = []
        directory = os.path.dirname(index_file)
        directory = os.path.split(directory)
        directory = directory[-1]
        self.static_directory = os.path.sep.join([
            feeds_directory.static_directory,
            directory,
        ])
        self.content_directory = os.path.sep.join([
            feeds_directory.content_directory,
            directory,
        ])

    def update(self):
        """
        Update a feed directory
        """
        root = self._fetch()
        if root is not None:
            self._parse(root)

    def _fetch(self):
        logger.debug("Fetch feed: %s", self.title)
        try:
            response = requests.get(self.url, timeout=10)
        except requests.exceptions.ConnectionError:
            logger.error("Unable to update: '%s': '%s'", self.title, self.url)
            return None
        text = response.text
        try:
            tree = ET.fromstring(text)
        except ET.ParseError:
            # TODO: error
            return None
        if hasattr(tree, 'getroot'):
            root = tree.getroot()
        else:
            root = tree
        return root

    def _parse(self, root):
        # pylint: disable=too-many-locals
        logger.debug("Parse feed: %s", self.content_directory)
        channels = root.findall('channel')
        for channel in channels:
            title = self._parse_element(channel, 'title')
            pub_date = self._parse_element(channel, 'pubDate', 'pub_date') or ''
            description = self._parse_element(channel, 'description')
            image = self._parse_element(channel, 'image')
            image = image or self._parse_element(channel, 'itunes:image')
            link = self._parse_element(channel, 'link')
            language = self._parse_element(channel, 'language')
            explicit = self._parse_element(channel, 'itunes:explicit', 'explicit')
            author = self._parse_element(channel, 'itunes:owner', 'owner')
            all_categories = channel.findall('itunes:category', NS)
            _tags = []
            for categories in all_categories:
                parent = categories.attrib['text']
                _tags.append(parent)
                for category in categories.findall('itunes:category', NS):
                    tag = '/'.join([
                        parent,
                        category.attrib['text'],
                    ])
                    _tags.append(tag)
            front_matter = {
                'title': title,
                'date': pub_date,
                'link': link,
                'language': language,
                'explicit': explicit,
                'description': description,
                'image': image,
                'image_remote': image,
                'feed_url': self.url,
                'author': author,
                'tags': _tags,
            }
            self._write(front_matter)
            items = channel.findall('item')
            for item in items:
                episode = Episode.from_item(item, self)
                episode.save()
                break  # TODO: one episode only
        # pylint: enable=too-many-locals

    def _write(self, front_matter):
        logger.debug("Write feed: %s", self.content_directory)
        image = front_matter.get('image')
        image = image.split('?')[0]
        extension = os.path.splitext(image)
        if len(extension) == 2:
            extension = extension[-1]
        elif extension not in [
            '.jpg',
            '.jpeg',
            '.gif',
            '.bmp',
            '.png',
        ]:
            extension = '.jpg'
        filename = os.path.sep.join([
            self.static_directory,
            'folder' + extension,
        ])
        image = image or ''
        if image != '':
            if not self.feeds_directory.args.get('skip_images'):
                if (
                    self.feeds_directory.args.get('overwrite_images')
                    or
                    not os.path.exists(filename)
                ):
                    mkdir(self.static_directory, recursive=True)
                    get_image(image, filename)
            front_matter['image'] = 'folder' + extension
        filename = os.path.sep.join([
            self.content_directory,
            '_index.markdown',
        ])
        front_matter['feed_url'] = self.url
        contents = HugoFeedDocument(front_matter)
        contents = str(contents)
        with open(filename, 'w', encoding='utf-8') as _file:
            _file.write(contents)

    @classmethod
    def from_index(cls, filename, feeds_directory):
        """
        Instantiate an object from an XML node
        """
        title = None
        data = frontmatter.load(filename)
        podcast = data.get('podcast') or {}
        url = podcast.get('feed_url') or ''
        title = podcast.get('title') or ''
        feed_directory = cls(title, url, filename, feeds_directory)
        return feed_directory


class FeedsDirectory:
    """
    Model a directory of RSS feeds
    """

    def __init__(self, args):
        self.output_directory = args.get('output_directory')
        logger.debug("Initialize feeds: %s", self.output_directory)
        self.args = args
        self._feeds = None
        self.content_directory = os.path.sep.join([
            args['output_directory'],
            args['content_directory'],
        ])
        self.static_directory = os.path.sep.join([
            args['output_directory'],
            args['static_directory'],
        ])

    def update(self):
        """
        Update a directory of RSS feeds
        """
        logger.info("Update feeds: %s", self.output_directory)
        feeds = self._load()
        for feed in feeds:
            feed.update()
            # break  # TODO: one podcast only

    def _load(self):
        logger.debug("Load feeds: %s", self.output_directory)
        pattern = os.path.sep.join([
            self.content_directory,
            '*',
            '_index.markdown',
        ])
        feed_files = glob(pattern)
        feeds = [
            FeedDirectory.from_index(feed_file, self)
            for feed_file in feed_files
        ]
        return feeds

    @staticmethod
    def _import_opml(filename):
        logger.debug('Import OPML: %s', filename)
        tree = ET.parse(filename)
        root = tree.getroot()
        # TODO: confirm tag == 'opml', version == '1.0'
        return root

    @staticmethod
    def _parse_outline(outline):
        logger.debug("Parse outline: %s", outline)
        _type = outline.attrib.get('type', '')
        if not _type or _type != 'rss':
            return None
        title = outline.attrib.get('text', '')
        feed_url = outline.attrib.get('xmlUrl', '')
        page_url = outline.attrib.get('htmlUrl', '')
        data = {
            'title': title,
            'feed_url': feed_url,
            'page_url': page_url,
        }
        return data

    def _contains(self, feed):
        feeds = self._load()
        for _feed in feeds:
            if feed['title'] == _feed.title:
                return True
            if feed['feed_url'] == _feed.url:
                return True
        return False

    def import_opml(self, filename):
        """
        Import an OPML file into a directory of podcasts
        """
        logger.info("Parse OPML: %s", filename)
        opml = FeedsDirectory._import_opml(filename)
        body = opml.find('body')
        feeds = body.findall('outline')
        mkdir(self.content_directory, recursive=True)
        for outline in feeds:
            outline = FeedsDirectory._parse_outline(outline)
            if self._contains(outline):
                logger.warning("Feed already exists: %s", outline['title'])
                continue
            self._create_feed_directory(outline)

    def _create_feed_directory(self, outline):
        logger.debug("Create feed: %s", outline['title'])
        title = outline['title']
        directory = get_filename(title)
        directory = os.path.sep.join([
            self.content_directory,
            directory,
        ])
        mkdir(directory)
        filename = os.path.sep.join([
            directory,
            '_index.markdown',
        ])
        self._create_feed_directory_index_outline(filename, outline)

    def _create_feed_directory_index_outline(self, filename, outline):
        logger.debug("Write to file: %s", filename)
        contents = HugoFeedDocument(outline, is_draft=True)
        contents = str(contents)
        with open(filename, 'w', encoding='utf-8') as _file:
            _file.write(contents)
