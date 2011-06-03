# -*- coding: utf-8 -*-
# Copyright (c) 2010, the IEP development team
#
# IEP is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

""" Module menu

Implements a menu that can be edited very easily. Every menu item is 
represented by a class. Also implements a dialog to change keyboard 
shortcuts.

"""

import os, sys, re, time
import unicodedata

from PyQt4 import QtCore, QtGui

import iep
from compactTabWidget import CompactTabWidget
from iepLogging import print
import webbrowser


class KeyMapper(QtCore.QObject):
    # This class is accessable via iep.keyMapper
    
    # iep.keyMapper.keyMappingChanged is emitted when keybinding are changed
    keyMappingChanged = QtCore.pyqtSignal()
    
    def setShortcut(self, action):
        """
        When an action is created or when keymappings are changed, this method
        is called to set the shortcut of an action based on its menuPath
        (which is the key in iep.config.shortcuts, e.g. shell__clear_screen)
        """
        if action.menuPath in iep.config.shortcuts:
            shortcuts = iep.config.shortcuts[action.menuPath]
            action.setShortcuts(shortcuts.split(','))
            


def unwrapText(text):
    """ Unwrap text to display in message boxes. This just removes all
    newlines. If you want to insert newlines, use \\r."""
    
    # Removes newlines
    text = text.replace('\n', '')
    
    # Remove double/triple/etc spaces
    text = text.lstrip()
    for i in range(10):
        text = text.replace('  ', ' ')
    
    # Convert \\r newlines 
    text = text.replace('\r', '\n')
    
    # Remove spaces after newlines
    text = text.replace('\n ', '\n')
    
    return text

from PyQt4 import QtCore, QtGui

class Menu(QtGui.QMenu):
    def __init__(self, parent = None, name = None):
        QtGui.QMenu.__init__(self, parent)
        
        # Make sure that the menu has a title
        if name:
            self.setTitle(name)
        else:
            raise ValueError
        
        # Action groups within the menu keep track of the selected value
        self._groups = {}
        
        # menuPath is used to bind shortcuts, it is ,e.g. shell__clear_screen
        if hasattr(parent,'menuPath'):
            self.menuPath = parent.menuPath + '__'
        else:
            self.menuPath = '' #This is a top-level menu
        self.menuPath += self._createMenuPathName(name)
        
        self.build()
    
    def _createMenuPathName(self, name):
        """
        Convert a menu title into a menuPath component name
        e.g. Interrupt current shell -> interrupt_current_shell
        """
        # hide anything between brackets
        name = re.sub('\(.*\)', '', name)
        # replace invalid chars
        name = name.replace(' ', '_')
        if name[0] in '0123456789_':
            name = "_" + name
        name = re.sub('[^a-zA-z_0-9]','',name)
        return name.lower()
    def _addAction(self, properties):
        """ call QMenu.addAction, but if properties is a tuple, unpack it """
        # Add the item, which can be anyting that QMenu accepts (strings, icons,
        # menus, etc.)
        if isinstance(properties, tuple):
            return self.addAction(*properties)
        else:
            return self.addAction(properties)        
    
    def build(self):
        """ Add all actions to the menu. To be overridden """
        raise NotImplementedError

    def _connectActionShortcut(self, a):
        # Set the menupath, connect a shortcut to the given action a and connect to the keyMappingChanged signal
        a.menuPath = self.menuPath + '__' + self._createMenuPathName(a.text())
        iep.keyMapper.keyMappingChanged.connect(lambda: iep.keyMapper.setShortcut(a))
        iep.keyMapper.setShortcut(a) 
    
    
    def addItem(self, properties, callback = None, value = None):
        """
        Add an item to the menu. If callback is given and not None,
        connect triggered signal to the callback. If value is None or not
        given, callback is called without parameteres, otherwise it is called
        with value as parameter
        """
        a = self._addAction(properties)
         
        # Connect the menu item to its callback
        if callback:
            if value is not None:
                a.triggered.connect(lambda b, v = value: callback(v))
            else:
                a.triggered.connect(lambda b: callback())
        
        self._connectActionShortcut(a)              
        return a

    def addGroupItem(self, properties, group = None, value = None, callback = None, selected = False):
        """
        Add a 'select-one' option to the menu. Items with equal group value form
        a group. If callback is specified and not None, the callback is called 
        for the new active item, with the value for that item as parameter
        whenever the selection is changed
        """
        a = self._addAction(properties)
        
        a.setCheckable(True)
        a.setChecked(selected)
        
        # Connect the menu item to its callback (toggled is a signal only
        # emitted by checkable actions, and can also be called programmatically,
        # e.g. in QActionGroup)
        if callback:
            def doCallback(b, v):
                if b:
                    callback(v)
            
            a.toggled.connect(lambda b, v = value: doCallback(b, v))
        
        # Add the menu item to a action group
        if group not in self._groups:
            #self._groups contains tuples (actiongroup, dict-of-actions)
            self._groups[group] = (QtGui.QActionGroup(self), {})
        
        actionGroup,actions = self._groups[group]
        actionGroup.addAction(a)
        actions[value]=a
            
        self._connectActionShortcut(a)          
        return a
    
    def addCheckItem(self, properties, callback = None, value = None, selected = False):
        """
        Add a true/false item to the menu. If callback is specified and not 
        None, the callback is called when the item is changed. If value is not
        specified or None, callback is called with the new state as parameter.
        Otherwise, it is called with the new state and value as parameters
        
        """
        a = self._addAction(properties)
        
        a.setCheckable(True)
        a.setChecked(selected)
        
        # Connect the menu item to its callback
        if callback:
            if value is not None:
                a.triggered.connect(lambda b, v = value: callback(b, v))
            else:
                a.triggered.connect(callback)
            
        self._connectActionShortcut(a)          
        return a
    
    def setCheckedOption(self, group, value):
        """ Set the selected value of a group. This will also activate the
        callback function of the item that gets selected """
        actionGroup,actions = self._groups[group]
        if value in actions:
            actions[value].setChecked(True)

class IndentationMenu(Menu):
    def __init__(self,*args,**kwds):
        self._items = []
        Menu.__init__(self,*args,**kwds)
        iep.editors.currentChanged.connect(self.onEditorsCurrentChanged)
    def build(self):
        self._items = [
            self.addGroupItem("Use tabs", "style", False, self.setStyle),
            self.addGroupItem("Use spaces", "style", True, self.setStyle)
            ]
        self.addSeparator()
        self._items += [
            self.addGroupItem("%d spaces" % i, "width", i, self.setWidth)
            for i in range(2,9)
            ]

        # Items are selected and enabled via the onEditorsCurrentChanged slot    
        self.setEnabled(False)
        
    def setEnabled(self, enabled):
        """ Enable or disable all items. If disabling, also uncheck all items """
        for child in self._items:
            child.setEnabled(enabled)
            if not enabled:
                child.setChecked(False)
            
    def onEditorsCurrentChanged(self):
        editor = iep.editors.getCurrentEditor()
        if editor is None:
            self.setEnabled(False) #Disable / uncheck all options
        else:
            self.setEnabled(True)
            self.setCheckedOption("style", editor.indentUsingSpaces())
            self.setCheckedOption("width", editor.indentWidth())
            
    def setWidth(self, width):
        editor = iep.editors.getCurrentEditor()
        if editor is not None:
            editor.setIndentWidth(width)

    def setStyle(self, style):
        editor = iep.editors.getCurrentEditor()
        if editor is not None:
            editor.setIndentUsingSpaces(style)
        
        
class FileMenu(Menu):
    def build(self):
         
        self.addItem("New", iep.editors.newFile)
        self.addItem("Open", iep.editors.openFile)
        self.addItem("Save", iep.editors.saveFile)
        self.addItem("Save as", iep.editors.saveFileAs)
        self.addItem("Save all", iep.editors.saveAllFiles)
        self.addItem("Close", iep.editors.closeFile)
        self.addItem("Close all", iep.editors.closeAllFiles)
        
        self.addSeparator()
        #TODO: style
        self.addMenu(IndentationMenu(self, "Indentation"))
        #TODO: line endings, encoding
        self.addSeparator()
  
        self.addItem("Restart IEP", iep.main.restart)
        self.addItem("Quit IEP", iep.main.close)
        
class EditMenu(Menu):
    def build(self):
        
        self.addItem("Undo", self._editItemCallback, "undo")
        self.addItem("Redo", self._editItemCallback, "redo")
        self.addSeparator()
        self.addItem("Cut", self._editItemCallback, "cut")
        self.addItem("Copy", self._editItemCallback, "copy")
        self.addItem("Paste", self._editItemCallback, "paste")
        self.addItem("Select all", self._editItemCallback, "selectAll")
        self.addSeparator()
        self.addItem("Indent lines", self._editItemCallback, "indentSelection")
        self.addItem("Dedent lines", self._editItemCallback, "dedentSelection")
        self.addSeparator()
        self.addItem("Comment lines", self._editItemCallback, "commentCode")
        self.addItem("Uncomment lines", self._editItemCallback, "uncommentCode")
        self.addSeparator()
        self.addItem("Find or replace", iep.editors._findReplace.startFind)
        self.addItem("Find selection", iep.editors._findReplace.findSelection)
        self.addItem("Find selection backward", iep.editors._findReplace.findSelectionBw)
        self.addItem("Find next", iep.editors._findReplace.findNext)
        self.addItem("Find previous", iep.editors._findReplace.findPrevious)
        

    def _editItemCallback(self, action):
        widget = QtGui.qApp.focusWidget()
        #If the widget has a 'name' attribute, call it
        if hasattr(widget, action):
            getattr(widget, action)()
    
class EdgeColumnMenu(Menu):
    def build(self):
        self.addGroupItem("None", "edge", 0, self.changed, 0)
        for value in range(60,130,10):
            self.addGroupItem(str(value), "edge", value, self.changed)
        
        self.setCheckedOption("edge", iep.config.view.edgeColumn)
        
    def changed(self, value):
        iep.config.view.edgeColumn = value
        for editor in iep.editors:
            editor.setLongLineIndicatorPosition(value)

class QtThemeMenu(Menu):
    def build(self):
        styleNames = list(QtGui.QStyleFactory.keys())
        styleNames.append('Cleanlooks+')
        styleNames.sort()
        #Add all items to the menu and mark the default one
        for styleName in styleNames:
            title = styleName
            if styleName.lower() == iep.defaultQtStyleName.lower():
                title+=" (default)"
            self.addGroupItem(title, "style", styleName.lower(), self.changed)
            
        #Select the one that is default from the iep config
        self.setCheckedOption("style", iep.config.view.qtstyle.lower())
    
    def changed(self, style):
        iep.config.view.qtstyle = style
        iep.main.setQtStyle(style)
            

        
class ViewMenu(Menu):
    def build(self):
        self.addItem("Select shell", self._selectShell)
        self.addItem("Select editor", self._selectEditor)
        self.addItem("Select previous file", iep.editors._tabs.selectPreviousItem)
        self.addSeparator()
        self.addEditorItem("Show whitespace", "showWhitespace")
        self.addEditorItem("Show line endings", "showLineEndings")
        self.addEditorItem("Show indentation guides", "showIndentationGuides")
        self.addSeparator()
        self.addEditorItem("Wrap long lines", "wrap")
        self.addEditorItem("Highlight current line", "highlightCurrentLine")
        self.addSeparator()
        self.addMenu(EdgeColumnMenu(self, "Edge column"))
        #TODO: zooming
        self.addMenu(QtThemeMenu(self, "Qt theme"))


    def addEditorItem(self, name, param):
        """ Create a boolean item that reperesents a property of the editors,
        whose value is stored in iep.config.view.param """
        if hasattr(iep.config.view, param):
            default = getattr(iep.config.view, param)
        else:
            default = True
            
        self.addCheckItem(name, self._configEditor, param, default)
        
            
    def _configEditor(self, state, param):
        """
        Callback for addEditorItem items
        """
        #Store this parameter in the config
        setattr(iep.config.view, param, state)
        #Apply to all editors, translate e.g. showWhitespace to setShowWhitespace
        setter = 'set' + param[0].upper() + param[1:]
        for editor in iep.editors:
            getattr(editor,setter)(state)

    def _selectShell(self):
        shell = iep.shells.getCurrentShell()
        if shell:
            shell.setFocus()
            
    def _selectEditor(self):
        editor = iep.editors.getCurrentEditor()
        if editor:
            editor.setFocus()

class ShellMenu(Menu):
    def __init__(self, *args, **kwds):
        self._shellCreateActions = []
        self._shellActions = []
        Menu.__init__(self, *args, **kwds)
        iep.shells.currentShellChanged.connect(self.onCurrentShellChanged)
        
    def onCurrentShellChanged(self):
        """ Enable/disable shell actions based on wether a shell is available """
        for shellAction in self._shellActions:
            shellAction.setEnabled(bool(iep.shells.getCurrentShell()))
            
    def build(self, isCtxMenu = False):
        """ Create the items for the shells menu """
        self._shellActions = [
            self.addItem('Interrupt current shell', self.shellAction, "interrupt"),
            self.addItem('Terminate current shell', self.shellAction, "terminate"),
            self.addItem('Restart current shell', self.shellAction, "restart"),
            self.addItem('Clear screen', self.shellAction, "clearScreen"),
            ]
        
        if not isCtxMenu:
            self.addSeparator()
            self.addItem('Edit shell configurations...', self.editConfig)
            # Add shell configs
            self.updateShells()    
    
    def updateShells(self):
        """ Remove, then add the items for the creation of each shell """
        for action in self._shellCreateActions:
            self.removeAction(action)
            
        self._shellCreateActions = [
            self.addItem('Create shell %s: (%s)' % (i+1, config.name),
                iep.shells.addShell, config)
            for i, config in enumerate(iep.config.shellConfigs) ] 
           

    def shellAction(self, action):
        """ Call the method specified by 'action' on the current shell """
        shell = iep.shells.getCurrentShell()
        if shell:
            # Call the specified action
            getattr(shell,action)()
            
    def editConfig(self):
        """ Edit, add and remove configurations for the shells. """
        from shellStack import ShellConfigDialog 
        d = ShellConfigDialog()
        d.exec_()
        # Update the shells items in the menu
        self.updateShells()

class ShellContextMenu(ShellMenu):
    def __init__(self, *args, **kwds):
        ShellMenu.__init__(self, *args, **kwds)
    
    def build(self):
        ShellMenu.build(self, isCtxMenu = True)
        
        self.addSeparator()
        self.addItem("Cut", self._editItemCallback, "cut")
        self.addItem("Copy", self._editItemCallback, "copy")
        self.addItem("Paste", self._editItemCallback, "paste")
        self.addItem("Select all", self._editItemCallback, "selectAll")
    
    def _editItemCallback(self, action):
        widget = QtGui.qApp.focusWidget()
        #If the widget has a 'name' attribute, call it
        if hasattr(widget, action):
            getattr(widget, action)()

class RunMenu(Menu):
    def build(self):
        self.addItem('Run selected lines', self.runSelected)
        self.addItem('Run cell', self.runCell)
        #In the runFile calls, the parameter specifies (asFile, mainFile)
        self.addItem('Run file', self.runFile,(False, False))
        self.addItem('Run main file', self.runFile,(False, True))
        self.addSeparator()
        self.addItem('Run file as script', self.runFile, (True, False))
        self.addItem('Run main file as script', self.runFile, (True, True))
        self.addSeparator()
        self.addItem('Help on running code', self.showHelp)

    
    def showHelp(self, value):
        """ Show more information about ways to run code. """
        
        # Get file item
        fileItem = iep.editors.loadFile(os.path.join(iep.iepDir,'tutorial.py'))
        
        # Select line number
        if fileItem:
            linenr = 77
            editor = fileItem._editor
            editor.gotoLine(linenr)
            iep.editors.getCurrentEditor().setFocus()
    
    
    def getShellAndEditor(self, what, mainEditor=False):
        """ Get the shell and editor. Shows a warning dialog when one of
        these is not available.
        """
        # Init empty error message
        msg = ''
        # Get shell
        shell = iep.shells.getCurrentShell()
        if shell is None:
            msg += "No shell to run code in. "
        # Get editor
        if mainEditor:
            editor = iep.editors.getMainEditor()
            if editor is None:
                msg += "The is no main file selected."
        else:
            editor = iep.editors.getCurrentEditor()
            if editor is None:
                msg += "No editor selected."
        # Show error dialog
        if msg:
            m = QtGui.QMessageBox(self)
            m.setWindowTitle("Could not run")
            m.setText("Could not run " + what + ":\n\n" + msg)
            m.setIcon(m.Warning)
            m.exec_()
        # Return
        return shell, editor
        

    def runSelected(self, value):
        """ Run the selected whole lines in the current shell. """
        # Get editor and shell
        shell, editor = self.getShellAndEditor('selected lines')
        if not shell or not editor:
            return
        # Get position to sample between (only sample whole lines)
        screenCursor = editor.textCursor() #Current selection in the editor
        runCursor = editor.textCursor() #The part that should be run
        
        runCursor.setPosition(screenCursor.selectionStart())
        runCursor.movePosition(runCursor.StartOfBlock) #This also moves the anchor
        lineNumber = runCursor.blockNumber()
        
        runCursor.setPosition(screenCursor.selectionEnd(),runCursor.KeepAnchor)
        if not runCursor.atBlockStart():
            #If the end of the selection is at the beginning of a block, don't extend it
            runCursor.movePosition(runCursor.EndOfBlock,runCursor.KeepAnchor)
        
        # Sample code 
        code = runCursor.selectedText().replace('\u2029', '\n') 
        # Show the result to user and set back
        editor.setTextCursor(runCursor)
        editor.update() #TODO: this doesn't work yet (at lease Mac OS X)
        editor.repaint()
        time.sleep(0.200)
        editor.setTextCursor(screenCursor)
        # Execute code
        fname = editor.id() # editor._name or editor._filename
        shell.executeCode(code, fname, lineNumber)
    
    def runCell(self, value):
        """ Run the code between two cell separaters ('##'). """
        #TODO: ignore ## in multi-line strings
        
        # Get editor and shell
        shell, editor = self.getShellAndEditor('cell')
        if not shell or not editor:
            return 
        # Get current cell
        screenCursor = editor.textCursor() #Current selection in the editor
        runCursor = editor.textCursor() #The part that should be run
        
        # Move up until the start of document or right after a line starting with ##
        runCursor.movePosition(runCursor.StartOfBlock)
        while True:
            if not runCursor.block().previous().isValid():
                break #Start of document
            if runCursor.block().text().lstrip().startswith('##'):
                # ## line, move to the line following this one
                if not runCursor.block().next().isValid():
                    #The user tried to execute the last line of a file which
                    #started with ##. Do nothing
                    return
                runCursor.movePosition(runCursor.NextBlock)
                break
            runCursor.movePosition(runCursor.PreviousBlock)
        
        #This is the line number of the start
        lineNumber = runCursor.blockNumber()
        
        #Move down until a line before one starting with ## or to end of document
        while True:
            if runCursor.block().text().lstrip().startswith('##'):
                #This line starts with ##, move to the end of the previous one
                runCursor.movePosition(runCursor.Left,runCursor.KeepAnchor)
                break
            if not runCursor.block().next().isValid():
                #Last block of the document, move to the end of the line
                runCursor.movePosition(runCursor.EndOfLine,runCursor.KeepAnchor)
                break
            runCursor.movePosition(runCursor.NextBlock,runCursor.KeepAnchor)
        
        
        # Sample code 
        code = runCursor.selectedText().replace('\u2029', '\n')
        # Show the result to user and set back
        editor.setTextCursor(runCursor)
        editor.update() #TODO: this doesn't work yet (at lease Mac OS X)
        editor.repaint()
        time.sleep(0.200)
        editor.setTextCursor(screenCursor)
        # Execute code
        fname = editor.id() # editor._name or editor._filename
        shell.executeCode(code, fname, lineNumber)
    
    
    def _getCodeOfFile(self, editor):
        # Obtain source code
        text = editor.toPlainText()
        # TODO:?? Show the result to user and set back
        #i1, i2 = editor.getPosition(), editor.getAnchor()
        #editor.setPosition(0); editor.setAnchor(editor.length())
        #editor.update()
        #editor.repaint()
        #time.sleep(0.200)
        #editor.setPosition(i1); editor.setAnchor(i2)
        # Get filename and return 
        fname = editor.id() # editor._name or editor._filename
        return fname, text
    
    
    def runFile(self, runMode, givenEditor = None):
        """ Run a file
         runMode is a tuple (asScript, mainFile)
         """
        asScript, mainFile = runMode
         
        # Get editor and shell
        description = 'main file' if mainFile else 'file'
        if asScript:
            description+= ' (as script)'
        
        shell, editor = self.getShellAndEditor(description, mainFile)
        if givenEditor:
            editor = givenEditor
        if not shell or not editor:
            return        
        
        if asScript:
            # Go
            self._runScript(editor, shell)
        else:
            # Obtain source code and fname
            fname, text = self._getCodeOfFile(editor)
            shell.executeCode(text, fname, -1)
    

    
    
    # todo: pass as code, not filename
    def _runScript(self, editor, shell):
        # Obtain fname and try running
        err = ""
        if editor._filename:
            if iep.editors.saveFile(editor):
                shell.restart(editor._filename)
            else:
                err = "Could not save the file."
        else:
            err = "Can only run scripts that are in the file system."
        # If not success, notify
        if err:
            m = QtGui.QMessageBox(self)
            m.setWindowTitle("Could not run script.")
            m.setText(err)
            m.setIcon(m.Warning)
            m.exec_()



class ToolsMenu(Menu):
    def __init__(self, *args, **kwds):
        self._toolActions = []
        Menu.__init__(self, *args, **kwds)
    def build(self):
        self.addItem('Reload tools', iep.toolManager.reloadTools)
        self.addSeparator()

        iep.toolManager.toolInstanceChange.connect(self.onToolInstanceChange)
    def onToolInstanceChange(self):
        # Remove all exisiting tools from the menu
        for toolAction in self._toolActions:
            self.removeAction(toolAction)
        
        # Add all tools, with checkmarks for those that are active
        self._toolActions = [
            self.addCheckItem(tool.name, tool.menuLauncher, 
                selected = bool(tool.instance))
            for tool in iep.toolManager.getToolInfo()
            ]
            


class HelpMenu(Menu):
    def build(self):
        
        self.addUrlItem("Website", "http://code.google.com/p/iep/")
        self.addUrlItem("Ask a question", "http://groups.google.com/group/iep_")
        self.addUrlItem("Report an issue", "http://code.google.com/p/iep/issues/list")
        self.addSeparator()
        self.addItem("Tutorial", lambda:
            iep.editors.loadFile(os.path.join(iep.iepDir,"tutorial.py")))
        self.addItem("View license", lambda:
            iep.editors.loadFile(os.path.join(iep.iepDir,"license.txt")))
        
        self.addItem("Check for updates") #TODO
        self.addItem("About IEP", lambda: None)
        

    def addUrlItem(self, name, url):
        self.addItem(name, lambda: webbrowser.open(url))
        

def buildMenus(menuBar):
    """
    Build all the menus
    """
    menus = [
        FileMenu(menuBar, "File"),
        EditMenu(menuBar, "Edit"),
        ViewMenu(menuBar, "View"),
        SettingsMenu(menuBar, "Settings"),
        ShellMenu(menuBar, "Shell"),
        RunMenu(menuBar, "Run"),
        ToolsMenu(menuBar, "Tools"),
        HelpMenu(menuBar, "Help")
        ]
    for menu in menus:
        menuBar.addMenu(menu)
    menuBar._menus = menus


BaseMenu=object

class SettingsMenu(Menu):
    def build(self):
        #TODO: auto indent is not linked to config settings
        #TODO: call tips not yet implemented
        self.addBoolSetting('Automatically indent', 'autoIndent',
            lambda state, key: [e.setAutoIndent(state) for e in iep.editors])
        self.addBoolSetting('Enable autocompletion', 'autoComplete')
        self.addBoolSetting('Autocomplete keywords', 'autoComplete_keywords')
        self.addSeparator()
        self.addItem('Edit key mappings...', lambda: KeymappingDialog().exec_())
        self.addItem('Edit syntax styles...', self.editStyles)
        self.addItem('Advanced settings...', self.advancedSettings)
        
    def editStyles(self, value):
        """ Edit the style file. """
        text = """
        The syntax styling can be changed by editing the style
        sheet, which will be opened after you press OK. 
        \r\r
        The changes will be applied as soon as you'll save the file.
        """
        m = QtGui.QMessageBox(self)
        m.setWindowTitle("Edit syntax styling")
        m.setText(unwrapText(text))
        m.setIcon(m.Information)
        m.setStandardButtons(m.Ok | m.Cancel)
        m.setDefaultButton(m.Ok)
        result = m.exec_()
        if result == m.Ok:
            iep.editors.loadFile(os.path.join(iep.appDataDir,'styles.ssdf'))
            
    def advancedSettings(self, value):
        """ How to edit the advanced settings. """
        text = """
        More settings are available via the logger-tool:
        \r\r
        - Advanced settings are stored in the struct "iep.config.advanced".
          Type "print(iep.config.advanced)" to view all advanced settings.\r
        - Call "iep.resetConfig()" to reset all settings.\r
        - Call "iep.resetConfig(True)" to reset all settings and state.\r
        - Call "iep.resetStyles() to reset the style sheet to the default.
        \r\r
        Note that most settings require a restart for the change to
        take effect.
        """
        m = QtGui.QMessageBox(self)
        m.setWindowTitle("Advanced settings")
        m.setText(unwrapText(text))
        m.setIcon(m.Information)
        m.exec_()
    
    def addBoolSetting(self, properties, key, callback = None):
        def _callback(state, key):
            setattr(iep.config.settings, key, state)
            if callback is not None:
                callback(state, key)
                
        self.addCheckItem(properties, 
            _callback, 
            key, 
            getattr(iep.config.settings,key)) #Default value
    


class xSettingsMenu(BaseMenu):
    def fill(self):
        BaseMenu.fill(self)
        addItem = self.addItem
        
        addItem( MI('Automatically indent', self.fun_autoIndent, []) )        
        addItem( MI('Enable call tips', self.fun_callTip, []) )
        addItem( MI('Enable auto completion', self.fun_autoComplete, []) )
        addItem( MI('Autocomplete keywords', self.fun_autoComplete_kw, []) )
        addItem( MI('Autocomplete case sensitive', self.fun_autoComplete_case, []) )
        addItem( MI('Autocomplete select chars', self.fun_autoComplete_fillups, []) )
        addItem( None )
        addItem( MI('Default style', self.fun_defaultStyle, []) )
        addItem( MI('Default indentation width', self.fun_defaultIndentWidth, []) )
        addItem( MI('Default indentation style', self.fun_defaultIndentStyle, []) )
        addItem( MI('Default line endings', self.fun_defaultLineEndings, []) )
        addItem( None )
        addItem( MI('Shell wraps to 80 columns', self.fun_shellWrap80, []) )
        addItem( MI('Shell always fits 80 columns', self.fun_shellFit80, []) )
        addItem( None )
        addItem( MI('Edit key mappings ...', self.fun_keymap) )
        addItem( MI('Edit syntax styles ...', self.fun_editStyles) )
        addItem( MI('Advanced settings ...', self.fun_advancedSettings) )
        #addItem( MI('Save settings now', self.fun_saveSettings) )
        
    
    def fun_defaultStyle(self, value):
        """ The style used for new files. """
        if value is None:
            current = iep.config.settings.defaultStyle
            options = iep.styleManager.getStyleNames()
            options.append(current)
            return options
        else:
            # store
            iep.config.settings.defaultStyle = value
    
    def fun_defaultIndentWidth(self, value):
        """ The indentation used for new files and in the shells. """
        
        if value is None:
            current = iep.config.settings.defaultIndentWidth
            options = [2,3,4,5,6,7,8, current]           
            return ['%d' % i for i in options]
        
        # parse value
        try:
            val = int(value[:2])
        except ValueError:
            val = 4      
        # store
        iep.config.settings.defaultIndentWidth = val
        # Apply to shells
        for shell in iep.shells:
            shell.setIndentWidth(val)
            
    def fun_defaultIndentStyle(self,value):
        """Whether to use tabs or spaces for indentation in the shells and in new files"""
        # get editor
        
        if value is None:
            options = ['Spaces', 'Tabs']        
            return options + [options[0 if iep.config.settings.defaultIndentUsingSpaces else 1]]
        else:
            # parse value
            val = None

            try:
                val = {'Spaces': True, 'Tabs': False}[value]
            except KeyError:
                val = True
            # apply
            iep.config.settings.defaultIndentUsingSpaces = val
            
    def fun_defaultLineEndings(self, value):
        """ The line endings used for new files. """
        if value is None:
            current = iep.config.settings.defaultLineEndings
            return ['LF', 'CR', 'CRLF', current]
        else:
            # store
            iep.config.settings.defaultLineEndings = value
    
    def fun_shellWrap80(self, value):
        """ The shell performs hard wrapping of long lines to 80 columns. """
        if value is None:
            return bool(iep.config.settings.shellWrap80)
        else:
            value = not bool(iep.config.settings.shellWrap80)
            iep.config.settings.shellWrap80 = value
    
    def fun_shellFit80(self, value):
        """ Decrease the shell font size so that at least 80 columns fit. """
        if value is None:
            return bool(iep.config.settings.shellFit80)
        else:
            value = not bool(iep.config.settings.shellFit80)
            iep.config.settings.shellFit80 = value
            for s in iep.getAllScintillas():
                if hasattr(s, 'updateFontSizeToMatch80Columns'):
                    s.updateFontSizeToMatch80Columns()
    

    
    def fun_autoComplete_case(self, value):
        """ Whether the autocompletion is case sensitive or not. """
        if value is None:
            return bool(iep.config.settings.autoComplete_caseSensitive)
        else:
            value = not bool(iep.config.settings.autoComplete_caseSensitive)
            iep.config.settings.autoComplete_caseSensitive = value
            # Apply
            for e in iep.getAllScintillas():
                e.SendScintilla(e.SCI_AUTOCSETIGNORECASE, not value)
    
    def fun_autoComplete_fillups(self, value):
        """ Selected autocomp item is inserted when typing these chars. """
        if value is None:
            # Show options
            options = ['Tab', 'Tab and Enter', 'Tab, Enter and " .(["']
            if '.' in iep.config.settings.autoComplete_fillups:
                options.append( options[2] )
            elif '\n' in iep.config.settings.autoComplete_fillups:
                options.append( options[1] )
            else:
                options.append( options[0] )
            return options
        else:
            # Process selection
            if '.' in value:
                iep.config.settings.autoComplete_fillups = '\n .(['
            elif 'enter' in value.lower():
                iep.config.settings.autoComplete_fillups = '\n'
            else:
                iep.config.settings.autoComplete_fillups = ''
            # Apply
            tmp = iep.config.settings.autoComplete_fillups
            for e in iep.getAllScintillas():                
                e.SendScintilla(e.SCI_AUTOCSETFILLUPS, tmp)
    
    def fun_callTip(self, value):
        """ Show a call tip for functions and methods. """
        if value is None:
            return bool(iep.config.settings.autoCallTip)
        else:
            value = not bool(iep.settings.settings.autoCallTip)
            iep.config.settings.autoCallTip = value
    
    def fun_autoIndent(self, value):
        """ Enable auto-indentation (python style only). """
        if value is None:
            return bool(iep.config.settings.autoIndent)
        else:
            value = not bool(iep.config.settings.autoIndent)
            iep.config.settings.autoIndent = value
    
    def fun_keymap(self, value):
        """ Edit the keymappings for the menu. """
        dialog = KeymappingDialog()
        dialog.exec_()
    


    def fun_saveSettings(self, value):
        """ Iep saves the settings when exiting, but you can also save now. """
        iep.main.saveConfig()
        widget = QtGui.qApp.focusWidget()
        # set focus away and back, if the open file is config.ssdf, 
        # a file-changed message will appear
        iep.editors._findReplace._findText.setFocus()
        widget.setFocus()
    

def expandVersion(version):        
        parts = []
        for ver in version.split('.'):
            try:
                tmp = '%05i' % int(ver)
                parts.append(tmp)
            except ValueError: 
                parts.append(ver)
        return '.'.join(parts)

class xHelpMenu(BaseMenu):

    
    def fun_updates(self, value):
        """ Check whether a newer version of IEP is available. """
        # Get versions available
        import urllib.request, re
        url = "http://code.google.com/p/iep/downloads/list"
        text = str( urllib.request.urlopen(url).read() )
        results = []
        for pattern in ['iep-(.{1,9}?)\.source\.zip' ]:
            results.extend( re.findall(pattern, text) )
        # Select best
        remoteVersion = ''
        for result in results:
            if expandVersion(result) > expandVersion(remoteVersion):
                remoteVersion = result
        if not remoteVersion:
            remoteVersion = '?'
        # Define message
        text = """ 
        Your version of IEP is: {}
        The latest version available is: {}\n        
        """.format(iep.__version__, remoteVersion)
        # Show message box
        m = QtGui.QMessageBox(self)
        m.setWindowTitle("Check for the latest version.")
        if remoteVersion == '?':
            text += "Oops, could not determine the latest version."    
        elif expandVersion(iep.__version__) < expandVersion(remoteVersion):
            text += "Do you want to download the latest version?"    
            m.setStandardButtons(m.Yes | m.Cancel)
            m.setDefaultButton(m.Cancel)
        else:
            text += "Your version is up to date."    
        m.setText(text)
        m.setIcon(m.Information)
        result = m.exec_()
        # Goto webpage if user chose to
        if result == m.Yes:
            import webbrowser
            webbrowser.open("http://code.google.com/p/iep/downloads/list")
    

    
    def fun_about(self, value):
        """ Show the about text for IEP. """
        
        aboutText = """
        <h2>IEP: the Interactive Editor for Python</h2>
        
        <b>Version info</b><br>
        IEP version: <u>{}</u><br>
        Platform: {}<br>
        Python version: {}<br>
        Qt version: {}<br>
        PyQt version: {}<br>
        <br>
        
        <b>IEP directories</b><br>
        IEP source directory: {}<br>
        IEP userdata directory: {}<br>
        <br>
        
        <b>Acknowledgements</b><br>
        IEP is written in Python 3 and uses the Qt4 widget
        toolkit. IEP uses code and concepts that are inspired by 
        IPython, Pype, and Spyder.
        IEP uses a (modified) subset of the silk icon set, 
        by Mark James (http://www.famfamfam.com/lab/icons/silk/).
        <br><br>
        
        <b>License</b><br>
        Copyright (c) 2010, the IEP development team<br>
        IEP is distributed under the terms of the (new) BSD License.<br>
        The full license can be found in 'license.txt'.
        <br><br>
        
        <b>Developers</b><br>
        Almar Klein (almar.klein AT gmail DOT com)<br>
        Rob Reilink<br>
        
        """
        # Insert information texts
        if iep.isFrozen():
            versionText = iep.__version__ + ' (binary)'
        else:
            versionText = iep.__version__ + ' (source)'
        aboutText = aboutText.format(versionText, 
                        sys.platform, sys.version.split(' ')[0],
                        QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR,
                        iep.iepDir, iep.appDataDir)
        
        # Define icon and text
        im = QtGui.QPixmap( os.path.join(iep.iepDir,'icons/iep48.png') )         
        # Show message box
        m = QtGui.QMessageBox(self)
        m.setTextFormat(QtCore.Qt.RichText)
        m.setWindowTitle("About IEP")
        m.setText(unwrapText(aboutText))
        m.setIconPixmap(im)
        m.exec_()
    
    

    
    

def getFullName(action):
    """ Get the full name of the action. 
    This is the key in the iep.config.shortcuts dict
    """
    item = action
    text = action.text()
    if not text:
        text = ''
    while isinstance(item.parent(), QtGui.QMenu):
        item = item.parent()
        try:
            text = item.title() + '__' + text
        except Exception:
            print('error getting name',text, item.title())
    # hide anything between brackets
    text = re.sub('\(.*\)', '', text)
    # replace invalid chars
    text = text.replace(' ', '_')
    if text[0] in '0123456789':
        text = "_"+text
    text = re.sub('[^a-zA-z_0-9]','',text,999)
    return text.lower()


def getShortcut( fullName):
    """ Given the full name or an action, get the shortcut
    from the iep.config.shortcuts dict. A tuple is returned
    representing the two shortcuts. """
    if isinstance(fullName, QtGui.QAction):
        fullName = getFullName(fullName)
    shortcut = '', ''
    if fullName in iep.config.shortcuts:
        shortcut = iep.config.shortcuts[fullName]
        if shortcut.count(','):
            shortcut = tuple(shortcut.split(','))
        else:
            shortcut = shortcut, ''
    return shortcut

## Classes to enable editing the key mappings

def translateShortcutToOSNames(shortcut):
    """
    Translate Qt names to OS names (e.g. Ctrl -> cmd symbol for Mac,
    Meta -> Windows for windows
    """
    
    if sys.platform == 'darwin':
        replace = (('Ctrl+','\u2318'),('Shift+','\u21E7'),
                    ('Alt+','\u2325'),('Meta+','^'))
    else:
        replace = ()
    
    for old, new in replace:
        shortcut = shortcut.replace(old, new)
        
    return shortcut

class KeyMapModel(QtCore.QAbstractItemModel):
    """ The model to view the structure of the menu and the shortcuts
    currently mapped. """
    
    def __init__(self, *args):
        QtCore.QAbstractListModel.__init__(self,*args)
        self._root = None
    
    def setRootMenu(self, menu):
        """ Call this after starting. """
        self._root = menu

    def data(self, index, role):
        if not index.isValid() or role not in [0, 8]:
            return None
        
        # get menu or action item
        item = index.internalPointer()
        
        # get text and shortcuts
        key1, key2 = '', ''
        if isinstance(item, QtGui.QMenu):
            value = item.title()
        else:
            value = item.text()
            if not value:
                value = '-'*10
            elif index.column()>0:
                key1, key2 = '<>','<>'
                shortcuts = getShortcut(item)
                if shortcuts[0]:
                    key1 = shortcuts[0]
                if shortcuts[1]:
                    key2 = shortcuts[1]
        # translate to text for the user
        key1 = translateShortcutToOSNames(key1)
        key2 = translateShortcutToOSNames(key2)
        
        # obtain value
        value = [value,key1,key2][index.column()]
        
        # return
        if role == 0:
            # display role
            return value
        else:
            return None
#             # 8: BackgroundRole
#             brush = QtGui.QBrush(QtGui.QColor(240,255,240))
#             if value and index.column()>0:
#                 return brush
#             else:
#                 return None
            
    
    def rowCount(self, parent):
        if parent.isValid():
            menu = parent.internalPointer()
            return len(menu.actions())
        else:
            return len(self._root.actions())
    
    def columnCount(self, parent):
        return 3
    
    def headerData(self, section, orientation, role):
        if role == 0:# and orientation==1:
            tmp = ['Menu action','Shortcut 1','Shortcut 2']
            return tmp[section]
    
    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        item = index.internalPointer()
        pitem = item.parent()
        if pitem is self._root:
            return QtCore.QModelIndex()
        else:
            L = pitem.parent().actions()
            row = 0
            if pitem in L:
                row = L.index(pitem)
            return self.createIndex(row, 0, pitem)
    
    def hasChildren(self, index):
        # no items have parents (except the root item)
        
        if index.row()<0:
            return True
        else:
            return isinstance(index.internalPointer(), QtGui.QMenu)
    
    def index(self, row, column, parent):
#         if not self.hasIndex(row, column, parent):
#             return QtCore.QModelIndex()
        # establish parent
        if not parent.isValid():
            parentMenu = self._root
        else:
            parentMenu = parent.internalPointer()
        # produce index and make menu if the action represents a menu
        childAction = parentMenu.actions()[row]
        if childAction.menu():
            childAction = childAction.menu()        
        return self.createIndex(row, column, childAction)
        # This is the trick. The internal pointer is the way to establish
        # correspondence between ModelIndex and underlying data.


# Key to string mappings
k = QtCore.Qt
keymap = {k.Key_Enter:'Enter', k.Key_Return:'Return', k.Key_Escape:'Escape', 
    k.Key_Tab:'Tab', k.Key_Backspace:'Backspace', k.Key_Pause:'Pause', 
    k.Key_Backtab: 'Tab', #Backtab is actually shift+tab
    k.Key_F1:'F1', k.Key_F2:'F2', k.Key_F3:'F3', k.Key_F4:'F4', k.Key_F5:'F5',
    k.Key_F6:'F6', k.Key_F7:'F7', k.Key_F8:'F8', k.Key_F9:'F9', 
    k.Key_F10:'F10', k.Key_F11:'F11', k.Key_F12:'F12', k.Key_Space:'Space',
    k.Key_Delete:'Delete', k.Key_Insert:'Insert', k.Key_Home:'Home', 
    k.Key_End:'End', k.Key_PageUp:'PageUp', k.Key_PageDown:'PageDown',
    k.Key_Left:'Left', k.Key_Up:'Up', k.Key_Right:'Right', k.Key_Down:'Down' }


class KeyMapLineEdit(QtGui.QLineEdit):
    """ A modified version of a lineEdit object that catches the key event
    and displays "Ctrl" when control was pressed, and similarly for alt and
    shift, function keys and other keys.
    """
    
    textUpdate = QtCore.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        QtGui.QLineEdit.__init__(self, *args, **kwargs)
        self.clear()

        
        # keep a list of native keys, so that we can capture for example
        # "shift+]". If we would use text(), we can only capture "shift+}"
        # which is not a valid shortcut.
        self._nativeKeys = {}

    # Override setText, text and clear, so as to be able to set shortcuts like
    # Ctrl+A, while the actually displayed value is an OS shortcut (e.g. on Mac
    # Cmd-symbol + A)
    def setText(self, text):
        QtGui.QLineEdit.setText(self, translateShortcutToOSNames(text))
        self._shortcut = text
    def text(self):
        return self._shortcut
    def clear(self):
        QtGui.QLineEdit.setText(self, '<enter key combination here>')
        self._shortcut = ''
            
    def focusInEvent(self, event):
        #self.clear()
        QtGui.QLineEdit.focusInEvent(self, event)
    
    def event(self,event):
        # Override event handler to enable catching the Tab key
        # If the event is a KeyPress or KeyRelease, handle it with
        # self.keyPressEvent or keyReleaseEvent
        if event.type()==event.KeyPress:
            self.keyPressEvent(event)
            return True #Mark as handled
        if event.type()==event.KeyRelease:
            self.keyReleaseEvent(event)
            return True #Mark as handled
        #Default: handle events as usual
        return QtGui.QLineEdit.event(self,event)
        
    def keyPressEvent(self, event):
        # get key codes
        key = event.key()
        nativekey = event.nativeVirtualKey()
        
        # try to get text
        if nativekey < 128 and sys.platform != 'darwin':
            text = chr(nativekey).upper()
        elif key<128:
            text = chr(key).upper()
        else:
            text = ''
        
        # do we know this specic key or this native key?
        if key in keymap:
            text = keymap[key]
        elif nativekey in self._nativeKeys:
            text = self._nativeKeys[nativekey]
        
        # apply!
        if text:
            storeNativeKey, text0 = True, text       
            if QtGui.qApp.keyboardModifiers() & k.AltModifier:
                text  = 'Alt+' + text
            if QtGui.qApp.keyboardModifiers() & k.ShiftModifier:
                text  = 'Shift+' + text
                storeNativeKey = False
            if QtGui.qApp.keyboardModifiers() & k.ControlModifier:
                text  = 'Ctrl+' + text
            if QtGui.qApp.keyboardModifiers() & k.MetaModifier:
                text  = 'Meta+' + text
            self.setText(text)
            if storeNativeKey and nativekey:
                # store native key if shift was not pressed.
                self._nativeKeys[nativekey] = text0
        
        # notify listeners
        self.textUpdate.emit()


class KeyMapEditDialog(QtGui.QDialog):
    """ The prompt that is shown when double clicking 
    a keymap in the tree. 
    It notifies the user when the entered shortcut is already used
    elsewhere and applies the shortcut (removing it elsewhere if
    required) when the apply button is pressed.
    """
    
    def __init__(self, *args):
        QtGui.QDialog.__init__(self, *args)
        
        # set title
        self.setWindowTitle('IEP - Edit shortcut mapping')
        self.setWindowIcon(iep.icon)
        
        # set size
        size = 400,140
        offset = 5
        size2 = size[0], size[1]+offset
        self.resize(*size2)
        self.setMaximumSize(*size2)
        self.setMinimumSize(*size2)
        
        self._label = QtGui.QLabel("", self)
        self._label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self._label.resize(size[0]-20, 80)
        self._label.move(10,2)
        
        self._line = KeyMapLineEdit('', self)
        self._line.resize(size[0]-80, 20)
        self._line.move(10,90)
        
        self._clear = QtGui.QPushButton("Clear", self)
        self._clear.resize(50, 20)
        self._clear.move(size[0]-60,90)
        
        self._apply = QtGui.QPushButton("Apply", self)
        self._apply.resize(50, 20)
        self._apply.move(size[0]-120,120)
        
        self._cancel = QtGui.QPushButton("Cancel", self)
        self._cancel.resize(50, 20)
        self._cancel.move(size[0]-60,120)
        
        # callbacks
        self._line.textUpdate.connect(self.onEdit)
        self._clear.clicked.connect(self.onClear)
        self._apply.clicked.connect(self.onAccept)
        self._cancel.clicked.connect(self.close)
        
        # stuff to fill in later
        self._fullname = ''
        self._intro = ''
        self._isprimary = True
        
    def setFullName(self, fullname, isprimary):
        """ To be called right after initialization to let the user
        know what he's updating, and show the current shortcut for that
        in the line edit. """
        
        # store
        self._isprimary = isprimary
        self._fullname = fullname
        # create intro to show, and store + show it
        tmp = fullname.replace('__',' -> ').replace('_', ' ')
        primSec = ['secondary', 'primary'][int(isprimary)]
        self._intro = "Set the {} shortcut for:\n{}".format(primSec,tmp)
        self._label.setText(self._intro)
        # set initial value
        if fullname in iep.config.shortcuts:
            current = iep.config.shortcuts[fullname]
            if ',' not in current:
                current += ','
            current = current.split(',')
            self._line.setText( current[0] if isprimary else current[1] )
            
        
    def onClear(self):
        self._line.clear()
        self._line.setFocus()
    
    def onEdit(self):
        """ Test if already in use. """
        
        # init
        shortcut = self._line.text()
        if not shortcut:
            self._label.setText(self._intro)
            return
        
        for key in iep.config.shortcuts:
            # get shortcut and test whether it corresponds with what's pressed
            shortcuts = getShortcut(key)
            primSec = ''
            if shortcuts[0].lower() == shortcut.lower():
                primSec = 'primary'
            elif shortcuts[1].lower() == shortcut.lower():
                primSec = 'secondary'
            # if a correspondence, let the user know
            if primSec:
                tmp = "WARNING: combo already in use "
                tmp += "as "+primSec+" shortcut for:\n" 
                tmp += key.replace('__',' -> ').replace('_', ' ')
                self._label.setText(self._intro + '\n\n' + tmp)
                break
        else:
            self._label.setText(self._intro)
    
    
    def onAccept(self):
        shortcut = self._line.text()
        
        # remove shortcut if present elsewhere
        keys = [key for key in iep.config.shortcuts] # copy
        for key in keys:
            # get shortcut, test whether it corresponds with what's pressed
            shortcuts = getShortcut(key)
            tmp = list(shortcuts)
            needUpdate = False
            if shortcuts[0].lower() == shortcut.lower():
                tmp[0] = ''
                needUpdate = True
            if shortcuts[1].lower() == shortcut.lower():
                tmp[1] = ''
                needUpdate = True
            if needUpdate:
                tmp = ','.join(tmp)
                tmp = tmp.replace(' ','')
                if len(tmp)==1:
                    del iep.config.shortcuts[key]
                else:
                    iep.config.shortcuts[key] = tmp
        
        # insert shortcut
        if self._fullname:
            # get current and make list of size two
            if self._fullname in iep.config.shortcuts:
                current = list(getShortcut(self._fullname))
            else:
                current = ['', '']
            # update the list
            current[int(not self._isprimary)] = shortcut
            iep.config.shortcuts[self._fullname] = ','.join(current)
        
        # close
        self.close()
    

class KeymappingDialog(QtGui.QDialog):
    """ The main keymap dialog, it has tabs corresponding with the
    different menus and each tab has a tree representing the structure
    of these menus. The current shortcuts are displayed. 
    On double clicking on an item, the shortcut can be edited. """
    
    def __init__(self, *args):
        QtGui.QDialog.__init__(self, *args)
        
        # set title
        self.setWindowTitle('IEP - Shortcut mappings')
        self.setWindowIcon(iep.icon)
        
        # set size
        size = 600,400
        offset = 0
        size2 = size[0], size[1]+offset
        self.resize(*size2)
        self.setMaximumSize(*size2)
        self.setMinimumSize(*   size2)
        
        self.tab = CompactTabWidget(self, padding=(4,4,6,6))
        self.tab.resize(*size)
        self.tab.move(0,offset)
        self.tab.setMovable(False)
        
        # fill tab
        self._models = []
        self._trees = []
        for menu in iep.main.menuBar()._menus:
            # create treeview and model
            model = KeyMapModel()
            model.setRootMenu(menu)
            tree = QtGui.QTreeView(self.tab) 
            tree.setModel(model)
            # configure treeview
            tree.clicked.connect(self.onClickSelect)
            tree.doubleClicked.connect(self.onDoubleClick)
            tree.setColumnWidth(0,150)
            # append to lists
            self._models.append(model)
            self._trees.append(tree)
            self.tab.addTab(tree, menu.title())
        
        self.tab.currentChanged.connect(self.onTabSelect)

    
    def closeEvent(self, event):
        # update key setting
        iep.keyMapper.keyMappingChanged.emit()
        
        event.accept()
    
    def onTabSelect(self):
        pass
    
    
    def onClickSelect(self, index):
        # should we show a prompt?
        if index.column():
            self.popupItem(index.internalPointer(), index.column())
    
    
    def onDoubleClick(self, index):        
        if not index.column():
            self.popupItem(index.internalPointer())
    
    
    def popupItem(self, item, shortCutId=1):
        """ Popup the dialog to change the shortcut. """
        if isinstance(item, QtGui.QAction) and item.text():
            # create prompt dialog
            dlg = KeyMapEditDialog(self)
            fullname = getFullName(item)
            dlg.setFullName( fullname, shortCutId==1 )
            # show it
            dlg.exec_()
