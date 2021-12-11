from posixpath import join
from .walk_utils import walk


def pathjoin(*paths: str):
    return join(*paths)


def pathwalk(path: str):
    return walk(path)
