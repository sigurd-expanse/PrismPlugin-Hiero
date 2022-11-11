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
import subprocess

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

if platform.system() == "Windows":
    if sys.version[0] == "3":
        import winreg as _winreg
    else:
        import _winreg

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class Prism_Hiero_externalAccess_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        if self.core.version.startswith("v2"):
            self.core.registerCallback(
                "prismSettings_saveSettings",
                self.prismSettings_saveSettings,
                plugin=self.plugin,
            )
            self.core.registerCallback(
                "prismSettings_loadSettings",
                self.prismSettings_loadSettings,
                plugin=self.plugin,
            )
            self.core.registerCallback("getPresetScenes", self.getPresetScenes, plugin=self.plugin)

    @err_catcher(name=__name__)
    def prismSettings_loadUI(self, origin, tab):
        origin.chb_nukeStudio = QCheckBox("Use Nuke Studio instead of Hiero")
        tab.layout().addWidget(origin.chb_nukeStudio)

    @err_catcher(name=__name__)
    def prismSettings_saveSettings(self, origin, settings):
        if "hiero" not in settings:
            settings["hiero"] = {}

        settings["hiero"]["usenukestudio"] = origin.chb_nukeStudio.isChecked()

    @err_catcher(name=__name__)
    def prismSettings_loadSettings(self, origin, settings):
        if "hiero" in settings:
            if "usenukestudio" in settings["hiero"]:
                origin.chb_nukeStudio.setChecked(settings["hiero"]["usenukestudio"])



    @err_catcher(name=__name__)
    def getAutobackPath(self, origin, tab):
        autobackpath = ""

        fileStr = "Nuke Script ("
        for i in self.sceneFormats:
            fileStr += "*%s " % i

        fileStr += ")"

        return autobackpath, fileStr

    @err_catcher(name=__name__)
    def customizeExecutable(self, origin, appPath, filepath):
        fileStarted = False
        if self.core.getConfig("hiero", "usenukestudio"):
            if appPath == "":
                if not hasattr(self, "hieroPath"):
                    self.getHieroPath(origin)

                if self.hieroPath is not None and os.path.exists(self.hieroPath):
                    appPath = self.hieroPath
                else:
                    QMessageBox.warning(
                        self.core.messageParent,
                        "Warning",
                        "Nuke executable doesn't exist:\n\n%s" % self.hieroPath,
                    )

            if appPath is not None and appPath != "":
                subprocess.Popen([appPath, "--studio", self.core.fixPath(filepath)])
                fileStarted = True
                #self.plugin.launch_mode = nukestudio
        else:
            if appPath == "":
                if not hasattr(self, "hieroPath"):
                    self.getHieroPath(origin)

                if self.hieroPath is not None and os.path.exists(self.hieroPath):
                    appPath = self.hieroPath
                else:
                    QMessageBox.warning(
                        self.core.messageParent,
                        "Warning",
                        "Nuke executable doesn't exist:\n\n%s" % self.hieroPath,
                    )

            if appPath is not None and appPath != "":
                subprocess.Popen([appPath, "--hiero", self.core.fixPath(filepath)])
                fileStarted = True
                #self.plugin.launch_mode = hiero
                #raise ValueError( "{0}, {1}, {2}".format(appPath, "--hiero", self.core.fixPath(filepath)) )
                #subprocess.Popen([appPath, "--hiero", self.core.fixPath(filepath)])
        return fileStarted

    """
    @err_catcher(name=__name__)
    def customizeExecutable(self, origin, appPath, filepath):
        fileStarted = False
        return fileStarted
    """


    @err_catcher(name=__name__)
    def getHieroPath(self, origin):
        try:
            ext = ".hrox"
            class_root = _winreg.QueryValue(_winreg.HKEY_CLASSES_ROOT, ext)

            with _winreg.OpenKey(
                _winreg.HKEY_CLASSES_ROOT, r"%s\\shell\\open\\command" % class_root
            ) as key:
                command = _winreg.QueryValueEx(key, "")[0].replace(' "--studio"', '')

            command = command.rsplit(" ", 1)[0][1:-1]

            self.hieroPath = command
        except:
            self.hieroPath = None

    @err_catcher(name=__name__)
    def getPresetScenes(self, presetScenes):
        presetDir = os.path.join(self.pluginDirectory, "Presets")
        scenes = self.core.entities.getPresetScenesFromFolder(presetDir)
        presetScenes += scenes
