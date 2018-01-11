from dataStructures import Parcel
from ormMethods import createSession

from gatherParcelDetails_AccessMyGov import gatherDataOnParcels
from identifyParcels import getAllParcelsFromMunicipality
from KMLMethods import writeKMLFile
import sys
reload(sys)
sys.setdefaultencoding('utf-8')



session = None

def init():
    global session
    session = createSession()



# search for new parcels adding a stub in database when one is found
# fill in details for stubbed parcels
init()
getAllParcelsFromMunicipality(session, "384")
# parcels =  session.query(Parcel).filter(Parcel.taxableValue > "1000000").all()
# print len(parcels)
# writeKMLFile(parcels)

parcels = session.query(Parcel).filter(Parcel.parcelNumber == "33-01-01-19-377-027").all()
gatherDataOnParcels(session, None)