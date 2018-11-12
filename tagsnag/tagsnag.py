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
from distutils.dir_util import copy_tree
import logging
import subprocess
from concurrent.futures.thread import ThreadPoolExecutor
import re

from git import Git
from git import Repo
from git.exc import InvalidGitRepositoryError

from xml.etree import ElementTree as ET


class Tagsnag():
    """Tagsnag main class"""

    def __init__(self, cwd):
        super(Tagsnag, self).__init__()

        self.cwd = cwd
        self.initial_setup()


    def start_with_xml(self, xml_path):
        self.set_xml_path(xml_path)
        self.load_repositories(self.xml_path)

        for snag in self.snags:

            self.checkout(self.repositories[snag.repo_name], 'master')
            self.pull(self.repositories[snag.repo_name])
            self.checkout(self.repositories[snag.repo_name], snag.tag)
            #  self.searchFileName(path=snag.local_repo_path, containing_folder=snag.containing_folder, filenames=[snag.filename], extension=snag.extension)

            found_paths = self.search_files(filename=snag.filename, path=snag.local_repo_path, extension=snag.extension)
            if len(found_paths) > 0:
                self.copy_file_to_destination(path = found_paths[0], destination = snag.destination)


    def update_all_repos(self, should_prune=False):
        """Initiate threaded updates for all repositories in working directory"""

        if not self.repos:
            self.repos = self.collect_repositories(self.cwd)

        max_worker_count = self.available_cpu_count()
        self.log.info('Initiating repo update on {} threads.'.format(max_worker_count))

        with ThreadPoolExecutor(max_workers=max_worker_count) as executor:
            for repo in self.repos:
                executor.submit(self.update_repo, repo, should_prune=should_prune)


    def update_repo(self, repo, should_prune=False):
        """Update provided repository"""

        repo_path = self.get_root(repo)
        repo_name = os.path.basename(repo_path)

        self.log.info('Initiating update for {} repository'.format(repo_name))
        self.checkout(repo, 'master')
        self.pull(repo, should_prune=should_prune)


    def find_tag(self, repo, keyword):
        """Attempt to find tag in provided repo. Fallback to fuzzyfind tag"""

        found_tag = ""

        # newest tags first — tags are in arbitrary order, therefore 1. sort, 2. reverse
        #  tags = reversed(sorted(repo.tags, key=lambda t: t.tag.tagged_date))
        tags = repo.tags
        self.log.debug('TAG LIST:{}'.format(tags))

        # check if keyword corresponds to one tag exactly
        if keyword in tags:
            self.log.debug('{} correspends exactly'.format())
            found_tag = keyword
        else:
            for tag in tags:
                if keyword in str(tag):
                    found_tag = tag

        return found_tag


    def extract_directory_from_all_repos(self, tag, directory, destination):
        """Initiate threaded directory extraction for all repositories in working directory"""

        if not self.repos:
            self.repos = self.collect_repositories(self.cwd)

        max_worker_count = self.available_cpu_count()
        self.log.info('Initiating directory extraction on {} threads.'.format(max_worker_count))

        with ThreadPoolExecutor(max_workers=max_worker_count) as executor:
            for repo in self.repos:
                executor.submit(self.extract_directory, repo, tag, directory, destination)


    def extract_directory(self, repo, tag, directory, destination):
        """Attempt to extract described directory from provided repo"""

        repo_path = self.get_root(repo)
        repo_name = os.path.basename(repo_path)

        self.log.info('Searching for corresponding tag for keyword: {}'.format(tag))
        valid_tag = self.find_tag(repo, tag)
        if valid_tag == '':
            self.log.info('{} tag could not be found in {}. Skipping repo'.format(tag, repo_name))
            return

        self.checkout(repo, valid_tag)

        found_paths = self.search_directory(directory=directory, path=repo_path)

        if len(found_paths) > 0:
            self.copy_directory_to_destination(path = found_paths[0], destination = os.path.join(destination, repo_name))


    def extract_file_from_all_repos(self, tag, filename, extension, destination):
        """Initiate threaded file extraction for all repositories in working directory"""

        if not self.repos:
            self.repos = self.collect_repositories(self.cwd)

        max_worker_count = self.available_cpu_count()
        self.log.info('Initiating file extraction on {} threads.'.format(max_worker_count))

        with ThreadPoolExecutor(max_workers=max_worker_count) as executor:
            for repo in self.repos:
                executor.submit(self.extract_file, repo, tag, filename, extension, destination)


    def extract_file(self, repo, tag, filename, extension, destination):
        """Attempt to extract described file from provided repo"""

        repo_path = self.get_root(repo)
        repo_name = os.path.basename(repo_path)

        self.log.info('Searching for corresponding tag for keyword: {}'.format(tag))
        valid_tag = self.find_tag(repo, tag)
        if valid_tag == '':
            self.log.info('{} tag could not be found. Skipping repo'.format(tag))
            return

        self.checkout(repo, valid_tag)
        found_paths = self.search_files(filename=filename,
                path=repo_path,
                extension=extension)

        if len(found_paths) > 0:
            self.copy_file_to_destination(path = found_paths[0], destination = os.path.join(destination, repo_name + '.' + extension))


    def start(self):
        self.load_repositories(self.xml_path)

        for snag in self.snags:

            self.checkout(self.repositories[snag.repo_name], 'master')
            self.pull(self.repositories[snag.repo_name])
            self.checkout(self.repositories[snag.repo_name], snag.tag)
            #  self.searchFileName(path=snag.local_repo_path, containing_folder=snag.containing_folder, filenames=[snag.filename], extension=snag.extension)

            found_paths = self.search_files(filename=snag.filename,
                    path=snag.local_repo_path,
                    extension=snag.extension)

            if len(found_paths) > 0:
                self.copy_file_to_destination(path = found_paths[0], destination = snag.destination)


    def initial_setup(self):
        # Instance variable init
        self.snags = []
        self.repos = []
        self.repo_names_and_urls = {}
        self.repositories = {}

        # Advanced setup
        self.setup_logger()


    def enable_logfile(self):

        if self.log:
            # Create filehandler
            fh = logging.FileHandler('Tagsnag.log')
            fh.setLevel(logging.DEBUG)
            self.log.addHandler(fh)


    def setup_logger(self):
        """ Creating / configuring logger instance """

        logging.basicConfig(level=logging.WARNING, format='%(msg)s')
        self.log = logging.getLogger('logger')


        ##
        # Setting up argument parser
        self.log.debug('Setting up argument parser...')


    ##
    # XML methods

    def set_xml_path(self, path):
        """ XML Path Setter """

        self.log.debug('Provided Path: {}'.format(path))
        self.xml_path = path
        self.generate_snag_from_xml_path(path)


    def generate_snag_from_xml_path(self, path):
        """ Ingests XML from provided path """

        self.log.debug('Attempting to parse xml file: {}'.format(path))

        doc = ET.parse(path).getroot()

        for repo in doc.findall('repository'):
            url = repo.find('./url').text.strip().rstrip()

            # create repo name by converting to norm path, extracting basepath and cutting off before the .git extension
            repo_name = os.path.basename(os.path.normpath(url)).split('.')[0]
            repo_path = os.path.normpath("{}/{}".format(os.path.dirname(path), repo_name))
            self.repo_names_and_urls[repo_name]=url
            self.log.debug('Repository: {}'.format(url))

            for snag in repo.findall('snag'):
                tag = snag.find('tag').text.strip().rstrip()
                containing_folder = snag.find('folder').text.strip().rstrip()
                filename = snag.find('filename').text.strip().rstrip()
                extension = snag.find('extension').text.strip().rstrip()
                destination = snag.find('destination').text.strip().rstrip()
                destination = os.path.join(destination + containing_folder, repo_name + '.' + extension)

                s = Snag(url=url,
                        tag=tag,
                        repo_name=repo_name,
                        local_repo_path=repo_path,
                        containing_folder=containing_folder,
                        filename=filename,
                        extension=extension,
                        destination=destination)

                self.snags.append(s)
                self.log.debug('Tag: {}\nFilename: {}\nextension: {}\nDestination: {}\n'.format(tag, filename, extension, destination))

            self.log.debug('Extracted Snags: {}'.format(self.snags))
            self.log.info('Extracted Repositories: {}'.format(self.repo_names_and_urls))


    ##
    # Git methods

    def clone_repository(self, destination, url):
        """ Clones repository from url into root destination folder """

        self.log.info('Cloning from {}\ninto {}'.format(url, destination))
        self.log.info('--- This feature is not implemented yet ---')

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


    def checkout(self, repo, target):
        self.log.debug('Checking out {} in {}'.format(target, self.get_root(repo)))
        git = repo.git
        git.checkout(target)


    def pull(self, repo, should_prune=False):
        self.log.debug('Pulling origin/master {}'.format(self.get_root(repo)))
        git = repo.git

        if should_prune:
            git.pull('origin', 'master')
            git.pull('origin', '--tags')

        else:
            git.pull('origin', 'master', '--prune')
            git.pull('origin', '--tags', '--prune')



    def get_root(self, repo):
        return repo.git.rev_parse("--show-toplevel")


    ##
    # Filesystem methods

    def collect_repositories(self, path):

        repos = []
        self.log.debug('DETECT REPOSITORIES IN PATH: {}'.format(path))

        with os.scandir(path) as dirnames:
            for sub_dir in dirnames:
                repo_path = os.path.join(path,  sub_dir)

                if self.is_git_dir(repo_path):
                    repos.append(Repo(repo_path))

        return repos


    def load_repositories(self, path):
        """ Checks existence of repository paths and initiates clone """
        destination_path = os.path.dirname(path)
        for repo_name in self.repo_names_and_urls:
            url = self.repo_names_and_urls[repo_name]
            repo_path = os.path.normpath("{}/{}".format(destination_path, repo_name))
            self.log.debug(repo_path)
            if os.path.exists(repo_path):
                self.log.info('Repository {} exists.'.format(repo_name))

                repo = Repo(repo_path)
                assert not repo.bare
                self.repositories[repo_name] = repo

            else:
                self.log.info('Repository {} does not exist. Attempting to clone it...'.format(repo_name))
                # @todo: Implement
                #  self.clone_repository(destination=repo_path, url=url)



    def search_directory(self, directory, path='.'):
        normalized_dirname = directory.lower()
        found_paths = []

        for dirpath, dirnames, files in os.walk(path):

            # Skip .git folder
            if ".git" in dirpath:
                continue

            if normalized_dirname in dirpath.lower():
                self.log.info('Found Directory {}'.format(dirpath))
                found_paths.append(dirpath)

        return found_paths


    def search_files(self, filename, path='.', extension=''):
        extension = extension.lower()
        found_paths = []

        for dirpath, dirnames, files in os.walk(path):

            # Skip .git folder
            if ".git" in dirpath:
                continue

            for file in files:
                if extension and file.lower().endswith(extension):
                    if filename.lower() in file.lower():
                        foundPath = os.path.join(dirpath, file)
                        self.log.info('Found {}'.format(foundPath))
                        found_paths.append(foundPath)
                #  elif not extension:
                    #  print(os.path.join(dirpath, file))
        return found_paths


    def copy_file_to_destination(self, path, destination):
        self.log.info('Copying from:\n{}\nto:\n{}'.format(path, destination))

        if os.path.exists(path):

            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
            try:
                copyfile(path, destination)
            except IOError:
                self.log.info(IOError.message)
        else:
            self.log.info('File does not exist. Aborting...')


    def copy_directory_to_destination(self, path, destination):
        self.log.info('Copying from:\n{}\nto:\n{}'.format(path, destination))

        if os.path.exists(path):

            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
            try:
                copy_tree(path, destination)
            except IOError:
                self.log.info(IOError.message)
        else:
            self.log.info('File does not exist. Aborting...')


    ##
    # Helper methods

    def is_git_dir(self, path):
        try:
            Repo(path)
            return True
        except InvalidGitRepositoryError:
            return False


    def available_cpu_count(self):
        """ Number of available virtual or physical CPUs on this system, i.e.
        user/real as output by time(1) when called with an optimally scaling
        userspace-only program"""

        # cpuset
        # cpuset may restrict the number of *available* processors
        try:
            m = re.search(r'(?m)^Cpus_allowed:\s*(.*)$',
                        open('/proc/self/status').read())
            if m:
                res = bin(int(m.group(1).replace(',', ''), 16)).count('1')
                if res > 0:
                    return res
        except IOError:
            pass

        # Python 2.6+
        try:
            import multiprocessing
            return multiprocessing.cpu_count()
        except (ImportError, NotImplementedError):
            pass

        # https://github.com/giampaolo/psutil
        try:
            import psutil
            return psutil.cpu_count()   # psutil.NUM_CPUS on old versions
        except (ImportError, AttributeError):
            pass

        # POSIX
        try:
            res = int(os.sysconf('SC_NPROCESSORS_ONLN'))

            if res > 0:
                return res
        except (AttributeError, ValueError):
            pass

        # Windows
        try:
            res = int(os.environ['NUMBER_OF_PROCESSORS'])

            if res > 0:
                return res
        except (KeyError, ValueError):
            pass

        # jython
        try:
            from java.lang import Runtime
            runtime = Runtime.getRuntime()
            res = runtime.availableProcessors()
            if res > 0:
                return res
        except ImportError:
            pass

        # BSD
        try:
            sysctl = subprocess.Popen(['sysctl', '-n', 'hw.ncpu'],
                                    stdout=subprocess.PIPE)
            scStdout = sysctl.communicate()[0]
            res = int(scStdout)

            if res > 0:
                return res
        except (OSError, ValueError):
            pass

        # Linux
        try:
            res = open('/proc/cpuinfo').read().count('processor\t:')

            if res > 0:
                return res
        except IOError:
            pass

        # Solaris
        try:
            pseudoDevices = os.listdir('/devices/pseudo/')
            res = 0
            for pd in pseudoDevices:
                if re.match(r'^cpuid@[0-9]+$', pd):
                    res += 1

            if res > 0:
                return res
        except OSError:
            pass

        # Other UNIXes (heuristic)
        try:
            try:
                dmesg = open('/var/run/dmesg.boot').read()
            except IOError:
                dmesgProcess = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
                dmesg = dmesgProcess.communicate()[0]

            res = 0
            while '\ncpu' + str(res) + ':' in dmesg:
                res += 1

            if res > 0:
                return res
        except OSError:
            pass

        raise Exception('Can not determine number of CPUs on this system')


    ##
    # Setter and getter

    def set_verbose(self, flag):
        """ Verbose Flag Setter """
        self.verbose = flag

        if flag:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)


    def set_create_logfile(self, flag):

        self.should_create_logfile = flag

        if flag:
            self.enable_logfile()

