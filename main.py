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

def main(argv):
    tagsnag = Tagsnag()
    try:
        ##
        # Create argument parser
        ap = ArgumentParser()
        ap.add_argument('-v', '--verbose', default=True, action='store_true', help='Increase verbosity')

        ap.add_argument('path', nargs='?')
        options = ap.parse_args()
        path = os.path.normpath(options.path)
        #  path  = os.getenv("~/Development/Python/Tagsnag_Test")

        ##
        # Configuring tagsnag using the provided arguments
        tagsnag.setVerbose(options.verbose)
        tagsnag.setXMLPath(path)

        tagsnag.start()


    except KeyboardInterrupt:
        tagsnag.log.info('Keyboard Interrupt detected: Exiting.')
        pass


if __name__ == "__main__":
    main(sys.argv)

