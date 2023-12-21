from PySide2 import QtGui, QtCore, QtWidgets
import re
import os
from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r

class GuiHelpers:
    def __init__(self, form, statusBar = None, APP_DIR=""):
        self.APP_DIR = APP_DIR
        self.form = form
        self.statusBar = statusBar

    def displayMessage(self, msgText, forceModal=True):
        if (not forceModal) and (self.statusBar is not None):
            self.statusBar.showMessage(msgText, 5000)
        else:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setText(msgText)
            msgBox.exec()

    #
    #   Display messagebox wit Save/Cancel buttons and after user choice return True/False
    #
    def displayYesNoMessage(self, msgText):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(msgText)
        #msgBox.setInformativeText("Do you want to save your changes?")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Cancel)
        return msgBox.exec() == QtWidgets.QMessageBox.Save

    def initRightColumnTopLevelItems(self):
        # MATERIALS
        topItem = QtWidgets.QTreeWidgetItem(["Material"])
        topItem.setIcon(0, QtGui.QIcon(os.path.join(self.APP_DIR, "img", "material.svg")))
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # EXCITATION
        topItem = QtWidgets.QTreeWidgetItem(["Excitation"])
        topItem.setIcon(0, QtGui.QIcon(os.path.join(self.APP_DIR, "img", "excitation.svg")))
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # GRID
        topItem = QtWidgets.QTreeWidgetItem(["Grid"])
        topItem.setIcon(0, QtGui.QIcon(os.path.join(self.APP_DIR, "img", "grid.svg")))
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # PORTS
        topItem = QtWidgets.QTreeWidgetItem(["Port"])
        topItem.setIcon(0, QtGui.QIcon(os.path.join(self.APP_DIR, "img", "port.svg")))
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # PROBES
        topItem = QtWidgets.QTreeWidgetItem(["Probe"])
        topItem.setIcon(0, QtGui.QIcon(os.path.join(self.APP_DIR, "img", "probe.svg")))
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # LUMPED PART
        topItem = QtWidgets.QTreeWidgetItem(["LumpedPart"])
        topItem.setIcon(0, QtGui.QIcon(os.path.join(self.APP_DIR, "img", "lumpedpart.svg")))
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        return

    # this should erase all items from tree widgets and everything before loading new configuration to everything pass right
    #	tree widget is just important to erase because all items contains userdata items which contains its configuration and whole
    #	gui is generating code based on these information, so when items are erased and new ones created everything is ok
    def deleteAllSettings(self):
        self.form.objectAssignmentRightTreeWidget.clear()  # init right column as at startup to have default structure cleared
        self.initRightColumnTopLevelItems()  # rerecreate default simulation structure

        self.form.objectAssignmentPriorityTreeView.clear()  # delete OBJECT ASSIGNMENTS entries
        self.form.gridSettingsTreeView.clear()  # delete GRID entries
        self.form.materialSettingsTreeView.clear()  # delete MATERIAL entries
        self.form.excitationSettingsTreeView.clear()  # delete EXCITATION entries
        self.form.portSettingsTreeView.clear()  # delete PORT entries
        self.form.probeSettingsTreeView.clear()  # delete PORT entries
        self.form.lumpedPartTreeView.clear()  # delete LUMPED PART entries

        self.form.portNf2ffObjectList.clear()   #clear NF2FF combobox
        return

    def setSimlationParamBC(self, comboBox, strValue):
        index = comboBox.findText(strValue, QtCore.Qt.MatchFixedString)
        if index >= 0:
            comboBox.setCurrentIndex(index)

    def removeAllMeshPriorityItems(self):
        print("START REMOVING MESH PRIORITY WIDGET ITEMS")
        print("ITEM TO REMOVE: " + str(self.form.meshPriorityTreeView.invisibleRootItem().childCount()))

        priorityItemsCount = self.form.meshPriorityTreeView.topLevelItemCount()
        for k in reversed(range(priorityItemsCount)):
            print("REMOVING ITEM " + self.form.meshPriorityTreeView.takeTopLevelItem(k).text(0))
            self.form.meshPriorityTreeView.takeTopLevelItem(k)


    def updateMeshPriorityDisableItems(self):
        itemsCount = self.form.meshPriorityTreeView.topLevelItemCount()
        for k in range(itemsCount):
            priorityItem = self.form.meshPriorityTreeView.topLevelItem(k)
            itemNameFields = priorityItem.text(0).split(',')
            gridParent = self.form.objectAssignmentRightTreeWidget.findItems(itemNameFields[1].strip(),
                                                                             QtCore.Qt.MatchRecursive)
            if len(gridParent) > 0:
                if not _bool(gridParent[0].data(0, QtCore.Qt.UserRole).topPriorityLines):
                    self.form.meshPriorityTreeView.topLevelItem(k).setBackground(0, QtGui.QColor('white'))
                else:
                    self.form.meshPriorityTreeView.topLevelItem(k).setBackground(0, QtGui.QColor('lightgray'))

        """
        # If grid item is set to have priority lines it means it should be highlighted in mesh priority widget
        # to display it is special generated in script for simulation
        if rightItem.data(0, QtCore.Qt.UserRole).topPriorityLines:
            #self.form.meshPriorityTreeView.topLevelItem(0).setFont(0, QtGui.QFont("Courier", weight = QtGui.QFont.Bold))
            self.form.meshPriorityTreeView.topLevelItem(0).setDisabled(True)
        else:
            #self.form.meshPriorityTreeView.topLevelItem(0).setFont(0, QtGui.QFont("Courier", weight = QtGui.QFont.Bold))
            self.form.meshPriorityTreeView.topLevelItem(0).setDisabled(False)
        """


    #
    # Universal function to add items into categories in GUI.
    #
    def addSettingsItemGui(self, settingsItem):
        treeItemName = settingsItem.name
        treeItem = QtWidgets.QTreeWidgetItem([treeItemName])

        itemTypeReg = re.search("(.*)SettingsItem", str(settingsItem.__class__.__name__))
        typeStr = itemTypeReg.group(1)

        treeItem.setIcon(0, QtGui.QIcon(os.path.join(self.APP_DIR, "img",  typeStr.lower()+".svg")))
        treeItem.setData(0, QtCore.Qt.UserRole, settingsItem)

        # add item into excitation list
        treeWidgetRef = {}
        itemChangedRef = {}
        if (typeStr.lower() == "excitation"):
            treeWidgetRef = self.form.excitationSettingsTreeView
        elif (typeStr.lower() == "port"):
            treeWidgetRef = self.form.portSettingsTreeView
        elif (typeStr.lower() == "grid"):
            treeWidgetRef = self.form.gridSettingsTreeView
        elif (typeStr.lower() == "material"):
            treeWidgetRef = self.form.materialSettingsTreeView
        elif (typeStr.lower() == "lumpedpart"):
            treeWidgetRef = self.form.lumpedPartTreeView
        elif (typeStr.lower() == "probe"):
            treeWidgetRef = self.form.probeSettingsTreeView
        else:
            print('cannot assign item ' + typeStr)
            return

        treeWidgetRef.insertTopLevelItem(0, treeItem)
        treeWidgetRef.setCurrentItem(treeWidgetRef.topLevelItem(0))

        # adding excitation also into OBJCET ASSIGNMENT WINDOW
        targetGroup = self.form.objectAssignmentRightTreeWidget.findItems(typeStr, QtCore.Qt.MatchExactly)
        targetGroup[0].addChild(treeItem.clone())

    ###
    #	Removing from Priority List
    ###
    def removePriorityName(self, priorityName):
        print("Removing from objects priority list tree view:" + priorityName)
        priorityItemRemoved = True
        while priorityItemRemoved:
            priorityItemRemoved = False

            # search item in priority list for OBJECTS
            priorityItemsCount = self.form.objectAssignmentPriorityTreeView.topLevelItemCount()
            for k in range(priorityItemsCount):
                priorityItem = self.form.objectAssignmentPriorityTreeView.topLevelItem(k)
                if priorityName in priorityItem.text(0):
                    self.form.objectAssignmentPriorityTreeView.takeTopLevelItem(k)
                    priorityItemRemoved = True
                    break

            # search item also in priority list for MESH
            if not priorityItemRemoved:
                priorityItemsCount = self.form.meshPriorityTreeView.topLevelItemCount()
                for k in range(priorityItemsCount):
                    priorityItem = self.form.meshPriorityTreeView.topLevelItem(k)
                    if priorityName in priorityItem.text(0):
                        self.form.meshPriorityTreeView.takeTopLevelItem(k)
                        priorityItemRemoved = True
                        break

    def portSpecificSettingsTabSetActiveByName(self, tabName):
        """
        Set active tab in Port Settings by providing its name, ie. Waveguide, Microstrip, ...
        :return: None
        """
        for index in range(self.form.portSpecificSettingsTab.count()):
            if tabName == self.form.portSpecificSettingsTab.tabText(index):
                self.form.portSpecificSettingsTab.setCurrentIndex(index)

    def probeSpecificSettingsTabSetActiveByName(self, tabName):
        """
        Set active tab in Probe Settings by providing its name, ie. Probe, DumpBox, ...
        :return: None
        """
        for index in range(self.form.probeSpecificSettingsTab.count()):
            if tabName == self.form.probeSpecificSettingsTab.tabText(index):
                self.form.probeSpecificSettingsTab.setCurrentIndex(index)

    def setComboboxItem(self, controlRef, text, alternativeEquivalentValues = None):
        index = controlRef.findText(text, QtCore.Qt.MatchFixedString)
        if index >= 0:
            controlRef.setCurrentIndex(index)
            print(f"setComboboxItem for {controlRef} to value {text} at index {index}")
        else:
            if (alternativeEquivalentValues != None):
                #
                #   if alternative values are provided trying to find them
                #
                for alternativeValueTuple in alternativeEquivalentValues:
                    if (alternativeValueTuple[0] == text):
                        print(f"WARNING: For {controlRef} instead {text} trying to use alternative equivalent value {alternativeValueTuple[1]}")
                        self.setComboboxItem(controlRef, alternativeValueTuple[1])
                    elif (alternativeValueTuple[1] == text):
                        print(f"WARNING: For {controlRef} instead {text} trying to use alternative equivalent value {alternativeValueTuple[0]}")
                        self.setComboboxItem(controlRef, alternativeValueTuple[0])
                return
            else:
                print(f"WARNING: Cannot set for {controlRef} item {text}, wasn't found in items.")
                return

            print(f"WARNING: Cannot set for {controlRef} item {text}, alternative value was not found.")

    def hasPortSomeObjects(self, portName):
        """
        Check if port category contains some assigned freecad objects
        :param port category name:
        :return: true if category contains some assigned objects
        """
        hasPortSomeObjects = False

        itemWithSameName = self.form.objectAssignmentRightTreeWidget.findItems(portName, QtCore.Qt.MatchFixedString | QtCore.Qt.MatchRecursive)
        for item in itemWithSameName:
            #test if it's under Port category, so look if parent().parent() is None as it's top level item and then if parent is Port item category
            if (item.parent().parent() == None and item.parent().text(0) == "Port"):
                if (item.childCount() > 0):
                    hasPortSomeObjects = True

        return hasPortSomeObjects

    def getGridGroupObjectAssignmentTreeItem(self, groupName):
        gridGroupWidgetItems = self.form.objectAssignmentRightTreeWidget.findItems(
            groupName,
            QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
        )
        gridGroupItem = None
        for item in gridGroupWidgetItems:
            if (item.parent().text(0) == "Grid"):
                gridGroupItem = item

        return gridGroupItem