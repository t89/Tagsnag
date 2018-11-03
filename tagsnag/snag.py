##
#  snag.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 01.11.2018.
#  Copyright (c) 2018 www.geeky.gent. All rights reserved.
#


class Snag():
    """ Data class to organize Snags """

    def __init__(self, url, repoName, localRepoPath, containingFolder, tag, filename, extension, destination):
        self.url = url
        self.repoName = repoName
        self.localRepoPath = localRepoPath
        self.containingFolder = containingFolder
        self.tag = tag
        self.filename = filename
        self.extension = extension
        self.destination = destination

    def __repr__(self):
        return "".join([self.repoName, self.tag])

