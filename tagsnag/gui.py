##
#  gui.py
#  tagsnag
#
#  Created by Thomas Johannesmeyer (thomas@geeky.gent) on 18.04.2019.
#  Copyright (c) 2019 www.geeky.gent. All rights reserved.
#


##
# For more information about the used modules, take a peek into the setup.py
# file within the root folder

from .git import Git
from git import RemoteProgress

import os
import re
import PySimpleGUI as gui
from pathos.multiprocessing import ProcessingPool as Pool
from concurrent import futures
from concurrent.futures.thread import ThreadPoolExecutor

# Opening paths
import webbrowser

# Handle paths elegantly on all platforms
from pathlib import Path

from datetime import datetime
from datetime import timedelta

# TODO: REMOVE. Only for debugging purposes
import time
import inspect


##
# Color Config
color_highlight = '#F89433'
color_accent    = '#33C5EF'
color_negative = '#EF4E7B'
color_positive = '#6EBB82'


##
# Setting up keys for gui elements. I predefine the keys as
# strings to avoid typos. Also it enables me to change them all
# in one place. They are defined following this scheme:
# Number of the Table element, description of gui element
# btn = button, txt = text, cb = checkbox, fb = folderbrowse
# combo = bombobox, pb = progressbar
# <num>_{btn|txt|cb|fb|combo|pb}_<description without '_' inside>
# The idx numbers are attached to the string if relevant

##
# MAIN GUI
txt_containing_dir       = '_txt_containingdir'
txt_destination_dir      = '_txt_destinationdir'
txt_extraction_command   = '_txt_gitcommand'
txt_extraction_tag       = '_txt_gittag'
txt_extraction_directory = '_txt_gitdirectory'
# txt_git_destination      = '_txt_gitdestination'

btn_folderbrowse     = '_btn_folderbrowse'
btn_invert_selection = '_btn_invertselection'
btn_checkout_master  = '_btn_checkout_master'
btn_update           = '_btn_update'
btn_execute          = '_btn_execute'
btn_dryrun           = '_btn_dryrun'
btn_extract          = '_btn_extract'
btn_exit             = '_btn_exit'
btn_contact          = '_btn_contact'
btn_destination_open = '_btn_destination_open'

cb_autostash    = '_cb_autostash'
cb_prune        = '_cb_prune'
cb_log          = '_cb_log'
cb_verbose      = '_cb_verbose'
cb_confirmation = '_cb_confirmation'

##
# Table GUI
cb_active          = '_cb_active'
txt_name           = '_txt_name'
txt_head_state     = '_txt_head_state'
txt_status         = '_txt_status'
txt_upstream       = '_txt_upstream'
combo_branches     = '_combo_branches'
combo_tags         = '_combo_tags'
btn_open           = '_btn_open'
btn_stash          = '_btn_stash'
txt_current_action = '_txt_currentaction'
pb_repo_action     = '_pb_repoaction'

na_string = '—'
cmd_fetch = 'fetch'
cmd_stash = 'stash'
cmd_pull = 'pull'


class ProgressPrinter(RemoteProgress):


    ##
    # Overriding GitPythons's implementation until issue #871 is fixed.
    # I don't have the time to develop the tests at the moment.
    # Ref: https://github.com/gitpython-developers/GitPython/pull/872

    def _parse_progress_line(self, line):
        """Parse progress information from the given line as retrieved by git-push
        or git-fetch.

        - Lines that do not contain progress info are stored in :attr:`other_lines`.
        - Lines that seem to contain an error (i.e. start with error: or fatal:) are stored
        in :attr:`error_lines`.

        :return: list(line, ...) list of lines that could not be processed"""
        # handle
        # Counting objects: 4, done.
        # Compressing objects:  50% (1/2)   \rCompressing objects: 100% (2/2)   \rCompressing objects: 100% (2/2), done.
        self._cur_line = line = line.decode('utf-8') if isinstance(line, bytes) else line

        if len(self.error_lines) > 0 or self._cur_line.startswith(('error:', 'fatal:')):
            self.error_lines.append(self._cur_line)
            return []

        elif 'up to date' in self._cur_line:
            # Checking this way instead of startswith, because debugging for
            # startswith(' = [up to date]') is going to be a major pain if just
            # a single space or bracket changes.

            # Strip the initial ' = [up to date]' from the line
            message_string = line.split('date]', 1)[-1]

            # Trim whitespace
            message_string = ' '.join(message_string.split())

            self.update(9999,
                        1,
                        1,
                        message_string)

        sub_lines = line.split('\r')
        failed_lines = []

        for sline in sub_lines:
            # find escape characters and cut them away - regex will not work with
            # them as they are non-ascii. As git might expect a tty, it will send them
            last_valid_index = None

            for i, c in enumerate(reversed(sline)):

                if ord(c) < 32:
                    # its a slice index
                    last_valid_index = -i - 1
                # END character was non-ascii
            # END for each character in sline
            if last_valid_index is not None:
                sline = sline[:last_valid_index]
            # END cut away invalid part
            sline = sline.rstrip()

            cur_count, max_count = None, None
            match = self.re_op_relative.match(sline)
            if match is None:
                match = self.re_op_absolute.match(sline)

            if not match:
                self.line_dropped(sline)
                failed_lines.append(sline)
                continue
            # END could not get match

            op_code = 0
            remote, op_name, percent, cur_count, max_count, message = match.groups()  # @UnusedVariable

            # get operation id
            if op_name == "Counting objects":
                op_code |= self.COUNTING
            elif op_name == "Compressing objects":
                op_code |= self.COMPRESSING
            elif op_name == "Writing objects":
                op_code |= self.WRITING
            elif op_name == 'Receiving objects':
                op_code |= self.RECEIVING
            elif op_name == 'Resolving deltas':
                op_code |= self.RESOLVING
            elif op_name == 'Finding sources':
                op_code |= self.FINDING_SOURCES
            elif op_name == 'Checking out files':
                op_code |= self.CHECKING_OUT
            else:
                # Note: On windows it can happen that partial lines are sent
                # Hence we get something like "CompreReceiving objects", which is
                # a blend of "Compressing objects" and "Receiving objects".
                # This can't really be prevented, so we drop the line verbosely
                # to make sure we get informed in case the process spits out new
                # commands at some point.
                self.line_dropped(sline)
                # Note: Don't add this line to the failed lines, as we have to silently
                # drop it
                self.other_lines.extend(failed_lines)
                return failed_lines
            # END handle op code

            # figure out stage
            if op_code not in self._seen_ops:
                self._seen_ops.append(op_code)
                op_code |= self.BEGIN
            # END begin opcode

            if message is None:
                message = ''
            # END message handling

            message = message.strip()
            if message.endswith(self.DONE_TOKEN):
                op_code |= self.END
                message = message[:-len(self.DONE_TOKEN)]
            # END end message handling
            message = message.strip(self.TOKEN_SEPARATOR)

            self.update(op_code,
                        cur_count and float(cur_count),
                        max_count and float(max_count),
                        message)
        # END for each sub line
        self.other_lines.extend(failed_lines)
        return failed_lines

    def update(self, op_code, cur_count, max_count=None, message=''):
        print("op_code: {}\ncur_count: {}\nmax_count: {}\nmessage: {}\n".format(op_code,
                                                                                cur_count,
                                                                                max_count,
                                                                                message))

        if self.r_idx != None and self.delegate:
            progress = cur_count / (max_count or 100.0)
            self.delegate.set_progress(self.r_idx, message, progress)

class GUI:
    """Tagsnag GUI class"""

    def __init__(self, path, cpu_count=1):
        super(GUI, self).__init__()

        self.path      = path
        self.cpu_count = cpu_count
        self.git       = Git(self.path)
        self.repos     = self.get_repositories_in_path(self.path)

        self.r_idx_is_selected               = {}
        self.r_idx_progress_map              = {}
        self.r_idx_progress_message_map      = {}
        self.r_idx_progress_color_map        = {}
        self.r_idx_active_cmd_map            = {}
        self.r_idx_behind_origin_map         = {}
        self.r_idx_last_action_timestamp_map = {}

        self.initialize_dicts_for_repo_count(len(self.repos))

        self.did_fetch = True

        self.window    = None

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


    def initialize_dicts_for_repo_count(self, count):

        for r_idx in range(0, count):
            self.r_idx_active_cmd_map[r_idx]            = na_string
            self.r_idx_progress_map[r_idx]              = 0
            self.r_idx_progress_message_map[r_idx]      = ''
            self.r_idx_progress_color_map[r_idx]        = 'black'
            self.r_idx_behind_origin_map[r_idx]         = 0
            self.r_idx_last_action_timestamp_map[r_idx] = datetime.now() - timedelta(seconds=5)


    def table_sizes_dict(self):
        """ Returns a dict {<element_key> : (<width>, 1)} for the repo table. """

        ##
        # I wanted the progress bar (pb_repo_action) to span the whole table, so I summed all widths.
        # Turns out it's way too large. I don't have time to debug this behaviour now.
        #
        # No f*ing clue why the progressbar size differs by such a huge factor.
        # It _seemed_ like the value was interpreted as percentage, since it was roughly
        # 10% too large. But I tested that and can now rule that out. Hard coded as 85,
        # for now. @HARDCODED @FIX

        sizes_dict = {cb_active          : (6, 1),
                      txt_name           : (20, 1),
                      txt_head_state     : (35, 1),
                      txt_status         : (5, 1),
                      txt_upstream       : (10, 1),
                      combo_branches       : (20, 1),
                      combo_tags         : (20, 1),
                      btn_open           : (6, 1),
                      btn_stash          : (6, 1),
                      txt_current_action : (5, 1),
                      pb_repo_action     : (95, 1)}

        return sizes_dict


    def layout_repo_table(self, path):
        """ Generates layout for table """

        sizes = self.table_sizes_dict()

        layout = [[gui.Text('Git-Cmd',
                            size=sizes[txt_current_action]),

                   gui.Text('Include',
                            size=sizes[cb_active]),

                   gui.Text('Repository',
                            size=sizes[txt_name]),

                   gui.Text('HEAD',
                            size=sizes[txt_head_state]),

                   gui.Text('Status',
                            size=sizes[txt_status]),

                   gui.Text('Upstream',
                            size=sizes[txt_upstream]),

                   gui.Text('Branches',
                            # The combo menu width is 3 chars wider than defined
                            size=(sizes[combo_branches][0] + 3, sizes[combo_branches][1])),

                   gui.Text('Tags',
                            # The combo menu width is 3 chars wider than defined
                            size=(sizes[combo_tags][0] + 3, sizes[combo_tags][1])),

                   gui.Text('Cleanup',
                            size=sizes[btn_stash]),

                   gui.Text('Browser',
                            size=sizes[btn_open])
                  ]]

        # Ignore the pooling completely, if we are limited to one core anyway.
        if (self.cpu_count > 1):
            with Pool(processes=self.cpu_count) as pool:
                layout_rows = list(pool.map(lambda e: self.table_row_layout_for_repo(e[0], e[1]),
                                            enumerate(self.repos)))
        else:
            layout_rows = list(map(lambda e: self.table_row_layout_for_repo(e[0], e[1]),
                                   enumerate(self.repos)))

        # Unwrap the inner lists
        # TODO: After an hour of debugging this was a working solution. A quick guess is, that the
        # list(...) function call wraps the lists another time. In this case I would have expected a
        # _single_ inner list which I could unwrap: [layout_rows] = list(map(...)). I can't though.
        # Fix if you have time to spare. For now take this "temporary" solution.

        for n in layout_rows:
            layout = layout + n

        print('\n'.format(layout))
        return layout


    def fetch_repos(self, repos):
        # get indeces from main repo list
        indeces = [self.repos.index(r) for r in repos]
        if (self.cpu_count > 1):
            with ThreadPoolExecutor(max_workers=self.cpu_count) as executor:
                for idx in indeces:
                    executor.submit(self.fetch_index, idx)

        else:
            for idx in indeces:
                self.fetch_index(idx = idx)

        self.did_fetch = True


    def fetch_all(self):
        self.fetch_repos(self.repos)


    def fetch_index(self, idx):

        repo = self.repos[idx]

        # Name of current branch
        branch = '{}'.format(self.git.active_branch(repo))
        print('{} BRANCH:{}'.format(idx, branch))

        # Description of Head State
        head_state = '{}'.format(self.git.head_state(repo))

        # Set to -1 so that we can distinguish if this value has been updated
        behind = -1

        # Assure we are fetching an actual branch
        print('1{}'.format(idx))
        if (branch in repo.branches):

            print('2{}'.format(idx))
            # Assure we have remotes to fetch from
            if (len(repo.remotes) > 0):
                print('3{}'.format(idx))

                # Search for origin
                for r in repo.remotes:

                    if r.name == 'origin':
                        print('4{}'.format(idx))
                        self.r_idx_active_cmd_map[idx] = cmd_fetch
                        self.r_idx_progress_map[idx]   = 0

                        print('{} Fetch about to start'.format(idx))
                        progress_printer = ProgressPrinter()

                        # Abusing Python here a bit.
                        progress_printer.r_idx = idx
                        progress_printer.delegate = self

                        fetch_result = self.git.fetch(repo, progress_printer = progress_printer)
                        # fetch_result = self.git.fetch(repo)

                        print(fetch_result)
                        # We got the fetch results > Progress finished
                        self.r_idx_last_action_timestamp_map[idx] = datetime.now()

                        behind = self.git.behind_branch(repo, 'origin', branch)
                        break

        self.r_idx_behind_origin_map[idx] = behind


    def merge_index(self, idx):

        repo = self.repos[idx]

        # Name of current branch
        branch = '{}'.format(self.git.active_branch(repo))

        # Descriptio of Head State
        head_state = '{}'.format(self.git.head_state(repo))

        # Set to -1 so that we can distinguish if this value has been updated
        behind = -1

        # Assure we are fetching an actual branch
        if (branch in repo.branches):

            # Assure we have remotes to fetch from
            if (len(repo.remotes) > 0):

                # Search for origin
                for r in repo.remotes:

                    if r.name == 'origin':
                        self.r_idx_active_cmd_map[idx] = cmd_fetch
                        self.r_idx_progress_map[idx]   = 0

                        print('{} Fetch about to start'.format(idx))
                        progress_printer = ProgressPrinter()

                        # Abusing Python here a bit.
                        progress_printer.repo_idx = idx
                        progress_printer.delegate = self

                        fetch_result                   = self.git.fetch(repo, progress_printer = progress_printer)
                        behind                         = self.git.behind_branch(repo, 'origin', branch)
                        break

        self.r_idx_behind_origin_map[idx] = behind


    def table_row_layout_for_repo(self, idx, repo):
        """ Takes index and repo to generate a table row for it. """

        # name = self.git.get_repo_name(repo)

        # status_color     = 'black'
        # upstream_color   = 'black'
        # head_state_color = 'black'

        # is_dirty         = self.git.is_dirty(repo)
        # if (is_dirty):
        #     status       = 'Dirty'
        #     status_color = color_highlight

        # else:
        #     status = 'Clean'

        # # Name of current branch
        # branch = '{}'.format(self.git.active_branch(repo))

        # # Descriptio of Head State
        # head_state = '{}'.format(self.git.head_state(repo))

        # if (repo.head.is_detached):
        #     head_state_color = color_highlight

        # # Set to -1 so that we can distinguish if this value has been updated
        # behind = -1

        # # CHECK IF BRANCH IS NONE!!
        # # print('Dis none? {}'.format(branch))
        # # print(name)
        # # print(repo.remotes)
        # # print('Current Branch: {}'.format(branch))
        # # print('Current Headstate: {}'.format(head_state))

        # if (branch in repo.branches):
        #     if (len(repo.remotes) > 0):
        #         for r in repo.remotes:
        #             if r.name == 'origin':
        #                 self.r_idx_active_cmd_map[idx] = cmd_fetch
        #                 fetch_result                   = self.git.fetch(repo, progress_printer = ProgressPrinter())
        #                 behind                         = self.git.behind_branch(repo, 'origin', branch)
        #                 break

        # if (behind == -1):
        #     upstream = 'n/a'

        # elif (behind == 0):
        #     upstream = 'Up to date'

        # else:
        #     upstream       = "{} behind".format(behind)
        #     upstream_color = color_highlight

        # tags = [t.path.lstrip('refs/tags/') for t in repo.tags]
        # no_tags_available = (len(tags) == 0)

        # if (no_tags_available):
        #     tags.append('No Tags')
        # else:
        #     tags.sort(reverse         = True)

        # repo_path = self.git.get_root(repo)

        sizes = self.table_sizes_dict()

        layout                         = [[gui.Text('{}'.format(na_string),
                            font       = 'Helvetica 10 italic',
                            text_color = 'black',
                            size       = sizes[txt_current_action],
                            key                = '{}{}'.format(idx, txt_current_action)),

                   gui.CBox('',
                            default = True,
                            size    = sizes[cb_active],
                            key='{}{}'.format(idx, cb_active)),

                   gui.Text('{}'.format('Loading'),
                            font = 'Helvetica 10 bold',
                            size = sizes[txt_name],
                            key          = '{}{}'.format(idx, txt_name)),

                   gui.Text('{}'.format(''),
                            text_color = 'black',
                            size       = sizes[txt_head_state],
                            key                = '{}{}'.format(idx, txt_head_state)),

                   gui.Text('{}'.format(''),
                            text_color='black',
                            size = sizes[txt_status],
                            key          = '{}{}'.format(idx, txt_status)),

                   gui.Text('{}'.format(''),
                            text_color = 'black',
                            size       = sizes[txt_upstream],
                            key                = '{}{}'.format(idx, txt_upstream)),

                   gui.InputCombo([na_string],
                                  size     = sizes[combo_branches],
                                  key      = '{}{}'.format(idx, combo_branches),
                                  # change_submits = True,
                                  enable_events = True,
                                  disabled = True),

                   gui.InputCombo([na_string],
                                  size     = sizes[combo_tags],
                                  key      = '{}{}'.format(idx, combo_tags),
                                  # change_submits = True,
                                  enable_events = True,
                                  disabled = True),

                   gui.Button('Stash',
                              size     = sizes[btn_stash],
                              disabled = True,
                              key      = '{}{}'.format(idx, btn_stash)),

                   gui.Button('Open',
                              size      = sizes[btn_open],
                              # tooltip         = 'Open in Filebrowser',
                              key       = '{}{}'.format(idx, btn_open))],

                  [gui.ProgressBar(100,
                                   orientation  = 'h',
                                   size                 = sizes[pb_repo_action],
                                   bar_color    = (color_accent, 'white'),
                                   border_width         = 0,
                                   key          = '{}{}'.format(idx, pb_repo_action))]
        ]

        return layout


    def reset_progress_for_repo_idx(self, r_idx):

        self.r_idx_progress_map[r_idx]         = 0
        self.r_idx_active_cmd_map[r_idx]       = na_string
        # self.r_idx_progress_message_map[r_idx] = na_string


    def refresh_gui_for_repo_idx(self, r_idx, include_tags = False):

        repo = self.repos[r_idx]
        assert repo

        name = self.git.get_repo_name(repo)

        status_color     = 'black'
        upstream_color   = 'black'
        head_state_color = 'black'

        is_dirty = self.git.is_dirty(repo)

        if (is_dirty):
            status       = 'Dirty'
            status_color = color_negative

        else:
            status = 'Clean'

        # Name of current branch
        branch = '{}'.format(self.git.active_branch(repo))

        # Description of head state
        head_state = na_string

        # last finished progress
        if (datetime.now() - self.r_idx_last_action_timestamp_map[r_idx] > timedelta(seconds=5)):
            # 5 Seconds have passed since last progress message change
            head_state = '{}'.format(self.git.head_state(repo))

            if (repo.head.is_detached):
                head_state_color = color_highlight

        else:
            head_state = '{}'.format(self.r_idx_progress_message_map[r_idx])
            head_state_color = self.r_idx_progress_color_map[r_idx]
            self.reset_progress_for_repo_idx(r_idx)


        tags = [re.sub(r"refs/tags/", "", "{}".format(t)) for t in repo.tags]
        no_tags_available = (len(tags) == 0)

        if (no_tags_available):
            tags.append('No Tags')

        else:
            tags.sort(reverse=True)
            tags.insert(0, na_string) # No selection


        branches = [re.sub(r"refs/heads/", "", "{}".format(b)) for b in repo.branches]
        no_branches_available = (len(branches) == 0)

        if (no_branches_available):
            branches.append('No Branches')

        else:
            branches.insert(0, na_string) # No selection

        gui_txt_git_cmd    = self.window.FindElement('{}{}'.format(r_idx, txt_current_action))
        gui_txt_name       = self.window.FindElement('{}{}'.format(r_idx, txt_name))
        gui_txt_head_state = self.window.FindElement('{}{}'.format(r_idx, txt_head_state))
        gui_txt_status     = self.window.FindElement('{}{}'.format(r_idx, txt_status))
        gui_txt_upstream   = self.window.FindElement('{}{}'.format(r_idx, txt_upstream))
        gui_combo_branches = self.window.FindElement('{}{}'.format(r_idx, combo_branches))
        gui_combo_tags     = self.window.FindElement('{}{}'.format(r_idx, combo_tags))
        gui_btn_stash      = self.window.FindElement('{}{}'.format(r_idx, btn_stash))

        active_command = self.r_idx_active_cmd_map[r_idx]
        active_command_color = 'black' if (active_command == na_string) else color_accent

        gui_txt_git_cmd.Update(value = active_command,
                               text_color = active_command_color)

        gui_txt_name.Update(value = name)

        gui_txt_head_state.Update(value = head_state,
                                    text_color = head_state_color)

        gui_txt_status.Update(value = status,
                              text_color = status_color)


        behind_count = self.r_idx_behind_origin_map[r_idx]
        upstream = ''

        if (behind_count == -1):
            upstream = na_string

        if (behind_count == 0):
            upstream = 'Up to date'

        else:
            upstream       = "{} behind".format(behind_count)
            upstream_color = color_highlight


        gui_txt_upstream.Update(value = upstream,
                                text_color = upstream_color)

        if include_tags:
            tag_selection_idx = 0

            if head_state in tags:
                tag_selection_idx = tags.index(head_state)

            gui_combo_tags.Update(values = tags,
                                  set_to_index = tag_selection_idx,
                                  disabled = (no_tags_available or is_dirty))


        branch_selection_idx = 0

        if head_state in branches:
            branch_selection_idx = branches.index(head_state)

        gui_combo_branches.Update(values = branches,
                                  set_to_index = branch_selection_idx,
                                  disabled = (no_branches_available or is_dirty))

        gui_btn_stash.Update(disabled = (not is_dirty))


    def assign_values(self, values):
        """ Takes the gui loop values and updates the instance variables """

        ##
        # Only _editable_ text elements return a value!
        try:
            # Assign Checkboxes
            self.should_autostash = values[cb_autostash]
            self.should_prune     = values[cb_prune]
            self.should_log       = values[cb_log]
            self.is_verbose       = values[cb_verbose]
            self.is_confirmed     = values[cb_confirmation]

            # Assign input fields
            self.destination_dir      = values[txt_destination_dir]
            self.extraction_command   = values[txt_extraction_command]
            self.extraction_tag       = values[txt_extraction_tag]
            self.extraction_directory = values[txt_extraction_directory]
            self.extraction_filename  = ''
            self.extraction_extension = ''

            for idx in range(0, len(self.repos)):
                # TODO: Assign. GUI layout is generated in parallel, do NOT
                # assume the order to be the same as in self.repos!
                active = values['{}{}'.format(idx, cb_active)]
                self.r_idx_is_selected[idx] = active

        except KeyError as error:
            print(error)


    def create_window(self):
        """ Setup GUI layout and start loop """


        main_layout = [[gui.Text('Containing Folder',
                                 size=(15, 1)),
                        gui.FolderBrowse(target=txt_containing_dir, key=btn_folderbrowse),
                        gui.Text('{}'.format(self.path), key=txt_containing_dir)]]

        # Spacer
        spacer = [[gui.Text('_' * 133)]]

        main_layout = main_layout + spacer
        table_layout = self.layout_repo_table(self.path)

        main_layout = main_layout + table_layout

        # print('\n'.join(str(line) for line in self.layout_repo_table(self.path)))
        main_layout = main_layout + spacer



        # These elements will be placed directly below the table and are not mode specific
        main_button_row_layout = [
            [gui.Button('Invert Selection',
                        key=btn_invert_selection),

             gui.Button('Checkout \'master\'',
                        key=btn_checkout_master),

             gui.Button('Pull selected branch',
                        key=btn_update),

             gui.CBox('Autostash',
                      default=True,
                      key=cb_autostash),

             gui.CBox('Prune',
                      default=True,
                      key=cb_prune),

             gui.CBox('Log',
                      default=False,
                      key=cb_log),

             gui.CBox('Verbose',
                      default=False,
                      key=cb_verbose)]]

        main_layout = main_layout + main_button_row_layout

        command_mode_layout = [[gui.Input(default_text='git stash',
                                          size=(70, 1),
                                          disabled=True,
                                          key=txt_extraction_command),

             gui.Button('Execute for selection',
                        disabled=True,
                        key=btn_execute),

             gui.CBox('I know what I\'m doing...',
                      default=False,
                      key=cb_confirmation)]]

        extraction_mode_layout = [[gui.Text('{}'.format('Extract from Tag:'),
                                            size=(15, 1)),

               gui.Input(default_text='',
                         size=(30, 1),
                         key=txt_extraction_tag),

               gui.Text('{}'.format('Fuzzy search enabled. \'02\' will match the latest tag containing 02 within it: <02_Release>, <Release_02>, <v02_RC> would all be matched.'))],

              [gui.Text('{}'.format('Extract Directory:'),
                        size=(15, 1)),

               gui.Input(default_text='',
                         size=(30,1),
                         key=txt_extraction_directory),

               gui.Text('{}'.format('Fuzzy & Recursive. First directory matched will be extracted. Starting from root'))],

              [gui.Text('{}'.format('Extract into:'),
                        size=(15, 1)),

               gui.FolderBrowse(target=txt_destination_dir),

               gui.Input(default_text='{}/Snagged'.format(self.path),
                         size=(70, 1),
                         key=txt_destination_dir),

               gui.Button('Open',
                          key=btn_destination_open)],

              [gui.Button('Dry Run',
                          key=btn_dryrun),

               gui.Button('Extract',
                          disabled=False,
                          key=btn_extract)]]

        # Bottom Tab assembly
        bottom_tab_layout = [[gui.TabGroup([[gui.Tab('Extraction Mode',
                                                     extraction_mode_layout),

                                             gui.Tab('Command Mode',
                                                     command_mode_layout)]])]]

        main_layout = main_layout + bottom_tab_layout

        main_layout = main_layout + [[gui.Button('Exit',
                                                 key=btn_exit),

                                      gui.Button('Contact',
                                                 key=btn_contact)]]

        # Main Tab Configuration
        log_layout = [[gui.Output(size=(200, 100))]]

        empty_layout = [[]]
        main_tab_layout = [[gui.TabGroup([[gui.Tab('Main',
                                                   main_layout),

                                           gui.Tab('Log',
                                                   empty_layout)]])]]

        self.window = gui.Window('TagSnag',
                            icon='tagsnag.ico').Layout(main_tab_layout).Finalize()

        # GUI Event Loop
        while True:
            event, values = self.window.Read(timeout=50)

            include_tags = False
            if self.did_fetch:
                self.did_fetch = False
                include_tags   = True

            for i in range(0, (len(self.repos))):
                self.window.FindElement('{}{}'.format(i, pb_repo_action)).UpdateBar(self.r_idx_progress_map[i])
                self.refresh_gui_for_repo_idx(i, include_tags)

            self.assign_values(values)

            if event != gui.TIMEOUT_KEY:
                # print(event, values)
                pass

            if event == btn_invert_selection:
                for i in range(0, (len(self.repos))):
                    checkbox = self.window.FindElement('{}{}'.format(i, cb_active))
                    checkbox.Update(value=(not checkbox.Get()))

            elif btn_stash in event:
                repo_idx = int(event.split('_')[0])
                btn_element = '{}{}'.format(repo_idx, btn_stash)
                status_element = '{}{}'.format(repo_idx, txt_status)

                repo = self.repos[repo_idx]
                assert repo
                self.git.stash_repo(repo)

                # Update UI
                self.window.FindElement(btn_element).Update(disabled=True)
                self.window.FindElement(status_element).Update(value = 'Clean', text_color='black')

            elif btn_open in event:
                repo_idx = int(event.split('_')[0])
                element_name = '{}{}'.format(repo_idx, btn_open)

                repo = self.repos[repo_idx]
                assert repo
                path = Path(self.git.get_root(repo))

                self.open_path(path.absolute())

            elif event == btn_checkout_master:
                selected_repos = self.get_selected_repos()

                for repo in selected_repos:
                    self.git.checkout(repo, 'master')

            elif event == btn_update:
                selected_repos = self.get_selected_repos()

                self.fetch_repos(selected_repos)

                for repo in selected_repos:
                    active_branch = self.git.active_branch(repo)
                    print('Active Branch {}'.format(active_branch))

                    if (active_branch == "") or (repo.head.is_detached):
                        active_branch = 'master'

                    print('Active Branch {}'.format(active_branch))

                    # self.git.checkout(repo, '{}'.format(active_branch))
                    self.git.merge(repo=repo,
                                   source_branch_name='origin/{}'.format(active_branch),
                                   target_branch_name='{}'.format(active_branch))
                # self.git.update_repos(selected_repos)

            elif event == btn_destination_open:
                path = Path(self.destination_dir)
                self.open_path(path.absolute())

            elif combo_branches in event:
                repo_idx = int(event.split('_')[0])
                element_name = '{}{}'.format(repo_idx, combo_branches)
                selected_branch = values[element_name]

                if not selected_branch == na_string:
                    self.git.checkout(self.repos[repo_idx], selected_branch)

            elif combo_tags in event:
                repo_idx = int(event.split('_')[0])
                element_name = '{}{}'.format(repo_idx, combo_tags)
                selected_tag = values[element_name]

                if not selected_tag == na_string:
                    self.git.checkout(self.repos[repo_idx], selected_tag)


            elif event == btn_extract:
                selected_repos = self.get_selected_repos()
                # TODO: Implement filename / extension

                did_start = False
                if self.extraction_tag != "" and self.extraction_filename != "" and self.extraction_extension != "":
                    did_start = True
                    self.git.extract_file_from_repos(repos = selected_repos,
                                                     tag=self.extraction_tag,
                                                     filename=self.extraction_filename,
                                                     extension=self.extraction_extension,
                                                     destination=self.destination_dir)

                elif self.extraction_tag != "" and self.extraction_directory != "" and self.destination_dir != "":
                    did_start = True
                    self.git.extract_directory_from_repos(repos=selected_repos,
                                                          tag=self.extraction_tag,
                                                          directory=self.extraction_directory,
                                                          destination=self.destination_dir)


                for idx in self.get_selected_indeces():
                    if did_start:
                        if self.git.status_map[self.repos[idx]] == True:
                            self.r_idx_progress_color_map[idx] = color_positive
                            self.r_idx_progress_message_map[idx] = 'Extraction completed'

                        else:
                            self.r_idx_progress_color_map[idx] = color_negative
                            self.r_idx_progress_message_map[idx] = 'Nothing found.'
                    else:
                        self.r_idx_progress_color_map[idx] = color_negative
                        self.r_idx_progress_message_map[idx] = 'Missing Info'

                    self.r_idx_last_action_timestamp_map[idx] = datetime.now()


            elif event == 'Show':
                # change the "output" element to be the value of "input" element
                # self.window.FindElement('_OUTPUT_').Update(values['_IN_'])
                pass

            elif event is None or event == btn_exit:
                break

            elif event == btn_contact:
                # Open Mail Client
                # mailto_link = 'mailto:tagsnag@geeky.gent?subject=Tagsnag&body=\n\nTagsnag Version: 0.9'
                # sp = subprocess.Popen([mailto_link, values['_URL_']], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # self.open_path(Path(mailto_link))
                pass


        self.window.Close()


    def open_path(self, path):
        """ Open provided path """

        ##
        # I tried to avoid this solution! I really did. Apparently the only reliable
        # and sane solution for opening a path in the filebrowser in a multiplatform
        # application is to import webbrowser and call the path within. I'm sorry.

        if not os.path.isdir(path):
            os.mkdir(path)

        webbrowser.open(path.as_uri())

    ##
    # Alternative to the webbrowser solution which does not perform reliably (at all) on all platforms
    # def open_path(self, path):
    #     platform = sys.platform

    #     if platform == 'darwin':
    #         def openFolder(path):
    #             subprocess.check_call(['open', '--', path])
    #     elif platform == 'linux2':
    #         def openFolder(path):
    #             subprocess.check_call(['xdg-open', '--', path])
    #     elif platform == 'win32':
    #         def openFolder(path):
    #             subprocess.check_call(['explorer', path])

    def set_progress(self, r_idx, message, progress):
        progress = min(progress, 1.0)
        progress *= 100
        print('Progress ={}'.format(round(progress)))
        print('R_IDX: {} message: {} progress: {}'.format(r_idx, message, progress))
        self.r_idx_progress_map[r_idx] = progress
        self.r_idx_progress_message_map[r_idx] = message


    def get_selected_indeces(self):
        """ Returns list of indeces which have been selected """
        return [k for k,v in self.r_idx_is_selected.items() if v == True]


    def get_selected_repos(self):
        """ Returns list of repositories which have been selected """
        return [self.repos[k] for k,v in self.r_idx_is_selected.items() if v == True]


    def inspect(self, element):
        # self.window.FindElement('{}{}'.format(repo_idx, combo_branches)).help()
        for i in inspect.getmembers(element):
            # Ignores anything starting with underscore
            # (that is, private and protected attributes)
            if not i[0].startswith('_'):
                # Ignores methods
                if not inspect.ismethod(i[1]):
                    print(i)
