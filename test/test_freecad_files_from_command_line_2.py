import FreeCAD
import FreeCADGui
import os
import sys
import glob
from PySide import QtCore

# 1. Open project file (same as before)
project_dir = r"C:/Users/ljagos/Documents/openEMS_projects"
fcstd_files = glob.glob(os.path.join(project_dir, "**", "*.FCStd"), recursive=True)

if fcstd_files:
    fcstd_files.sort(key=os.path.getmtime, reverse=True)
    first_file = fcstd_files[0]
    doc = FreeCAD.open(first_file)
    FreeCAD.setActiveDocument(doc.Name)
    FreeCADGui.setActiveDocument(doc.Name)
    print(f"Successfully opened: {first_file}")

# 2. Locate the test macro
macro_name = "TestBasicGuiFunctionality_2.py"
local_test_path = r"C:/Users/ljagos/Documents/openEMS_projects/FreeCAD-OpenEMS-Export/test/" + macro_name

if os.path.exists(local_test_path):
    print(f"Scheduling macro execution via Qt Event Loop: {local_test_path}")

    with open(local_test_path, "r", encoding="utf-8") as macro_file:
        macro_code = macro_file.read()

    macro_globals = {
        '__name__': '__main__',
        '__file__': local_test_path,
        '__builtins__': __builtins__,
    }
    macro_globals.update(globals())

    addon_dir = os.path.dirname(os.path.dirname(local_test_path))
    parent_dir = os.path.dirname(addon_dir)

    # 3. Define a deferred runner function to execute once FreeCAD's UI loop is fully spinning
    def run_tests_deferred():
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(local_test_path))
        sys.path.insert(0, addon_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        try:
            compiled_code = compile(macro_code, local_test_path, 'exec')
            exec(compiled_code, macro_globals)

            # Explicitly trigger the test suite function defined inside the macro
            if 'run_interactive_tests' in macro_globals:
                macro_globals['run_interactive_tests']()

            print("CLI Test macro execution finished.")
        except Exception as e:
            print(f"ERROR during deferred macro execution: {e}")
            import traceback
            traceback.print_exc()

    # Use QTimer to kick off execution 500ms after FreeCAD GUI finishes initializing
    QtCore.QTimer.singleShot(500, run_tests_deferred)

else:
    print(f"Macro not found at path: {local_test_path}")