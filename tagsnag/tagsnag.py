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

from xml.dom.minidom import parse, parseString

class Tagsnag():
    """Tagsnag main class"""

    def __init__(self):
        super(Tagsnag, self).__init__()
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

        xml = parse(path)
        repos = xml.getElementsByTagName('repository')

        for repo in repos:
            url = repo.getElementsByTagName('url')[0].firstChild.data
            self.log.debug('Repository: {}'.format(url))

            snags = xml.getElementsByTagName('snag')

            for snag in snags:
                tag = snag.getElementsByTagName("tag")[0].firstChild.data
                filename = snag.getElementsByTagName("filename")[0].firstChild.data
                filetype = snag.getElementsByTagName("filetype")[0].firstChild.data
                destination = snag.getElementsByTagName("destination")[0].firstChild.data

                s = Snag(url=url, tag=tag, filename=filename, filetype=filetype, destination=destination)
                print("{}".format(s))
                self.log.debug('Tag: {}Filename: {}Filetype: {}Destination: {}'.format(tag, filename, filetype, destination))

    def setVerbose(self, flag):
        """ Verbose Flag Setter """

        if flag:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

