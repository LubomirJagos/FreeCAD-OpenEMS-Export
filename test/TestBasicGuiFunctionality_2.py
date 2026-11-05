import os
import sys
import inspect
import unittest
from typing import Literal

# Add parent dir to system path to instantiate FreeCAD simulation creator gui
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from ExportOpenEMSDialog import ExportOpenEMSDialog
from PySide import QtGui, QtCore, QtWidgets

import time

def wait_for_ui(seconds=1):
    """Non-blocking wait to let FreeCAD render widgets."""
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(int(seconds * 1000), loop.quit)
    loop.exec_()

class MacroTestBase(unittest.TestCase):
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
        categoryItem = self.appWindow.form.objectAssignmentRightTreeWidget.findItems(name, QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)[0]
        return categoryItem

class TestWindowBasics(MacroTestBase):
    def test_window_visible(self):
        self.assertIsNotNone(self.appWindow, "Main window should be visible")
        self.assertTrue(self.appWindow.form.isVisible(), "Window should be visible")

    def test_dialog_opens(self):
        # Use the already active test window instance from setUpClass
        self.assertIsNotNone(self.appWindow)
        self.assertTrue(self.appWindow.form.isVisible())
        wait_for_ui(1.5)

class TestMaterialCategory(MacroTestBase):
    def test_material_checkDefaultMaterial(self):
        materialCategoryItem = self.getCategoryItem("Material")
        self.assertEqual(materialCategoryItem.child(0).text(0), "PEC")

    def test_material_addNew(self):
        materialCategoryItem = self.getCategoryItem("Material")
        self.appWindow.form.objectAssignmentRightTreeWidget.setCurrentItem(materialCategoryItem)
        materialCategoryItem.setExpanded(True)
        self.assertEqual(materialCategoryItem.childCount(), 1)
        wait_for_ui(1)

        for i, name in enumerate(["auto material 1", "auto material 2", "auto material 3"], start=2):
            self.appWindow.form.materialSettingsNameInput.setText(name)
            self.appWindow.form.materialMetalRadioButton.toggle()
            self.appWindow.form.materialSettingsAddButton.clicked.emit()
            self.assertEqual(materialCategoryItem.childCount(), i)
            wait_for_ui(1)

    def test_material_addItemToMaterial(self):
        assert self.appWindow.form.objectAssignmentLeftTreeWidget.topLevelItemCount() >= 2

        leftItems = [
            self.appWindow.form.objectAssignmentLeftTreeWidget.topLevelItem(0),
            self.appWindow.form.objectAssignmentLeftTreeWidget.topLevelItem(1)
        ]
        for item in leftItems:
            item.setSelected(True)

        materialCategoryItem = self.getCategoryItem("Material")
        materialCategoryItem.setExpanded(True)

        materialItemPEC = materialCategoryItem.child(0)
        self.appWindow.form.objectAssignmentRightTreeWidget.setCurrentItem(materialItemPEC)
        self.appWindow.form.moveRightButton.click()
        wait_for_ui(1)

        assert materialItemPEC.childCount() == 2
        for k in range(materialItemPEC.childCount()):
            assert materialItemPEC.child(k).text(0) == leftItems[k].text(0)
            wait_for_ui(1)

        self.assertEqual(self.appWindow.form.objectAssignmentPriorityTreeView.topLevelItemCount(), 2)
        leftItems.reverse()
        for k in range(self.appWindow.form.objectAssignmentPriorityTreeView.topLevelItemCount()):
            priorityItem = self.appWindow.form.objectAssignmentPriorityTreeView.topLevelItem(k)
            priorityItemLabel = priorityItem.text(0)
            expectedLabel = f"Material, PEC, {leftItems[k].text(0)}"
            self.assertEqual(expectedLabel, priorityItemLabel)
            wait_for_ui(1)

# Function wrapper so the CLI loader can explicitly execute the test suite
def run_interactive_tests():
    print("Executing test cases interactively in FreeCAD...")
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Explicitly load test cases from current module context
    suite.addTests(loader.loadTestsFromTestCase(TestWindowBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestMaterialCategory))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"Test suite finished. Success: {result.wasSuccessful()}")

    #
    #   Keep FreeCAD app hanging and open.
    #
    print("Keeping dialog open for inspection...")
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(10000, loop.quit)
    loop.exec_()


    #
    #   This will close whole FreeCAD application.
    #
    # Determine exit code based on test success (0 = success, 1 = failure)
    # exit_code = 0 if result.wasSuccessful() else 1
    #
    # # Cleanly close the main FreeCAD window / application
    # try:
    #     import FreeCADGui
    #     if FreeCADGui.getMainWindow():
    #         FreeCADGui.getMainWindow().close()
    # except Exception:
    #     pass
    #
    # # Forcefully exit the Python interpreter process so FreeCAD shuts down completely
    # sys.exit(exit_code)


if __name__ == '__main__':
    if 'FreeCAD' in sys.modules and FreeCADGui and FreeCADGui.getMainWindow():
        run_interactive_tests()