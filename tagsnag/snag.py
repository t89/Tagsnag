##
#  snag.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 01.11.2018.
#  Copyright (c) 2018 www.geeky.gent. All rights reserved.
#


class Snag():
    """ Data Class to organize Snags """

    def __init__(self, url, tag, filename, filetype, destination):
        self.url = url
        self.tag = tag
        self.filename = filename
        self.filetype = filetype
        self.destination = destination

    def __repr__(self):
        return "".join([self.url, self.tag, self.filename, self.filetype, self.destination])

