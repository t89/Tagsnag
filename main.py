##
#!/usr/bin/python
#
#  main.py
#  Tagsnatch
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 31.10.2018.
#  Copyright (c) 2018 www.geeky.gent. All rights reserved.
#


import sys
import logging
from argparse import ArgumentParser
from xml.dom.minidom import parse, parseString

def main(argv):
    try:
        ##
        # Setting up logger
        logging.basicConfig(level=logging.WARNING, format='%(msg)s')
        LOG = logging.getLogger('logger')

        # Create filehandler
        fh = logging.FileHandler('Tagsnag.log')
        fh.setLevel(logging.DEBUG)
        LOG.addHandler(fh)

        # Setting logger to debug setting for now, this value will change once we have parsed to arguments
        logging.getLogger().setLevel(logging.DEBUG)

        LOG.debug('Created Logger.')

        ##
        # Setting up argument parser
        LOG.debug('Setting up argument parser...')

        ap = ArgumentParser()
        ap.add_argument('-v', '--verbose', default=True, action='store_true', help='Increase verbosity')

        ap.add_argument('path', nargs='?')
        options = ap.parse_args()
        path = options.path
        #  path  = os.getenv("~/Development/Python/Tagsnag_Test")
        LOG.debug('Provided Path: {}'.format(path))

        if options.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

        ##
        # Ingest XML File from provided path

        LOG.debug('Attempting to parse xml file: {}'.format(path))

        xml = parse(path)
        repos = xml.getElementsByTagName('repository')

        for repo in repos:
            url = repo.getElementsByTagName('url')[0].firstChild.data
            LOG.debug('Repository: {}'.format(url))

            snags = xml.getElementsByTagName('snag')

            for snag in snags:
                tag = snag.getElementsByTagName("tag")[0].firstChild.data
                filename = snag.getElementsByTagName("filename")[0].firstChild.data
                filetype = snag.getElementsByTagName("filetype")[0].firstChild.data
                destination = snag.getElementsByTagName("destination")[0].firstChild.data

                LOG.debug('Tag: {}Filename: {}Filetype: {}Destination: {}'.format(tag, filename, filetype, destination))

    except KeyboardInterrupt:
        LOG.info('Keyboard Interrupt detected: Exiting.')
        pass


if __name__ == "__main__":
    main(sys.argv)

