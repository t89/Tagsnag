##
#  gui.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 18.04.2019.
#  Copyright (c) 2019 www.geeky.gent. All rights reserved.
#


from .git import Git

##
# For more information about the used modules, take a peek into the setup.py
# file within the root folder

import PySimpleGUI as gui
from pathos.multiprocessing import ProcessingPool as Pool


class GUI():
    """Tagsnag main class"""

    def __init__(self, path, cpu_count=1):
        super(GUI, self).__init__()

        self.path = path
        self.cpu_count = cpu_count
        self.git = Git(self.path)
        self.repos = self.get_repositories_in_path(self.path)

        self.initial_setup()


    def initial_setup(self):
        ##
        # Instance variable init

        ##
        # Flags

        ##
        # Advanced setup
        self.create_window()


    def get_repositories_in_path(self, path):
        return self.git.collect_repositories(path)


    def layout_console(self):
        """ Generate layout for console output """


    def table_sizes(self):
        """ Returns a list of (width, 1) tuples for the repo table. Last element is the total width) """
        sizes = [6, 20, 35, 5, 10, 20, 11]

        # Last element is the sum of all (for progressbars)
        # sizes.append(sum(sizes))

        ##
        # No f*ing clue why the progressbar size differs by such a huge factor.
        # It _seemed_ like the value was interpreted as percentage, since it was roughly
        # 10% too large. But I tested that and can now rule that out. Hard coded as 85,
        # for now. @HARDCODED @FIX
        sizes.append(85)

        return [(x, 1) for x in sizes]

    def test_function(self, index, repo):
        print('Testfunction: {} {}'.format(index, repo))
        return [[]]


    def layout_repo_table(self, path):
        """ Generates layout for table """

        # orange="#F89433"
        # blue="#33C5EF"

        sizes = self.table_sizes()

        layout = [[gui.Text('Include', size=sizes[0]),
                   gui.Text('Repository', size=sizes[1]),
                   gui.Text('HEAD', size=sizes[2]),
                   gui.Text('Status', size=sizes[3]),
                   gui.Text('Upstream', size=sizes[4]),
                   gui.Text('Tags', size=sizes[5]),
                   gui.Text('Filebrowser', size=sizes[6])
                  ]]

        # Ignore the pooling completely, if we are limited to one core anyway.
        if (self.cpu_count > 1):
            with Pool(processes=self.cpu_count) as pool:
                layout_rows = list(pool.map(lambda e: self.table_row_layout_for_repo(e[0], e[1]), enumerate(self.repos)))
        else:
            layout_rows = list(map(lambda e: self.table_row_layout_for_repo(e[0], e[1]), enumerate(self.repos)))

        # Unwrap the inner lists
        # TODO: After an hour of debugging this was a working solution. A quick quess is, that the
        # list(...) function call wraps the lists another time. In this case I would have expected a
        # _single_ inner list which I could unwrap: [layout_rows] = list(map(...)). I can't though.
        # Fix if you have time to spare. For now take this "temporary" solution.

        for n in layout_rows:
            layout = layout + n

        print('\n'.format(layout))
        return layout


    def table_row_layout_for_repo(self, index, repo):

        orange='#F89433'
        blue='#33C5EF'

        name = self.git.get_repo_name(repo)

        status_color = 'black'
        upstream_color = 'black'
        head_state_color = 'black'

        if (self.git.is_dirty(repo)):
            status = 'Dirty'
            status_color = orange

        else:
            status = 'Clean'

        # Name of current branch
        branch = '{}'.format(self.git.active_branch(repo))

        # Description of Head State
        head_state = '{}'.format(self.git.head_state(repo))

        if (repo.head.is_detached):
            head_state_color = orange

        # Set to -1 so that we can distinguish if this value has been updated
        behind = -1

        # CHECK IF BRANCH IS NONE!!
        print('Dis none? {}'.format(branch))
        print(name)
        print(repo.remotes)
        print('Current Branch: {}'.format(branch))
        print('Current Headstate: {}'.format(head_state))

        if (branch in repo.branches):
            if (len(repo.remotes) > 0):
                for r in repo.remotes:
                    if r.name == 'origin':
                        behind = self.git.behind_branch(repo, 'origin', branch)
                        break

        if (behind == -1):
            upstream = 'n/a'

        elif (behind == 0):
            upstream = 'Up to date'

        else:
            upstream = "{} behind".format(behind)
            upstream_color = orange

        tags = [t.path.lstrip('refs/tags/') for t in repo.tags]
        repo_path = self.git.get_root(repo)

        sizes = self.table_sizes()

        layout = [[gui.CBox('', default=True, size=sizes[0], key='__{}_ACTIVE__'.format(index)),
                   gui.Text('{}'.format(name), font='Helvetica 10 bold', size=sizes[1], key='__{}_NAME__'.format(index)),
                   gui.Text('{}'.format(head_state), text_color=head_state_color, size=sizes[2], key='__{}_HEAD_STATE__'.format(index)),
                   gui.Text('{}'.format(status), text_color=status_color, size=sizes[3], key='__{}_STATUS__'.format(index)),
                   gui.Text('{}'.format(upstream), text_color=upstream_color, size=sizes[4], key='__{}_UPSTREAM__'.format(index)),
                   gui.InputCombo(tags, size=sizes[5], key='__{}_TAG__'.format(index)),
                   gui.Button('Open', size=sizes[6], tooltip='Open in Filebrowser', key='__{}_OPEN__'.format(index))],
                  [gui.ProgressBar(100, orientation='h', size=sizes[-1], bar_color=(blue, 'white'), border_width=0, key='__{}_PROGBAR__'.format(index))]
        ]

        return layout


    def create_window(self):
        """ Setup GUI layout and start loop """

        main_layout = [[gui.Text('Containing Folder',
                            size=(20, 1)),
                   # gui.Input('{}'.format(self.path), do_not_clear=True, key='_CONTAINING_DIR_'),
                   gui.FolderBrowse(),
                   gui.Text('{}'.format(self.path), key='_CONTAINING_DIR_')],

                  [gui.Text('Destination Folder',
                            size=(20, 1)),
                   gui.FolderBrowse(),
                   gui.Text('{}/TagSnag'.format(self.path), key='_DESTINATION_DIR_')]]


        main_layout = main_layout + [[gui.Text('_' * 140)]]
        main_layout = main_layout + self.layout_repo_table(self.path)
        main_layout = main_layout + [[gui.Text('_' * 140)]]

        main_layout = main_layout + [

            [gui.Button('Invert Selection'),
             gui.CBox('Autostash', default=True),
             gui.CBox('Prune', default=True),
             gui.CBox('Log', default=False),
             gui.CBox('Verbose', default=False),
             gui.Button('Update')],

            [gui.Input(default_text='git stash', size=(70,1), disabled=True),
             gui.Button('Execute for selection', disabled=True),
             gui.CBox('I know what I\'m doing...', default=False)],

            [gui.Input(default_text='Tag', size=(20,1)),
             gui.Input(default_text='Directory', size=(30,1)),
             gui.Input(default_text='Destination', size=(30,1)),
             gui.Button('Dry Run'),
             gui.Button('Extract', disabled=True)],

            [gui.Button('Exit'),
             gui.Button('Contact')]]

        log_layout = [[gui.Output(size=(200, 100))]]

        tab_layout = [[gui.TabGroup([[gui.Tab('Main', main_layout), gui.Tab('Log', log_layout)]])]]

        window = gui.Window('TagSnag').Layout(tab_layout)

        # GUI Event Loop
        while True:
            event, values = window.Read(timeout=10)
            if event != gui.TIMEOUT_KEY:
                # window.Element('_MULTIOUT_').Update(str(event) + '\n' + str(values), append=True)
                window.FindElement('__0_PROGBAR__').UpdateBar(50 + 1)
                window.FindElement('__1_PROGBAR__').UpdateBar(50 + 1)
                print(event, values)

            if event is None or event == 'Exit':
                break

            if event == 'Load':
                # window.FindElement('_DESTINATION_FOLDER_').Update(val
                print('TODO: LOAD DIRECTORY:')

            if event == 'Show':
                # change the "output" element to be the value of "input" element  
                window.FindElement('_OUTPUT_').Update(values['_IN_'])

        window.Close()
