from PySide import QtGui, QtCore
import re
from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r

class GuiHelpers:
    def __init__(self, form, statusBar = None):
        self.form = form
        self.statusBar = statusBar

    def displayMessage(self, msgText, forceModal=True):
        if (not forceModal) and (self.statusBar is not None):
            self.statusBar.showMessage(msgText, 5000)
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText(msgText)
            msgBox.exec()

    #
    #   Display messagebox wit Save/Cancel buttons and after user choice return True/False
    #
    def displayYesNoMessage(self, msgText):
        msgBox = QtGui.QMessageBox()
        msgBox.setText(msgText)
        #msgBox.setInformativeText("Do you want to save your changes?")
        msgBox.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Cancel)
        return msgBox.exec() == QtGui.QMessageBox.Save

    def initRightColumnTopLevelItems(self):
        #
        # Default items for each section
        #
        """ NO DEFAULT ITEMS!
        topItem = self.form.objectAssignmentRightTreeWidget.itemAt(0,0)
        defaultMaterialItem = QtGui.QTreeWidgetItem(["Material Default"])
        defaultExcitationItem = QtGui.QTreeWidgetItem(["Excitation Default"])
        defaultGridItem = QtGui.QTreeWidgetItem(["Grid Default"])
        defaultPortItem = QtGui.QTreeWidgetItem(["Port Default"])
        defaultLumpedPartItem = QtGui.QTreeWidgetItem(["LumpedPart Default"])
        """

        #
        # Default items in each subsection have user data FreeCADSttingsItem classes to have just basic information like genereal freecad object
        #
        """ NO DEFAULT ITEMS!
        defaultMaterialItem.setData(0, QtCore.Qt.UserRole, FreeCADSettingsItem("Material Default"))
        defaultExcitationItem.setData(0, QtCore.Qt.UserRole, FreeCADSettingsItem("Excitation Default"))
        defaultGridItem.setData(0, QtCore.Qt.UserRole, FreeCADSettingsItem("Grid Default"))
        defaultPortItem.setData(0, QtCore.Qt.UserRole, FreeCADSettingsItem("Port Default"))
        defaultLumpedPartItem.setData(0, QtCore.Qt.UserRole, FreeCADSettingsItem("LumpedPart Default"))
        """

        # MATERIALS
        topItem = QtGui.QTreeWidgetItem(["Material"])
        topItem.setIcon(0, QtGui.QIcon("./img/material.svg"))
        # topItem.addChildren([defaultMaterialItem])	#NO DEFAULT ITEM
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # LuboJ
        self.MaterialsItem = topItem  # aux item materials item to have some reference here to be sure for future access it

        # EXCITATION
        topItem = QtGui.QTreeWidgetItem(["Excitation"])
        topItem.setIcon(0, QtGui.QIcon("./img/excitation.svg"))
        # topItem.addChildren([defaultExcitationItem])	#NO DEFAULT ITEM
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # GRID
        topItem = QtGui.QTreeWidgetItem(["Grid"])
        topItem.setIcon(0, QtGui.QIcon("./img/grid.svg"))
        # topItem.addChildren([defaultGridItem])	#NO DEFAULT ITEM
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # PORTS
        topItem = QtGui.QTreeWidgetItem(["Port"])
        topItem.setIcon(0, QtGui.QIcon("./img/port.svg"))
        # topItem.addChildren([defaultPortItem])	#NO DEFAULT ITEM
        self.form.objectAssignmentRightTreeWidget.insertTopLevelItem(0, topItem)

        # LUMPED PART
        topItem = QtGui.QTreeWidgetItem(["LumpedPart"])
        topItem.setIcon(0, QtGui.QIcon("./img/lumpedpart.svg"))
        # topItem.addChildren([defaultLumpedPartItem])	#NO DEFAULT ITEM
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
            print("Searching......" + itemNameFields[1])
            gridParent = self.form.objectAssignmentRightTreeWidget.findItems(itemNameFields[1].strip(),
                                                                             QtCore.Qt.MatchRecursive)
            if len(gridParent) > 0:
                print("parent grid found")
                print(gridParent[0].data(0, QtCore.Qt.UserRole).topPriorityLines)
                print(type(gridParent[0].data(0, QtCore.Qt.UserRole).topPriorityLines))
        #	if not gridParent[0].data(0, QtCore.Qt.UserRole).topPriorityLines or gridParent[0].data(0, QtCore.Qt.UserRole).topPriorityLines == 'false':
        #		self.form.meshPriorityTreeView.topLevelItem(k).setDisabled(True)
        #	else:
        #		self.form.meshPriorityTreeView.topLevelItem(k).setDisabled(False)

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
        treeItem = QtGui.QTreeWidgetItem([treeItemName])

        itemTypeReg = re.search("(.*)SettingsItem", str(settingsItem.__class__.__name__))
        typeStr = itemTypeReg.group(1)

        treeItem.setIcon(0, QtGui.QIcon("./img/" + typeStr.lower() + ".svg"))
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
