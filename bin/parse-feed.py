import argparse
import os
import sys


def get_parser():
    parser = argparse.ArgumentParser(
        prog = os.path.basename(__file__),
        description = 'Update all podcast feeds and download new content',
        epilog = 'Note: If skip-images is set, overwrite-images will be ignored.',
    )
    parser.add_argument(
        action='store',
        help='The base directory containing one directory per feed, where output will be saved.',
        dest='output_directory',
    )
    parser.add_argument(
        '-i',
        '--overwrite-images',
        action='store_true',
        help='Should images be redownload, if they already exist?',
    )
    parser.add_argument(
        '-I',
        '--skip-images',
        action='store_true',
        help='Should images downloads be skipped?',
    )
    parser.add_argument(
        '-m',
        '--overwrite-media',
        action='store_true',
        help='Should media (audio/video) be redownload, if they already exist?',
    )
    parser.add_argument(
        '-M',
        '--skip-media',
        action='store_true',
        help='Should media downloads be skipped?',
    )
    parser.add_argument(
        '-c',
        '--content-directory',
        action='store',
        help='Where should text/content be stored, relative to output directory?',
        default='content',
    )
    parser.add_argument(
        '-s',
        '--static-directory',
        action='store',
        help='Where should images/audio/video be stored, relative to output directory?',
    )
    return parser


def _clean(args):
    for key, value in (
        ('skip_images', 'overwrite_images'),
        ('skip_media', 'overwrite_media'),
    ):
        if getattr(args, key):
            setattr(args, value, None)
    args = dict(args.__dict__)
    if not args['static_directory']:
        args['static_directory'] = args['content_directory']
    return args


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    args = _clean(args)
    try:
        from rss2hugo.models import FeedsDirectory
    except ImportError:
        print('Unable to locate the rss2hugo package; try reinstalling...')
        sys.exit(1)
    try:
        feeds_directory = FeedsDirectory(args)
        feeds_directory.update()
    except KeyboardInterrupt:
        pass
