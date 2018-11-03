##
#  tagsnag.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 01.11.2018.
#  Copyright (c) 2018 www.geeky.gent. All rights reserved.
#

from .snag import Snag

import os
from shutil import copyfile
import logging
import subprocess

from git import Git
from git import Repo

from xml.etree import ElementTree as ET


class Tagsnag():
    """Tagsnag main class"""

    def __init__(self):
        super(Tagsnag, self).__init__()
        self.initialSetup()

    def start(self):
        self.loadRepositories(self.setXMLPath)

        for snag in self.snags:


            self.checkout(self.repositories[snag.repoName], 'master')
            self.pull(self.repositories[snag.repoName])
            self.checkout(self.repositories[snag.repoName], snag.tag)
            #  self.searchFileName(path=snag.localRepoPath, containingFolder=snag.containingFolder, filenames=[snag.filename], extension=snag.extension)

            foundPaths = self.search_files(filename=snag.filename, path=snag.localRepoPath, extension=snag.extension)
            if len(foundPaths) > 0:
                self.copyFileToDestination(path = foundPaths[0], destination = snag.destination)



    def initialSetup(self):
        # Instance variable init
        self.snags = []
        self.repoNamesAndURLs = {}
        self.repositories = {}

        # Advanced setup
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
            url = repo.find('./url').text.strip().rstrip()

            # create repo name by converting to norm path, extracting basepath and cutting off before the .git extension
            repoName = os.path.basename(os.path.normpath(url)).split('.')[0]
            repoPath = os.path.normpath("{}/{}".format(os.path.dirname(path), repoName))
            self.repoNamesAndURLs[repoName]=url
            self.log.debug('Repository: {}'.format(url))

            for snag in repo.findall('snag'):
                tag = snag.find('tag').text.strip().rstrip()
                containingFolder = snag.find('folder').text.strip().rstrip()
                filename = snag.find('filename').text.strip().rstrip()
                extension = snag.find('extension').text.strip().rstrip()
                destination = snag.find('destination').text.strip().rstrip()
                destination = os.path.join(destination + containingFolder, repoName + '.' + extension)

                s = Snag(url=url, tag=tag, repoName=repoName, localRepoPath=repoPath, containingFolder=containingFolder, filename=filename, extension=extension, destination=destination)
                self.snags.append(s)
                self.log.debug('Tag: {}\nFilename: {}\nextension: {}\nDestination: {}\n'.format(tag, filename, extension, destination))

            self.log.debug('Extracted Snags: {}'.format(self.snags))
            self.log.info('Extracted Repositories: {}'.format(self.repoNamesAndURLs))


    def loadRepositories(self, path):
        """ Checks existence of repository paths and initiates clone """
        destinationPath = os.path.dirname(path)
        for repoName in self.repoNamesAndURLs:
            url = self.repoNamesAndURLs[repoName]
            repoPath = os.path.normpath("{}/{}".format(destinationPath, repoName))
            self.log.debug(repoPath)
            if os.path.exists(repoPath):
                self.log.info('Repository {} exists.'.format(repoName))

                repo = Repo(repoPath)
                assert not repo.bare
                self.repositories[repoName] = repo

            else:
                self.log.info('Repository {} does not exist. Attempting to clone it...'.format(repoName))
                # @todo: Implement
                #  self.cloneRepository(destination=repoPath, url=url)


    def checkout(self, repo, target):
        git = repo.git
        git.checkout(target)


    def pull(self, repo):
        git = repo.git
        git.pull('origin', 'master')


    def search_files(self, filename, path='.', extension=''):
        extension = extension.lower()
        foundPaths = []

        for dirpath, dirnames, files in os.walk(path):
            for file in files:
                if extension and file.lower().endswith(extension):
                    if filename.lower() in file.lower():
                        foundPath = os.path.join(dirpath, file)
                        self.log.info('Found {}'.format(foundPath))
                        foundPaths.append(foundPath)
                #  elif not extension:
                    #  print(os.path.join(dirpath, file))
        return foundPaths


    def copyFileToDestination(self, path, destination):
        self.log.debug('Copying from:\n{}\nto:\n{}'.format(path, destination))
        if os.path.exists(path):
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
            try:
                copyfile(path, destination)
            except IOError:
                self.log.info(IOError.message)
        else:
            self.log.info('File does not exist. Aborting...')



    def cloneRepository(self, destination, url):
        """ Clones repository from url into root destination folder """

        self.log.info('Cloning from {}\ninto {}'.format(url, destination))

        #  Repo.clone_from(url, destination)

        #  p = subprocess.Popen(['git', 'clone', url], cwd=destination)
        #  p.wait()

        #  ssh_executable = os.path.join('.', 'ssh_executable.sh')
        #  with Git().custom_environment(GIT_SSH=ssh_executable):
            #  Repo.clone_from(url, destination)


        # Somehow doesnt work properly?
        #  git_ssh_identity_file = os.path.expanduser('~/.ssh/github')
        #  git_ssh_cmd = 'ssh -i {}'.format(git_ssh_identity_file)
        #  with Git().custom_environment(GIT_SSH_COMMND=git_ssh_cmd):
            #  Repo.clone_from(url, destination)


    def setVerbose(self, flag):
        """ Verbose Flag Setter """

        if flag:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

