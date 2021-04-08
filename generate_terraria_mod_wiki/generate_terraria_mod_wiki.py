import os
import sys

from mod_wiki import ModWiki


def main():
    if len(sys.argv) > 1:
        os.chdir("../")
        wiki = ModWiki(sys.argv[1])
        wiki.build_wiki()
    else:
        print("Please supply an input path")


if __name__ == '__main__':
    main()
