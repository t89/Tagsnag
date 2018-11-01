##
#  tagsnag.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 01.11.2018.
#  Copyright (c) 2018 www.geeky.gent. All rights reserved.
#

from .snag import Snag

import os
import logging

from xml.etree import ElementTree as ET


class Tagsnag():
    """Tagsnag main class"""

    def __init__(self):
        super(Tagsnag, self).__init__()
        self.snags = []
        self.repoNames = []
        self.initialSetup()


    def initialSetup(self):
        self.setupLogger()



    def setupLogger(self):
        """ Creating / configuring logger instance """

        logging.basicConfig(level=logging.WARNING, format='%(msg)s')
        self.log = logging.getLogger('logger')

        # Create filehandler
        fh = logging.FileHandler('Tagsnag.log')
        fh.setLevel(logging.DEBUG)
        self.log.addHandler(fh)

        # Setting logger to debug setting for now, this value will change once we have parsed to arguments
        logging.getLogger().setLevel(logging.DEBUG)

        self.log.debug('Created Logger.')

        ##
        # Setting up argument parser
        self.log.debug('Setting up argument parser...')


    def setXMLPath(self, path):
        """ XML Path Setter """

        self.log.debug('Provided Path: {}'.format(path))
        self.setXMLPath = path
        self.generateSnagFromXMLPath(path)


    def generateSnagFromXMLPath(self, path):
        """ Ingests XML from provided path """

        self.log.debug('Attempting to parse xml file: {}'.format(path))

        doc = ET.parse(path).getroot()

        for repo in doc.findall('repository'):
            url = repo.find('./url').text
            self.log.debug('Repository: {}'.format(url))

            for snag in repo.findall('snag'):
                tag = snag.find('tag').text
                filename = snag.find('filename').text
                filetype = snag.find('filetype').text
                destination = snag.find('destination').text

                s = Snag(url=url, tag=tag, filename=filename, filetype=filetype, destination=destination)
                self.snags.append(s)
                self.repoNames.append(s.name)
                self.log.debug('Tag: {}Filename: {}Filetype: {}Destination: {}'.format(tag, filename, filetype, destination))

            self.log.debug('Extracted Snags: {}'.format(self.snags))
            self.log.info('Extracted Repositories: {}'.format(self.repoNames))


    def setVerbose(self, flag):
        """ Verbose Flag Setter """

        if flag:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

