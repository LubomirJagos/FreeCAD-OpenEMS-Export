import FreeCAD as App

# evtHandler : helper class that manages adding, removing and calls to a list of event handlers.
class evtHandler(object):
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, Ehandler):
        self.__handlers.append(Ehandler)
        return self

    def __isub__(self, Ehandler):
        self.__handlers.remove(Ehandler)
        return self

    def __call__(self, *args, **keywargs):
        for h in self.__handlers:
            h(*args, **keywargs)

# FreeCADDocObserver : implements a sub-set of the FreeCAD documentObserver to provide event handling. For a full list,
# see https://github.com/FreeCAD/FreeCAD/blob/42a71ccbbd2937d270e46c1688b9411a7f82f13d/src/Gui/DocumentObserverPython.h#L37
# and https://github.com/FreeCAD/FreeCAD/blob/8efe30c8a90305d688fa164048941be1fd474918/src/Mod/Test/Document.py#L1619 .
class FreeCADDocObserver():
    def __init__(self):
        self.documentCreated = evtHandler()
        self.documentActivated = evtHandler()
        self.documentDeleted = evtHandler()
        self.objectRecomputed = evtHandler()
        self.objectCreated = evtHandler()
        self.objectChanged = evtHandler()
        self.objectDeleted = evtHandler()

    def startObservation(self):
        # set up document observer
        App.addDocumentObserver(self)

    # print("Observation started.")

    def endObservation(self):
        App.removeDocumentObserver(self)

    # print("Observation terminated.")

    def slotCreatedDocument(self, doc):
        # print ("Create document")
        self.documentCreated(doc)

    def slotActivateDocument(self, doc):
        # print ("Activate document")
        self.documentActivated(doc)

    def slotDeletedDocument(self, doc):
        # print ("Delete document")
        self.documentDeleted(doc)

    def slotRecomputedObject(self, obj):
        #print("recomputation triggered")
        self.objectRecomputed(obj)

    def slotCreatedObject(self, obj):
        #print("A new object was added")
        self.objectCreated(obj)

    def slotChangedObject(self, obj, prop):
        #print("you have changed an object: " + repr(obj))
        self.objectChanged(obj, prop)

    def slotDeletedObject(self, obj):
        #print("you have queued an object for deletion: " + repr(obj))
        self.objectDeleted(obj)


