# -*- coding: utf-8 -*-
#
# Copyright © 2009 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Globals explorer widget"""

import sys

# Debug
STDOUT = sys.stdout
STDERR = sys.stderr

from PyQt4.QtGui import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu,
                         QToolButton)
from PyQt4.QtCore import SIGNAL, Qt

# Local imports
from spyderlib.widgets.externalshell.monitor import (monitor_get_remote_view,
                                    monitor_set_global, monitor_get_global,
                                    monitor_del_global, monitor_copy_global)
from spyderlib.widgets.dicteditor import RemoteDictEditorTableView
from spyderlib.utils.programs import is_module_installed
from spyderlib.utils.qthelpers import (create_toolbutton, add_actions,
                                       create_action)
from spyderlib.config import get_icon
#TODO: remove the following line and make it work anyway
# In fact, this 'CONF' object has nothing to do in package spyderlib.widgets
# which should not contain anything directly related to Spyder's main app
# (including its preferences which are stored in CONF).
# So, one should be able to get rid of this object and set options through
# methods like 'set_options(kw1=..., kw2=..., ...)
from spyderlib.config import CONF


def get_settings():
    """
    Return Globals Browser settings
    according to Spyder's configuration file
    """
    settings = {}
    for name in ('filters', 'itermax', 'exclude_private', 'exclude_upper',
                 'exclude_unsupported', 'excluded_names',
                 'truncate', 'minmax', 'collvalue'):
        settings[name] = CONF.get('external_shell', name)
    return settings


class GlobalsExplorer(QWidget):
    ID = 'external_shell'
    
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        
        self.shell = parent

        # Dict editor:
        truncate = CONF.get(self.ID, 'truncate')
        inplace = CONF.get(self.ID, 'inplace')
        minmax = CONF.get(self.ID, 'minmax')
        collvalue = CONF.get(self.ID, 'collvalue')
        self.editor = RemoteDictEditorTableView(parent, None,
                                        truncate=truncate, inplace=inplace,
                                        minmax=minmax, collvalue=collvalue,
                                        get_value_func=self.get_value,
                                        set_value_func=self.set_value,
                                        new_value_func=self.set_value,
                                        remove_values_func=self.remove_values,
                                        copy_value_func=self.copy_value)
        self.connect(self.editor, SIGNAL('option_changed'), self.option_changed)
        
        # Setup layout
        hlayout = QHBoxLayout()
        vlayout = QVBoxLayout()
        self.setup_toolbar(vlayout)
        hlayout.addWidget(self.editor)
        hlayout.addLayout(vlayout)
        self.setLayout(hlayout)
        hlayout.setContentsMargins(0, 0, 0, 0)

        self.connect(self, SIGNAL('option_changed'), self.option_changed)
        
    def setup_toolbar(self, layout):
        toolbar = []

        refresh_button = create_toolbutton(self, text=self.tr("Refresh"),
                                           icon=get_icon('reload.png'),
                                           triggered=self.refresh_table,
                                           text_beside_icon=False)
        toolbar.append(refresh_button)
        
        exclude_private_action = create_action(self,
                self.tr("Exclude private references"),
                tip=self.tr("Exclude references which name starts"
                            " with an underscore"),
                toggled=lambda state:self.emit(SIGNAL('option_changed'),
                                               'exclude_private', state))
        exclude_private_action.setChecked(CONF.get(self.ID, 'exclude_private'))
        
        exclude_upper_action = create_action(self,
                self.tr("Exclude capitalized references"),
                tip=self.tr("Exclude references which name starts with an "
                            "upper-case character"),
                toggled=lambda state:self.emit(SIGNAL('option_changed'),
                                               'exclude_upper', state))
        exclude_upper_action.setChecked( CONF.get(self.ID, 'exclude_upper') )
        
        exclude_unsupported_action = create_action(self,
                self.tr("Exclude unsupported data types"),
                tip=self.tr("Exclude references to unsupported data types"
                            " (i.e. which won't be handled/saved correctly)"),
                toggled=lambda state:self.emit(SIGNAL('option_changed'),
                                               'exclude_unsupported', state))
        exclude_unsupported_action.setChecked(CONF.get(self.ID,
                                              'exclude_unsupported'))
        
        options_button = create_toolbutton(self, text=self.tr("Options"),
                                           icon=get_icon('tooloptions.png'),
                                           text_beside_icon=False)
        toolbar.append(options_button)
        options_button.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(self)
        editor = self.editor
        actions = [exclude_private_action, exclude_upper_action,
                   exclude_unsupported_action, None, editor.truncate_action,
                   editor.inplace_action, editor.collvalue_action]
        if is_module_installed('numpy'):
            actions.append(editor.minmax_action)
        add_actions(menu, actions)
        options_button.setMenu(menu)

        layout.setAlignment(Qt.AlignTop)
        for widget in toolbar:
            layout.addWidget(widget)

    def option_changed(self, option, value):
        CONF.set(self.ID, option, value)
        self.refresh_table()
        
    def refresh_table(self):
        sock = self.shell.monitor_socket
        if sock is None:
            return
        settings = get_settings()
        self.set_data( monitor_get_remote_view(sock, settings) )
        
    def get_value(self, name):
        return monitor_get_global(self.shell.monitor_socket, name)
        
    def set_value(self, name, value):
        sock = self.shell.monitor_socket
        monitor_set_global(sock, name, value)
        self.refresh_table()
        
    def remove_values(self, names):
        sock = self.shell.monitor_socket
        for name in names:
            monitor_del_global(sock, name)
        self.refresh_table()
        
    def copy_value(self, orig_name, new_name):
        sock = self.shell.monitor_socket
        monitor_copy_global(sock, orig_name, new_name)
        self.refresh_table()
        
    def set_data(self, data):
        self.editor.set_data(data)
        self.editor.adjust_columns()
        
    def collapse(self):
        self.emit(SIGNAL('collapse()'))
        
