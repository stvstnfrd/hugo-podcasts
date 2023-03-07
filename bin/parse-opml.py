import argparse
import os
import sys



def get_parser():
    parser = argparse.ArgumentParser(
        prog = os.path.basename(__file__),
        description = 'Parse an OPML file of podcast feeds and create a file/directory stub for each feed',
    )
    parser.add_argument(
        action='store',
        help='The location of the OPML file to be imported',
        dest='filename',
    )
    parser.add_argument(
        action='store',
        help='The base directory containing one directory per feed, where output will be saved.',
        dest='output_directory',
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
    args = dict(args.__dict__)
    if not args['static_directory']:
        args['static_directory'] = args['content_directory']
    return args


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    args = _clean(args)
    filename = args['filename']
    try:
        from rss2hugo.models import FeedsDirectory
    except ImportError:
        print('Unable to locate the rss2hugo package; try reinstalling...')
        sys.exit(1)
    try:
        feeds_directory = FeedsDirectory(args)
        feeds_directory.import_opml(filename)
    except KeyboardInterrupt:
        pass
