import FreeCAD
import FreeCADGui
import os
import sys
import glob

# 1. Open the project file
project_dir = r"C:/Users/ljagos/Documents/openEMS_projects"
fcstd_files = glob.glob(os.path.join(project_dir, "**", "*.FCStd"), recursive=True)

if fcstd_files:
    fcstd_files.sort(key=os.path.getmtime, reverse=True)
    first_file = fcstd_files[0]
    doc = FreeCAD.open(first_file)
    FreeCAD.setActiveDocument(doc.Name)
    FreeCADGui.setActiveDocument(doc.Name)
    print(f"Successfully opened: {first_file}")

# 2. Locate and execute the macro with a mocked __file__ context
macro_name = "FreeCAD-OpenEMS-Export.FCMacro"
macro_path = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Macro").GetString("MacroPath")
full_macro_path = os.path.abspath(os.path.join(macro_path, macro_name))

if os.path.exists(full_macro_path):
    print(f"Executing macro: {full_macro_path}")

    with open(full_macro_path, "r", encoding="utf-8") as macro_file:
        macro_code = macro_file.read()

    # Create a custom globals dictionary that includes __file__ so internal path logic succeeds
    macro_globals = globals().copy()
    macro_globals['__file__'] = full_macro_path

    # Temporarily set CWD to the macro's directory just in case
    old_cwd = os.getcwd()
    addon_dir = os.path.dirname(full_macro_path)
    os.chdir(addon_dir)
    sys.path.insert(0, addon_dir)

    try:
        exec(macro_code, macro_globals)
    finally:
        os.chdir(old_cwd)
        if addon_dir in sys.path:
            sys.path.remove(addon_dir)
else:
    print(f"Macro not found at path: {full_macro_path}")