#import sys
#sys.path.append("..") # Adds higher directory to python modules path.

import os
import sys
import inspect

import time

# Add parent dir to system path to instantiate FreeCAD simulation creator gui
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import unittest
from typing import Literal

from ExportOpenEMSDialog import ExportOpenEMSDialog
from PySide import QtGui, QtCore, QtWidgets

class MacroTestBase(unittest.TestCase):
    """
    Loads the macro once per TestCase class and exposes `cls.window`.
    Override `window_title_fragment` if your dialog has a distinctive title.
    """

    appWindow: QtWidgets.QWidget | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.appWindow = ExportOpenEMSDialog()
        cls.appWindow.show()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.appWindow.form.close()
        return

    def getCategoryItem(self, name: Literal["LumpedPart", "Probe", "Port", "Grid", "Excitation", "Material"]) -> QtWidgets.QTreeWidgetItem:
        """
        Return category item from right assignement QTreeWidget, it's top level category as Material or Excitation, ...
        :param name:
        :return:
        """
        categoryItem = self.appWindow.form.objectAssignmentRightTreeWidget.findItems(name, QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)[0]
        return categoryItem

class TestWindowBasics(MacroTestBase):
    """The main window opens and has a sensible title."""

    def test_window_visible(self):
        self.assertIsNotNone(self.appWindow, "Main window should be visible")
        self.assertTrue(self.appWindow.form.isVisible(), "Window should be visible")

class TestMaterialCategory(MacroTestBase):

    def test_material_checkDefaultMaterial(self):
        materialCategoryItem = self.getCategoryItem("Material")
        self.assertEqual(materialCategoryItem.child(0).text(0), "PEC")

    def test_material_addNew(self):
        materialCategoryItem = self.getCategoryItem("Material")

        self.appWindow.form.objectAssignmentRightTreeWidget.setCurrentItem(materialCategoryItem)
        materialCategoryItem.setExpanded(True)
        self.assertEqual(materialCategoryItem.childCount(), 1)

        #add first material
        self.appWindow.form.materialSettingsNameInput.setText("auto material 1")
        self.appWindow.form.materialMetalRadioButton.toggle()
        self.appWindow.form.materialSettingsAddButton.clicked.emit()
        self.assertEqual(materialCategoryItem.childCount(), 2)
        time.sleep(1)

        #add second material
        self.appWindow.form.materialSettingsNameInput.setText("auto material 2")
        self.appWindow.form.materialMetalRadioButton.toggle()
        self.appWindow.form.materialSettingsAddButton.clicked.emit()
        self.assertEqual(materialCategoryItem.childCount(), 3)
        time.sleep(1)

        #add third material
        self.appWindow.form.materialSettingsNameInput.setText("auto material 3")
        self.appWindow.form.materialMetalRadioButton.toggle()
        self.appWindow.form.materialSettingsAddButton.clicked.emit()
        self.assertEqual(materialCategoryItem.childCount(), 4)
        time.sleep(1)

    def test_material_addItemToMaterial(self):
        assert self.appWindow.form.objectAssignmentLeftTreeWidget.topLevelItemCount() >= 2

        # select item in left widget, these objects will be assigned to material
        leftItems = []
        leftItems.append(self.appWindow.form.objectAssignmentLeftTreeWidget.topLevelItem(0))
        leftItems.append(self.appWindow.form.objectAssignmentLeftTreeWidget.topLevelItem(1))
        [item.setSelected(True) for item in leftItems]

        materialCategoryItem = self.getCategoryItem("Material")
        materialCategoryItem.setExpanded(True)

        # select PEC material
        materialItemPEC = materialCategoryItem.child(0)
        self.appWindow.form.objectAssignmentRightTreeWidget.setCurrentItem(materialItemPEC)

        # click on move right button to assign objects to material
        self.appWindow.form.moveRightButton.click()
        time.sleep(1)

        #
        #   Test checking if everything was assigned to material
        #       - check selected items names from objects with assigned objects to material 'PEC'
        #
        assert materialItemPEC.childCount() == 2
        for k in range(materialItemPEC.childCount()):
            assert materialItemPEC.child(k).text(0) == leftItems[k].text(0)
            time.sleep(1)

        #
        #   Check priority list if material items were added into it
        #
        self.assertEqual(self.appWindow.form.objectAssignmentPriorityTreeView.topLevelItemCount(), 2)
        leftItems.reverse()
        for k in range(self.appWindow.form.objectAssignmentPriorityTreeView.topLevelItemCount()):
            priorityItem = self.appWindow.form.objectAssignmentPriorityTreeView.topLevelItem(k)
            priorityItemLabel = priorityItem.text(0)
            expectedLabel = f"Material, PEC, {leftItems[k].text(0)}"
            self.assertEqual(expectedLabel, priorityItemLabel)
            time.sleep(1)

#
#   Running all tests
#
if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for case in [
        TestWindowBasics,
        TestMaterialCategory
    ]:
        suite.addTests(loader.loadTestsFromTestCase(case))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
