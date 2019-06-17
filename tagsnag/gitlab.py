
##
#  gitlab.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 17.06.2019
#  Copyright (c) 2019 www.geeky.gent. All rights reserved.
#

from pathlib import Path

class Gitlab():
    """This class handles Gitlab related tasks"""

    def __init__(self, path, cpu_count=1):
        self.initial_setup()


    def initial_setup(self):
        pass

    @staticmethod
    def config_exists():
        cfg_name = '.python-gitlab.cfg'
        cfg_path = Path('{}/{}'.format(Path.home(), cfg_name))
        return cfg_path.exists()



