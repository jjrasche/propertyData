import inspect
import constants
from dataStructures import Base, Numeric, String, Integer, Date, SQLCoordinate, Currency, Boolean, \
    Parcel, Sale, Tax, TaxDetail, Certificate
import sqlalchemy.types as types
import re
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

engine = None
Session = None
session = None
pendingAdds = None


def resetPending():
    global pendingAdds
    pendingAdds = {
        Parcel: [],
        Sale: [],
        Tax: [],
        TaxDetail: [],
        Certificate: []
    }
resetPending()

def createSession(schema):
    global session
    global Session
    engine = create_engine("mysql://root:gonavy123@localhost/{0}".format(schema))
    Base.metadata.create_all(engine)
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    session = Session()
    return session;


def tryFindElement(expression):
    try:
        return expression()
    except Exception, e:
        #print 'failed to run expression: {0}'.format(inspect.getsourcelines(expression))
        return e.message


def strToDate(str):
    if re.match("\d{2}/\d{2}/\d{4}", str) == None:
        return None
    return datetime.strptime(str, '%m/%d/%Y').date()

from sqlalchemy import inspect as alchemyInspect
def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in alchemyInspect(obj).mapper.column_attrs}

def setValue(dbObject, property, expression):
    val = None
    try:
        val = expression()
        propType = type(getattr(dbObject.__class__, property).property.columns[0].type)
        val = testValidSQLValue(propType, val)
        setattr(dbObject, property, val)
    except AttributeError, e:
        return
        # print 'no {0} found'.format(property)
    except Exception, e:
        print 'failed to run expression:{0}\nvalue:{1}\nerror:{2}\n'\
            .format(inspect.getsourcelines(expression), val, e.message)


def testValidSQLValue(inType, value):
    if(inType == Numeric):
        return float(value.replace(",", ""))
    if(inType == String):
        return unicode(value.encode("utf-8").strip())
    if(inType == Integer):
        value = filter(str.isdigit, str(value.replace(".00","")))
        if len(value) == 0:
            return None
        return int(value)
    if(inType == Date):
        return  strToDate(value)
    if(inType == types.DateTime):
        return  value
    if(inType == Boolean):
        return bool(value)
    if(inType == SQLCoordinate):
        return value
    if(inType == Currency):
        return value
    raise Exception("no mapping for type: {0}".format(inType))


def commitDBObject(obj):
    try:
        session.add(obj)
        session.flush()
        session.commit()
    except IntegrityError, e:
        print "unique error: {0}\nobj: {1}".format(e.message, object_as_dict(obj))
        session.rollback()

def safeCommitDBObject():
    try:
        session.flush()
        session.commit()
    except IntegrityError, e:
        print "unique error: {0}".format(e.message)
        session.rollback()
    finally:
        resetPending()

# performs validation on objects and only saves if validation passes
def safeAddObject(obj):
    if (isValidObject(obj)):
        addToPendingArray(type(obj), obj)
        return session.add(obj)


def addToPendingArray(type, obj):
    pendingAdds[type].append(obj)

def passesCheck(obj, check):
    for item in pendingAdds[type(obj)]:
        if check(item, obj):
            return False
    return True

def isValidObject(obj):
    objType = type(obj)
    if (objType == Parcel):
        check = lambda item, obj: item.parcelNumber == obj.parcelNumber
    if (objType == Sale):
        check = lambda item, obj: item.parcelId == obj.parcelId and item.date == obj.date and item.price == obj.price
    if (objType == Tax):
        check = lambda item, obj: item.parcelId == obj.parcelId and item.season == obj.season and item.year == obj.year
    if (objType == TaxDetail):
        check = lambda item, obj: item.taxId == obj.taxId and item.authority == obj.authority and item.due == obj.due
    if (objType == Certificate):
        check = lambda item, obj: item.parcelId == obj.parcelId and item.number == obj.number and item.issued == obj.issued

    return passesCheck(obj, check)


def getIncompleteParcels():
    return session.query(Parcel).filter(Parcel.lat == -1).all()

def getIncompleteParcel():
    parcel = session.query(Parcel).filter(Parcel.lat == -1).first()
    parcel.lat = -2
    session.commit()
    return parcel

# coordinateBox should be dictionary with entries for north, south, east, and west.
def getParcelsWithinGeographicalBoundaries(coordinateBox):
    return session.query(Parcel)\
            .filter(coordinateBox["south"] <= Parcel.lat,
                    Parcel.lat <= coordinateBox["north"],
                    coordinateBox["west"] <= Parcel.long,
                    Parcel.long <= coordinateBox["east"])\
            .limit(constants.resultsLimit)\
            .all()