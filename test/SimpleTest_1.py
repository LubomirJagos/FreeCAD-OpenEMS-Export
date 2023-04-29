#import sys
#sys.path.append("..") # Adds higher directory to python modules path.

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


from ExportOpenEMSDialog import ExportOpenEMSDialog
from PySide import QtGui, QtCore

if __name__ == '__main__':
    #
    #   Preparation, open application
    #
    appWindow = ExportOpenEMSDialog()
    appWindow.show()

    #
    #   TEST 1
    #
    #[appWindow.form.objectAssignmentLeftTreeWidget.topLevelItem(k).setSelected(True) for k in (3,4,8,9)]

    leftItems = []
    leftItems.append(appWindow.form.objectAssignmentLeftTreeWidget.findItems("top part", QtCore.Qt.MatchExactly)[0])
    leftItems.append(appWindow.form.objectAssignmentLeftTreeWidget.findItems("bottom part", QtCore.Qt.MatchExactly)[0])
    [item.setSelected(True) for item in leftItems]


    materialCategoryItem = appWindow.form.objectAssignmentRightTreeWidget.findItems(
        "Material",
        QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
    )[0]

    appWindow.form.objectAssignmentRightTreeWidget.setCurrentItem(materialCategoryItem)
    materialCategoryItem.setExpanded(True)

    assert 1 == materialCategoryItem.childCount()
    appWindow.form.materialSettingsNameInput.setText("auto material 1")
    appWindow.form.materialMetalRadioButton.toggle()
    appWindow.form.materialSettingsAddButton.clicked.emit()
    assert 2 == materialCategoryItem.childCount()
    appWindow.form.materialSettingsNameInput.setText("auto material 2")
    appWindow.form.materialMetalRadioButton.toggle()
    appWindow.form.materialSettingsAddButton.clicked.emit()
    assert 3 == materialCategoryItem.childCount()
    appWindow.form.materialSettingsNameInput.setText("auto material 3")
    appWindow.form.materialMetalRadioButton.toggle()
    appWindow.form.materialSettingsAddButton.clicked.emit()
    assert 4 == materialCategoryItem.childCount()

    appWindow.form.objectAssignmentRightTreeWidget.setCurrentItem(materialCategoryItem.child(0))
    appWindow.form.moveRightButton.click()

    # rename object in freecad
    obj = [obj for obj in FreeCAD.ActiveDocument.Objects if obj.Label == "top part"][0]
    obj.Label = "top part modified"
    assert "top part modified" == materialCategoryItem.child(0).child(0).text(0)    #check it was renamed in GUI
    obj.Label = "top part"








