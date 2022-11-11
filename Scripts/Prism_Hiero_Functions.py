# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2020 Richard Frangenberg
#
# Licensed under GNU GPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.
#
####################################################
#
# Modifed by EXPANSE team for internal pipeline usage
#
####################################################

import os
import sys
import platform
import random
import logging

import nuke
import hiero

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher as err_catcher


logger = logging.getLogger(__name__)


class Prism_Hiero_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.isRendering = {}
        self.useLastVersion = False

    @err_catcher(name=__name__)
    def startup(self, origin):
        if self.core.uiAvailable:
            origin.timer.stop()

            for obj in QApplication.topLevelWidgets():
                if (
                    obj.inherits("QMainWindow")
                    and obj.metaObject().className() == "Foundry::UI::DockMainWindow"
                ):
                    nukeQtParent = obj
                    break
            else:
                nukeQtParent = QWidget()

            origin.messageParent = QWidget()
            origin.messageParent.setParent(nukeQtParent, Qt.Window)
            if platform.system() != "Windows" and self.core.useOnTop:
                origin.messageParent.setWindowFlags(
                    origin.messageParent.windowFlags() ^ Qt.WindowStaysOnTopHint
                )

        self.addPluginPaths()
        if self.core.uiAvailable:
            print("adding menus!")
            self.addMenus()
        else:
            print("skipping menus!")

        self.addCallbacks()
        hiero.core.TaskPresetBase.addUserResolveEntries = self.global_addRenderPaths

    @err_catcher(name=__name__)
    def addPluginPaths(self):
        gdir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "Gizmos")
        nuke.pluginAddPath(gdir)

    @err_catcher(name=__name__)
    def addMenus(self):
        global prism_menu
        global prism_menuItems
        prism_menuItems = []
        self.removeMenu()
        print('\n*** Loaded PRISM Toolbar ***\n')
        menuBar = hiero.ui.menuBar()
        prism_menu = menuBar.addMenu("Prism")
        prism_menuItems.append( prism_menu.addAction("Project Browser", self.core.projectBrowser) )
        prism_menuItems.append( prism_menu.addAction("Save Version", self.core.saveScene) )
        prism_menuItems.append( prism_menu.addAction("Save Comment", self.core.saveWithComment) )
        prism_menuItems.append( prism_menu.addAction("Settings", self.core.prismSettings) )
        return

    @err_catcher(name=__name__)
    def removeMenu(self):
        menuBar = hiero.ui.menuBar()
        for child in menuBar.children():
            try:
                menuTitle = child.title()
                if menuTitle == 'Prism':
                    print('\n*** Removing Old Prism Toolbar ***\n')
                    child.deleteLater()
            except:
                pass

    @err_catcher(name=__name__)
    def global_addRenderPaths(self, resolver):
        renderProductBasePaths = self.core.paths.getRenderProductBasePaths()
        for basePath in renderProductBasePaths:
            resolver.addResolver("{{prism_{0}}}".format(basePath), "Prism {0} location: {1}".format(basePath, renderProductBasePaths[basePath]), renderProductBasePaths[basePath] )


    @err_catcher(name=__name__)
    def addCallbacks(self):
        nuke.addOnScriptLoad(self.core.sceneOpen)

    @err_catcher(name=__name__)
    def onProjectChanged(self, origin):
        pass

    @err_catcher(name=__name__)
    def sceneOpen(self, origin):
        if hasattr(origin, "asThread") and origin.asThread.isRunning():
            origin.startasThread()

    @err_catcher(name=__name__)
    def executeScript(self, origin, code, preventError=False):
        if preventError:
            try:
                return eval(code)
            except Exception as e:
                msg = "\npython code:\n%s" % code
                exec("raise type(e), type(e)(e.message + msg), sys.exc_info()[2]")
        else:
            return eval(code)

    @err_catcher(name=__name__)
    def getCurrentFileName(self, origin, path=True):
        try:
            #currentFileName = nuke.root().name()
            activeSequence = hiero.ui.activeSequence()
            currentFileName = activeSequence.project().path()
        except:
            currentFileName = ""

        if currentFileName == "Root":
            currentFileName = ""

        return currentFileName

    @err_catcher(name=__name__)
    def getSceneExtension(self, origin):
        return self.sceneFormats[0]

    @err_catcher(name=__name__)
    def saveScene(self, origin, filepath, details={}):
        try:
            sequence = hiero.ui.activeSequence()
            currentProject = sequence.project()
            return currentProject.saveAs(filepath)
        except:
            return ""

    @err_catcher(name=__name__)
    def getImportPaths(self, origin):
        return False

    @err_catcher(name=__name__)
    def getAppVersion(self, origin):
        return nuke.NUKE_VERSION_STRING

    @err_catcher(name=__name__)
    def onProjectBrowserStartup(self, origin):
        origin.actionStateManager.setEnabled(False)

    @err_catcher(name=__name__)
    def openScene(self, origin, filepath, force=False):
        if os.path.splitext(filepath)[1] not in self.sceneFormats:
            return False

        openedProjects = []
        for project in hiero.core.projects():
            openedProjects.append(project.path())
        if filepath not in openedProjects:
            try:
                #nuke.scriptOpen(filepath)
                hiero.core.openProject(filepath)
                return True
            except:
                pass
        else:
            nuke_launchmode = "Nuke Studio"
            if nuke.env["hiero"]:
                nuke_launchmode = "Hiero"
            QMessageBox.warning(
                self.core.messageParent,
                "Notice",
                "This scene is already open in {0}:\n\n{1}".format( nuke_launchmode, filepath),
            )

        return False

    @err_catcher(name=__name__)
    def correctExt(self, origin, lfilepath):
        return lfilepath

    @err_catcher(name=__name__)
    def setSaveColor(self, origin, btn):
        btn.setPalette(origin.savedPalette)

    @err_catcher(name=__name__)
    def clearSaveColor(self, origin, btn):
        btn.setPalette(origin.oldPalette)

    @err_catcher(name=__name__)
    def setProject_loading(self, origin):
        pass

    @err_catcher(name=__name__)
    def onPrismSettingsOpen(self, origin):
        pass

    @err_catcher(name=__name__)
    def createProject_startup(self, origin):
        pass

    @err_catcher(name=__name__)
    def editShot_startup(self, origin):
        pass

    @err_catcher(name=__name__)
    def shotgunPublish_startup(self, origin):
        pass

    @err_catcher(name=__name__)
    def postSaveScene(self, origin, filepath, versionUp, comment, isPublish, details):
        """
        origin:     PrismCore instance
        filepath:   The filepath of the scenefile, which was saved
        versionUp:  (bool) True if this save increments the version of that scenefile
        comment:    The string, which is used as the comment for the scenefile. Empty string if no comment was given.
        isPublish:  (bool) True if this save was triggered by a publish
        """
        pass
