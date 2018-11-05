##
#!/usr/bin/python
#
#  main.py
#  Tagsnatch
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 31.10.2018.
#  Copyright (c) 2018 www.geeky.gent. All rights reserved.
#


import os
import sys
from argparse import ArgumentParser
from tagsnag.tagsnag import Tagsnag


def display_help():

    with open('./docs/help', 'r') as fh:
        help_string = fh.read()
        print("{}".format(help_string))



def main(argv):
    tagsnag = Tagsnag()
    try:
        cwd_path = os.getcwd()

        ##
        # Create argument parser
        ap = ArgumentParser()

        ##
        # Optionals grouped by category
        ap.add_argument('-d', '--destination', default=cwd_path, help='Destination Path')

        ap.add_argument('-e', '--extension', help='Specify a file extension')
        ap.add_argument('-f', '--filename', help='String the filename contains')
        ap.add_argument('-dir', '--directory', help='Name of the folder you would like to extract')

        ap.add_argument('-t', '--tag', help='String the Tag you would like to checkout contains')
        #  ap.add_argument('-b', '--branch', help='String the Tag you would like to checkout contains')

        ap.add_argument('-x', '--xml', help='Provide an xml config file')


        ##
        # Flags
        ap.add_argument('-u', '--update', default=False, action='store_true', help='Pull from origin/master into master prior to checkout')
        ap.add_argument('-v', '--verbose', default=False, action='store_true', help='Increase verbosity')
        ap.add_argument('-l', '--log', default=False, action='store_true', help='Create Logfile')

        #  ap.add_argument('path', nargs='?')
        #  path = os.path.normpath(options.path)

        options = ap.parse_args()

        ##
        # Bind options
        destination = options.destination
        extension   = options.extension
        filename    = options.filename
        directory   = options.directory
        tag         = options.tag
        xml_path    = options.xml

        # Flags
        should_update         = options.update
        verbose               = options.verbose
        should_create_logfile = options.log

        ##
        #  Configuring tagsnag using the provided arguments

        tagsnag.set_verbose(options.verbose)
        tagsnag.set_create_logfile(should_create_logfile)

        if xml_path:
            tagsnag.start_with_xml(xml_path)

        elif tag and filename and destination and extension:
            tagsnag.extract_file(cwd=cwd_path,
                    tag=tag,
                    filename=filename,
                    extension=extension,
                    destination=destination,
                    update=should_update)

        elif tag and directory and destination:
            tagsnag.extract_directory(cwd=cwd_path,
                    tag=tag,
                    directory=directory,
                    destination=destination,
                    update=should_update)

        else:
            display_help()






    except KeyboardInterrupt:
        tagsnag.log.info('Keyboard Interrupt detected: Exiting.')
        pass


if __name__ == "__main__":
    main(sys.argv)

