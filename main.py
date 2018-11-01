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

def main(argv):
    try:
        ##
        # Setting up logger
        logging.basicConfig(level=logging.WARNING, format='%(msg)s')
        LOG = logging.getLogger('logger')

        # Create filehandler
        fh = logging.FileHandler('main.log')
        fh.setLevel(logging.DEBUG)
        LOG.addHandler(fh)

        # Setting logger to debug setting for now, this value will change once we have parsed to arguments
        logging.getLogger().setLevel(logging.DEBUG)

        LOG.debug('Created Logger.')

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main(sys.argv)

