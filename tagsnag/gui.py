##
#  gui.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 18.04.2019.
#  Copyright (c) 2019 www.geeky.gent. All rights reserved.
#

import PySimpleGUI as gui

class GUI():
    """Tagsnag main class"""

    def __init__(self, path):
        super(GUI, self).__init__()

        self.path = path
        self.initial_setup()


    def initial_setup(self):
        ##
        # Instance variable init

        ##
        # Flags

        ##
        # Advanced setup
        self.create_window()

    def create_window(self):
        """ Setup GUI layout and start loop """

        layout = [[gui.Text('Containing Folder',
                            size=(8, 1)),
                   gui.Input(do_not_clear=True, key='_CONTAINING_DIR_'),
                   gui.FolderBrowse(),
                   gui.Button('Load')],

                  [gui.CBox('Upd.'),
                   gui.Txt('Repo Name'),
                   gui.Text('master'),
                   gui.Text('update needed', key='_UPDATE_'),
                   gui.Button('Browse')],

                  [gui.Button('Show'),
                   gui.Button('Exit')]]

        window = gui.Window('TagSnag').Layout(layout)

        # GUI Event Loop
        while True:
            event, values = window.Read()
            print(event, values)
            if event is None or event == 'Exit':
                break

            if event == 'Load':
                print("TODO: LOAD DIRECTORY:")

            if event == 'Show':
                # change the "output" element to be the value of "input" element  
                window.FindElement('_OUTPUT_').Update(values['_IN_'])

        window.Close()
