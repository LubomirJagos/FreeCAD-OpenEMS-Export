import emerge as em

with open("01_emerge_material_catalog.csv", "w") as outFile:
    outFile.write("material;permittivity;permeability;conductivity;loss_tangent\n")
    for name in dir(em.lib):
        obj = getattr(em.lib, name)
        if type(obj) == em.Material:
            outFile.write(f"{name};{obj.er.value};{obj.ur.value};{obj.cond.value};{obj.tand.value}\n")
