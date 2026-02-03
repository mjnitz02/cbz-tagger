import argparse


def get_arg_parser():
    """Argparse for the container"""
    parser = argparse.ArgumentParser(description="Manga Tagger")
    parser.add_argument("--entrymode", help="Container Entrymode Start", action="store_true")
    parser.add_argument("--manual", help="Manual Mode", action="store_true")
    parser.add_argument("--refresh", help="Refresh Mode", action="store_true")
    parser.add_argument("--add", help="Add Tracked Mode", action="store_true")
    parser.add_argument("--remove", help="Remove Tracked Mode", action="store_true")
    parser.add_argument("--delete", help="Delete Mode", action="store_true")
    kwargs = vars(parser.parse_args())
    return kwargs
