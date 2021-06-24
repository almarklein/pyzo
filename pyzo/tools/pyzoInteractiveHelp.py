# -*- coding: utf-8 -*-
# Copyright (C) 2016, the Pyzo development team
#
# Pyzo is distributed under the terms of the 2-Clause BSD License.
# The full license can be found in 'license.txt'.


import sys, re
from functools import partial

from pyzo.util.qt import QtCore, QtGui, QtWidgets  # noqa
import pyzo

tool_name = pyzo.translate("pyzoInteractiveHelp", "Interactive help")
tool_summary = pyzo.translate(
    "pyzoInteractiveHelp", "Shows help on an object when using up/down in autocomplete."
)

keywordsHelp = {
    "await": pyzo.translate(
        "pyzoInteractiveHelp",
        "Suspend the execution of coroutine on an awaitable object. Can only be used inside a coroutine function."
    ),
    "else": pyzo.translate(
        "pyzoInteractiveHelp",
        """This keyword can appear as part of an alternative (see: ``if``), a loop (see: ``for``, ``while``) or a ``try`` statement."""
    ),
    "import": pyzo.translate(
        "pyzoInteractiveHelp",
        """Find and load modules or members of modules.

Examples:
```
import foo                 # foo imported and bound locally
import foo.bar.baz         # foo.bar.baz imported, foo bound locally
import foo.bar.baz as fbb  # foo.bar.baz imported and bound as fbb
from foo.bar import baz    # foo.bar.baz imported and bound as baz
from foo import attr       # foo imported and foo.attr bound as attr
from foo import *          # foo imported and all its members bound
                                    # under their respective names
```"""
    ),
    "pass": pyzo.translate(
        "pyzoInteractiveHelp",
        "This is an instruction that does nothing. It is useful in cases where a statement must appear because of syntactic constraints but we have nothing to do."
    ),
    "break": pyzo.translate(
        "pyzoInteractiveHelp",
        """This keyword can only appear in the body of a ``for`` or ``while`` loop. It terminates the loop early, regardless of the loop condition.

See also: ``continue``"""
    ),
    "except": pyzo.translate(
        "pyzoInteractiveHelp",
        "An ``except`` clause can appear as a part of a ``try`` statement."
    ),
    "in": pyzo.translate(
        "pyzoInteractiveHelp",
        """This keyword usually refers to membership of an object in a structure. There are actually two different kinds of ``in``.

In a construct of the form ``for identifier in iterable``, ``in`` is a purely syntactic element that bears no meaning per se. See: ``for``

Outside such constructs, ``in`` is an operator and its precise meaning depends on the type of the first operand."""
    ),
    "raise": pyzo.translate(
        "pyzoInteractiveHelp",
        "The ``raise`` statement is used to raise an Exception. Raising an exception will cause the program to abort, unless the exception is handled by a surrounding ``try``/``except`` statement or ``with`` statement."
    ),
    "class": pyzo.translate(
        "pyzoInteractiveHelp", "This keyword introduces the definition of a class."
    ),
    "finally": pyzo.translate(
        "pyzoInteractiveHelp",
        "An ``finally`` clause can appear as a part of a ``try`` statement."
    ),
    "is": pyzo.translate(
        "pyzoInteractiveHelp",
        """This operator tests for an object’s identity: ``x is y`` is true if and only if ``x`` and ``y`` are the same object.

See also: ``id``"""
    ),
    "return": pyzo.translate(
        "pyzoInteractiveHelp",
        "This keyword can only appear in the definition of a function. It is usually followed by an expression. It means that the execution of the function call terminates here and that the result of the call is the value of the following expression. If ``return`` is not followed by an expression, the result is ``None``."
    ),
    "and": pyzo.translate(
        "pyzoInteractiveHelp",
        """This operator computes the boolean conjunction in a lazy manner. More precisely, the expression ``x and y`` first evaluates ``x``; if ``x`` is false, its value is returned; otherwise, ``y`` is evaluated and the resulting value is returned.

See also: ``or``, ``not``, ``True``, ``False``"""
    ),
    "continue": pyzo.translate(
        "pyzoInteractiveHelp",
        """This keyword can only appear in the body of a ``for`` or ``while`` loop. It terminates the current run of the body early. The loop may still make additional runs of its body if its condition is still true .

See also: ``break``"""
    ),
    "for": pyzo.translate(
        "pyzoInteractiveHelp",
        """The ``for`` statement is used to iterate over the elements of an iterable object:

```
for variable in iterable:
    body
else:       # optional
    suite
```
The expression ``iterable`` is evaluated once; its value should be an iterable object. An iterator is created for the result of that expression. The ``body`` is then executed once for each item provided by the iterator, in the order returned by the iterator: each item in turn is assigned to the ``variable`` and then the ``body`` is executed. When the items are exhausted (which is immediately when the ``iterable`` is empty), the ``suite`` in the ``else`` clause, if present, is executed, and the loop terminates.

A ``break`` statement executed in the first suite terminates the loop without executing the ``else`` clause’s ``suite``. A ``continue`` statement executed in the first suite skips the rest of the ``body`` and continues with the next item, or with the ``else`` clause if there is no next item.

The for-loop makes assignments to the ``variable``. This overwrites all previous assignments to that variable including those made in the ``body`` of the for-loop:
```
for i in range(10):
    print(i)
    i = 5             # this will not affect the for-loop
                      # because i will be overwritten with the next
                      # index in the range
```

The ``for`` keyword can also be part of a generator.

Example:
```
[2*x for x in T]
```
This builds from ``T`` a list where each item was doubled.
"""
    ),
    "lambda": pyzo.translate(
        "pyzoInteractiveHelp",
        """This keyword is used to produce an anonymous function.

Example:
```
lambda x,y,z : (x+y) * z
```"""
    ),
    "try": pyzo.translate(
        "pyzoInteractiveHelp",
        """The ``try`` statement allows to recover when an Exception was raised. It has two main forms.

```
try:
    critical_section
except SomeExceptionType as e:
    suite   # manage exceptions of type SomeExceptionType
else:       # optional
    everything_ok
```
If ``critical_section`` raises an exception of type ``SomeExceptionType``, the whole program will not abort but the ``suite`` will be executed, with ``e`` being bound to the actual exception. Several ``except`` clauses may be specified, each dealing with some kind of exception. If an exception is raised in ``critical_section`` but is not managed by any ``except`` clause, the whole program aborts. If there is an ``else`` clause, its body is executed if the control flow leaves the ``critical_section``, no exception was raised, and no ``return``, ``continue`` or ``break`` statement was executed. Exceptions in the ``else`` clause are not handled by the preceding ``except`` clauses.


```
try:
    critical_section
finally:
    suite
```
If ``critical_section`` raises an exception, the ``suite`` will be executed before aborting the program. The ``suite`` is also executed when no exception is raised. When a ``return``, ``break`` or ``continue`` statement is executed in the ``critical_section``, the ``finally`` clause is also executed ‘on the way out.’ A ``continue`` statement is illegal in the ``finally`` clause.

Both mechanisms can be combined, the ``finally`` clause coming after the last ``except`` clause or after the optional ``else`` clause."""
    ),
    "as": pyzo.translate(
        "pyzoInteractiveHelp",
        "The ``as`` keyword can appear in an ``import`` statement, in an ``except`` clause of a ``try`` statement or in a ``with`` statement."
    ),
    "def": pyzo.translate(
        "pyzoInteractiveHelp", "This keyword introduces the definition of a function."
    ),
    "from": pyzo.translate(
        "pyzoInteractiveHelp",
        "This keyword can appear as a part of an ``import`` or a ``raise``. It has different meanings; see help on those keywords."
    ),
    "nonlocal": pyzo.translate(
        "pyzoInteractiveHelp",
        """This keyword can only appear in the definition of a function. It is followed by identifiers and indicates that those identifier refer variables from the outer scope, not local variables in the function being defined.

See also: ``global``"""
    ),
    "while": pyzo.translate(
        "pyzoInteractiveHelp",
        """The while statement is used for repeated execution as long as an expression is true:

```
while expression:
    body
else:           # optional
    suite
```
This repeatedly tests the ``expression`` and, if it is true, executes the ``body``; if the ``expression`` is false (which may be the first time it is tested) the ``suite`` of the ``else`` clause, if present, is executed and the loop terminates.

A ``break`` statement executed in the ``body`` terminates the loop without executing the ``else`` clause’s ``suite``. A ``continue`` statement executed in the ``body`` skips the rest of the ``body`` and goes back to testing the ``expression``."""
    ),
    "assert": pyzo.translate(
        "pyzoInteractiveHelp",
        "Assert statements are a convenient way to insert debugging assertions into a program."
    ),
    "del": pyzo.translate(
        "pyzoInteractiveHelp",
        """Deletion of a name removes the binding of that name from the local or global namespace. It is also possible to delete an item in a list."""
    ),
    "global": pyzo.translate(
        "pyzoInteractiveHelp",
        """This keyword is followed by identifiers and indicates that those identifiers refer variables from the module scope, not local variables.

See also: ``nonlocal``"""
    ),
    "not": pyzo.translate(
        "pyzoInteractiveHelp",
        """The operator ``not`` returns ``True`` if its argument is false, ``False`` otherwise.

See also: ``and``, ``or``, ``True``, ``False``"""
    ),
    "with": pyzo.translate(
        "pyzoInteractiveHelp",
        """The ``with`` statement is used to wrap the execution of a block with methods defined by a context manager.

Example:
```
with open(filename) as infile:
    header = infile.readline()
    # etc.
```
In this example, the context manager will ensure correct closing of the file upon exiting the ``with`` statement, even if an exception was raised."""
    ),
    "async": pyzo.translate(
        "pyzoInteractiveHelp",
        "This keyword appears as part of the ``async def``, ``async for`` and ``async with`` constructs and allows for writing coroutines."
    ),
    "elif": pyzo.translate(
        "pyzoInteractiveHelp",
        "This keyword can only appear as part of an alternative. See: ``if``"
    ),
    "if": pyzo.translate(
        "pyzoInteractiveHelp",
        """This keyword usually introduces an alternative. It is followed by a conditon and introduces the statement to execute when this condition is true. The alternative can only have one ``if`` clause, at the beginning. It can also comprise one or more ``elif`` clauses and at most one ``else`` clause at the end.

Example:

```
if condition1 :
    doSomething       # when condition1 evaluates to True
elif condition2 :     # optional, may have several such clauses
    doSomeOtherthing  # when condition1 evaluates to False and condition2 to True
else :                # optional
    doAnotherThing    # when all conditions evaluate to False
```


The ``if`` keyword can also appear in a generator.

Example:
```
[x for x in T if x%2==0]
```
This filters ``T`` to keep only its even items."""
    ),
    "or": pyzo.translate(
        "pyzoInteractiveHelp",
        """This operator computes the boolean disjunction in a lazy manner. More precisely, the expression ``x or y`` first evaluates ``x``; if ``x`` is true, its value is returned; otherwise, ``y`` is evaluated and the resulting value is returned.

See also: ``and``, ``not``, ``True``, ``False``"""
    ),
    "yield": pyzo.translate(
        "pyzoInteractiveHelp",
        """The ``yield`` expression is used when defining a generator function or an asynchronous generator function and thus can only be used in the body of a function definition. Using a yield expression in a function’s body causes that function to be a generator, and using it in an ``async def`` function’s body causes that coroutine function to be an asynchronous generator."""
    ),
}

operators = [
    "+",
    "-",
    "*",
    "**",
    "/",
    "//",
    "%",
    "@",
    "<<",
    ">>",
    "&",
    "|",
    "^",
    "~",
    "<",
    ">",
    "<=",
    ">=",
    "==",
    "!=",
]
operatorsHelp = pyzo.translate(
    "pyzoInteractiveHelp",
    "No help is available for operators because they are ambiguous: their meaning depend on the type of the first operand."
)


#
htmlWrap = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN"
"http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head>
<style type="text/css">
pre, code {{background-color: #F2F2F2;}}
</style>
</head>
<body style=" font-family:'Sans Serif'; font-size:{}pt; font-weight:400; font-style:normal;">
{}
</body>
</html>
"""

# Define title text (font-size percentage does not seem to work sadly.)
def get_title_text(objectName, h_class="", h_repr=""):
    title_text = "<p style='background-color:#def;'>"
    if h_class == "~python_keyword~":
        title_text += "<b>Keyword:</b> {}".format(objectName)
    elif h_class == "~python_operator~":
        title_text += "<b>Operator:</b> {}".format(objectName)
    elif h_class == "":
        title_text += "<b>Unknown construct:</b> {}".format(objectName)
    else:
        title_text += "<b>Object:</b> {}".format(objectName)
        title_text += ", <b>class:</b> {}".format(h_class)
        if h_repr:
            if len(h_repr) > 40:
                h_repr = h_repr[:37] + "..."
            title_text += ", <b>repr:</b> {}".format(h_repr)

    # Finish
    title_text += "</p>\n"
    return title_text


initText = pyzo.translate(
    "pyzoInteractiveHelp",
    """
Help information is queried from the current shell
when moving up/down in the autocompletion list
and when double clicking on a name.
"""
)


class PyzoInteractiveHelpHistoryMenu(QtWidgets.QMenu):
    def __init__(self, title, parent, forward):
        super().__init__(title, parent)
        self._forward = forward
        self.aboutToShow.connect(self.populate)

    def populate(self):
        self.clear()
        if self._forward:
            indices = range(self.parent()._histindex + 1, len(self.parent()._history))
        else:
            indices = range(self.parent()._histindex - 1, -1, -1)
        for i in indices:
            action = self.addAction(self.parent()._history[i])
            action.triggered.connect(partial(self.doAction, i=i))

    def doAction(self, i):
        self.parent()._histindex = i
        self.parent().setObjectName(self.parent().currentHist())


class PyzoInteractiveHelp(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        # Create text field, checkbox, and button
        self._text = QtWidgets.QLineEdit(self)
        self._printBut = QtWidgets.QPushButton("Print", self)

        style = QtWidgets.qApp.style()

        self._backBut = QtWidgets.QToolButton(self)
        self._backBut.setIcon(style.standardIcon(style.SP_ArrowLeft))
        self._backBut.setIconSize(QtCore.QSize(16, 16))
        self._backBut.setPopupMode(self._backBut.DelayedPopup)
        self._backBut.setMenu(
            PyzoInteractiveHelpHistoryMenu("Backward menu", self, False)
        )

        self._forwBut = QtWidgets.QToolButton(self)
        self._forwBut.setIcon(style.standardIcon(style.SP_ArrowRight))
        self._forwBut.setIconSize(QtCore.QSize(16, 16))
        self._forwBut.setPopupMode(self._forwBut.DelayedPopup)
        self._forwBut.setMenu(
            PyzoInteractiveHelpHistoryMenu("Forward menu", self, True)
        )

        # Create options button
        self._options = QtWidgets.QToolButton(self)
        self._options.setIcon(pyzo.icons.wrench)
        self._options.setIconSize(QtCore.QSize(16, 16))
        self._options.setPopupMode(self._options.InstantPopup)
        self._options.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Create options menu
        self._options._menu = QtWidgets.QMenu()
        self._options.setMenu(self._options._menu)

        # Create browser
        self._browser = QtWidgets.QTextBrowser(self)
        self._browser_text = initText
        self._browser.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._browser.customContextMenuRequested.connect(self.showMenu)

        # Create two sizers
        self._sizer1 = QtWidgets.QVBoxLayout(self)
        self._sizer2 = QtWidgets.QHBoxLayout()

        # Put the elements together
        self._sizer2.addWidget(self._backBut, 1)
        self._sizer2.addWidget(self._forwBut, 2)
        self._sizer2.addWidget(self._text, 4)
        self._sizer2.addWidget(self._printBut, 0)
        self._sizer2.addWidget(self._options, 3)
        #
        self._sizer1.addLayout(self._sizer2, 0)
        self._sizer1.addWidget(self._browser, 1)
        #
        self._sizer1.setSpacing(2)
        # set margins
        margin = pyzo.config.view.widgetMargin
        self._sizer1.setContentsMargins(margin, margin, margin, margin)

        self.setLayout(self._sizer1)

        # Set config
        toolId = self.__class__.__name__.lower()
        self._config = config = pyzo.config.tools[toolId]
        #
        if not hasattr(config, "smartNewlines"):
            config.smartNewlines = True
        if not hasattr(config, "fontSize"):
            if sys.platform == "darwin":
                config.fontSize = 12
            else:
                config.fontSize = 10

        # Create callbacks
        self._text.returnPressed.connect(self.queryDoc)
        self._printBut.clicked.connect(self.printDoc)
        self._backBut.clicked.connect(self.goBack)
        self._forwBut.clicked.connect(self.goForward)
        #
        self._options.pressed.connect(self.onOptionsPress)
        self._options._menu.triggered.connect(self.onOptionMenuTiggered)

        # Start
        self._history = []
        self._histindex = 0
        self.setText()  # Set default text
        self.onOptionsPress()  # Fill menu

    def showMenu(self, pos):
        menu = self._browser.createStandardContextMenu()
        help = QtWidgets.QAction(
            pyzo.icons.help, pyzo.translate("pyzoInteractiveHelp", "Help on this"), menu
        )
        help.triggered.connect(partial(self.helpOnThis, pos=pos))
        menu.insertAction(menu.actions()[0], help)
        menu.exec(self.mapToGlobal(pos))

    def helpOnThis(self, pos):
        name = self._browser.textCursor().selectedText().strip()
        if name == "":
            cursor = self._browser.cursorForPosition(pos)
            cursor.select(cursor.WordUnderCursor)
            name = cursor.selectedText()
        if name != "":
            self.setObjectName(name, True)

    def onOptionsPress(self):
        """Create the menu for the button, Do each time to make sure
        the checks are right."""

        # Get menu
        menu = self._options._menu
        menu.clear()

        # Add smart format option
        action = menu.addAction(pyzo.translate("pyzoInteractiveHelp", "Smart format"))
        action._what = "smart"
        action.setCheckable(True)
        action.setChecked(bool(self._config.smartNewlines))

        # Add delimiter
        menu.addSeparator()

        # Add font size options
        currentSize = self._config.fontSize
        for i in range(8, 15):
            action = menu.addAction(
                pyzo.translate("pyzoInteractiveHelp", "Font size: %i") % i
            )
            action._what = "font-size: %ipx" % i
            action.setCheckable(True)
            action.setChecked(i == currentSize)

    def onOptionMenuTiggered(self, action):
        """  The user decides what to show in the structure. """

        # Get text
        text = action._what.lower()

        if "smart" in text:
            # Swap value
            current = bool(self._config.smartNewlines)
            self._config.smartNewlines = not current
            # Update
            self.queryDoc()

        elif "size" in text:
            # Get font size
            size = int(text.split(":", 1)[1][:-2])
            # Update
            self._config.fontSize = size
            # Update
            self.setText()

    def setText(self, text=None):

        # (Re)store text
        if text is None:
            text = self._browser_text
        else:
            self._browser_text = text

        # Set text with html header
        size = self._config.fontSize
        self._browser.setHtml(htmlWrap.format(size, text))

    def setObjectName(self, name, addToHist=False):
        """Set the object name programatically
        and query documentation for it."""
        self._text.setText(name)
        self.queryDoc(addToHist)

    def helpFromCompletion(self, name, addToHist=False):
        self.setObjectName(name, addToHist)

    def currentHist(self):
        try:
            return self._history[self._histindex]
        except Exception:
            return None

    def addToHist(self, name):
        if name == self.currentHist():
            return
        self._history = self._history[: self._histindex + 1]
        self._history.append(name)
        self._histindex = len(self._history) - 1

    def restoreCurrent(self):
        self.setObjectName(self.currentHist())

    def goBack(self):
        if self._histindex > 0 and self._history != []:
            self._histindex -= 1
            self.setObjectName(self.currentHist())

    def goForward(self):
        if self._histindex < len(self._history) - 1:
            self._histindex += 1
            self.setObjectName(self.currentHist())

    def printDoc(self):
        """ Print the doc for the text in the line edit. """
        # Get name
        name = self._text.text()
        # Tell shell to print doc
        shell = pyzo.shells.getCurrentShell()
        if shell and name:
            if name in operators:
                shell.processLine(
                    'print("""{}""")'.format(
                        "Help on operator: " + name + "\n\n" + operatorsHelp
                    )
                )
            elif name in keywordsHelp:
                shell.processLine(
                    'print("""{}""")'.format(
                        "Help on keyword: " + name + "\n\n" + keywordsHelp[name]
                    )
                )
            else:
                shell.processLine("print({}.__doc__)".format(name))

    def queryDoc(self, addToHistory=True):
        """ Query the doc for the text in the line edit. """
        # Get name
        name = self._text.text()
        if addToHistory:
            self.addToHist(name)
        if name in operators:
            text = name + "\n~python_operator~\n\n\n" + operatorsHelp
            self.displayResponse(text)
        elif name in keywordsHelp:
            text = name + "\n~python_keyword~\n\n\n" + keywordsHelp[name]
            self.displayResponse(text)
        else:
            # Get shell and ask for the documentation
            shell = pyzo.shells.getCurrentShell()
            if shell and name:
                future = shell._request.doc(name)
                future.add_done_callback(self.queryDoc_response)
            elif not name:
                self.setText(initText)

    def queryDoc_response(self, future):
        """ Process the response from the shell. """

        # Process future
        if future.cancelled():
            # print('Introspect cancelled') # No living kernel
            return
        elif future.exception():
            print("Introspect-queryDoc-exception: ", future.exception())
            return
        else:
            response = future.result()
            if not response:
                return
            self.displayResponse(response)

    def displayResponse(self, response):
        try:
            # Get parts
            parts = response.split("\n")
            objectName, h_class, h_fun, h_repr = tuple(parts[:4])
            h_text = "\n".join(parts[4:])

            # Obtain newlines that we hid for repr
            h_repr.replace("/r", "/n")

            # Make all newlines \n in h_text and strip
            h_text = h_text.replace("\r\n", "\n").replace("\r", "\n")
            h_text = h_text.lstrip()

            # Init text
            text = ""

            # These signs will fool the html
            h_repr = h_repr.replace("<", "&lt;")
            h_repr = h_repr.replace(">", "&gt;")
            h_text = h_text.replace("<", "&lt;")
            h_text = h_text.replace(">", "&gt;")

            if self._config.smartNewlines:

                # Make sure the signature is separated from the rest using at
                # least two newlines
                header = ""
                if True:
                    # Get short version of objectName
                    name = objectName.split(".")[-1]
                    # Is the signature in the docstring?
                    docs = h_text.replace("\n", "|")
                    tmp = re.search("[a-zA-z_\.]*?" + name + "\(.*?\)", docs)
                    if tmp and tmp.span(0)[0] < 5:
                        header = tmp.group(0)
                        h_text = h_text[len(header) :].lstrip(":").lstrip()
                        header = header.replace("|", "")
                        # h_text = header + '\n\n' + h_text
                    elif h_text.startswith(objectName) or h_text.startswith(name):
                        header, sep, docs = h_text.partition("\n")
                        # h_text = header + '\n\n' + docs
                        h_text = docs
                    elif h_fun is not None and h_fun != "":
                        header = h_fun

                # Parse the text as rest/numpy like docstring
                h_text = self.smartFormat(h_text)
                h_text = re.sub("``(.*?)``", r"<code>\1</code>", h_text)
                if header:
                    h_text = "<p style='color:#005;'><b>%s</b></p>\n%s" % (
                        header,
                        h_text,
                    )
                    # h_text = "<b>%s</b><br /><br />\n%s" % (header, h_text)
            else:
                # Make newlines html
                h_text = h_text.replace("\n", "<br />")

            # Compile rich text
            text += get_title_text(objectName, h_class, h_repr)
            if not self._config.smartNewlines and h_fun is not None and h_fun != "":
                text += "<p><b>Signature:</b> {}</p>".format(h_fun)
            text += "{}<br />".format(h_text)

        except Exception:
            try:
                text += get_title_text(objectName, h_class, h_repr)
                if h_fun is not None and h_fun != "":
                    text += "<p><b>Signature:</b> {}</p>".format(h_fun)
                text += h_text
            except Exception:
                text = response

        # Done
        # size = self._config.fontSize
        self.setText(text)

    def smartFormat(self, text):

        # Get lines
        lines = text.splitlines(True)

        # Test minimal indentation
        minIndent = 9999
        for line in lines[1:]:
            line_ = line.lstrip()
            indent = len(line) - len(line_)
            if line_:
                minIndent = min(minIndent, indent)

        # Remove minimal indentation
        lines2 = [lines[0]]
        for line in lines[1:]:
            lines2.append(line[minIndent:])

        # Prepare
        prevLine_ = ""
        prevIndent = 0
        prevWasHeader = False
        inExample = False
        forceNewline = False
        inPre = False

        # Format line by line
        lines3 = []
        for line in lines2:

            # Get indentation
            line_ = line.lstrip()
            if line_ in ("```", "```\n"):
                if inPre:
                    line = "</pre>"
                    inPre = False
                else:
                    line = "<pre>"
                    inPre = True
            elif not inPre:
                indent = len(line) - len(line_)
                # indentPart = line[:indent-minIndent]
                indentPart = line[:indent]

                if not line_:
                    lines3.append("<br />")
                    forceNewline = True
                    continue

                # Indent in html
                line = "&nbsp;" * len(indentPart) + line

                # Determine if we should introduce a newline
                isHeader = False
                if ("---" in line or "===" in line) and indent == prevIndent:
                    # Header
                    lines3[-1] = "<b>" + lines3[-1] + "</b>"
                    line = ""  #'<br /> ' + line
                    isHeader = True
                    inExample = False
                    # Special case, examples
                    if prevLine_.lower().startswith("example"):
                        inExample = True
                    else:
                        inExample = False
                elif " : " in line:
                    tmp = line.split(" : ", 1)
                    line = "<br /><u>" + tmp[0] + "</u> : " + tmp[1]
                elif line_.startswith("* "):
                    line = "<br />&nbsp;&nbsp;&nbsp;&#8226;" + line_[2:]
                elif prevWasHeader or inExample or forceNewline:
                    line = "<br />" + line
                else:
                    if prevLine_:
                        line = " " + line_
                    else:
                        line = line_

                # Force next line to be on a new line if using a colon
                if " : " in line:
                    forceNewline = True
                else:
                    forceNewline = False

                # Prepare for next line
                prevLine_ = line_
                prevIndent = indent
                prevWasHeader = isHeader

            # Done with line
            lines3.append(line)

        # Done formatting
        return "".join(lines3)
