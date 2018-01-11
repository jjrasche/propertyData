from sqlalchemy import Column, ForeignKey, Integer, String, Date, Numeric, Boolean, Enum, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from decimal import Decimal
import sqlalchemy.types as types
from sqlalchemy import UniqueConstraint
import re


Base = declarative_base()

def typeMatch(obj, compare):
    return type(obj) == compare

# enter a value in format "19.54" and returned in decimal format, stored as integer to maintain precision
class Currency(types.TypeDecorator):
    impl = types.Integer

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.Integer)

    def process_bind_param(self, value, dialect):
        if value == None:
            return None

        # formatting
        if value.find('$') != -1:
            value = value.split('$')[1]
        value = value.replace(',', '')

        numDecimalChars = 0
        if value.find(".") != -1:
            numDecimalChars = len(value.split('.')[1])

        # ensure 2 decimal places
        while (numDecimalChars != 2):
            value += "0"
            numDecimalChars += 1

        # validation
        nonNumericCharacters = len(re.findall('[^0-9]', value)) > 1
        if nonNumericCharacters or numDecimalChars > 2:
            raise Exception("'{0}' is invalid format for currency.".format(str(value)))

        return int(value.replace(".", ""))

    def process_result_value(self, value, dialect):
        if value == None:
            return None
        value = str(value)
        value = value[:-2] + '.' + value[-2:]
        return Decimal(value)


class Coordinate(object):
    def __init__(self, obj):
        self.lat = Decimal(obj["lat"])
        self.lng = Decimal(obj["lng"])

    def stringify(self):
        return str({"lat": self.lat, "lng": self.lng})

# enter a value in format "-84.541423,42.7368049" and return a coordinate object
class SQLCoordinate(types.TypeDecorator):
    impl = types.VARCHAR(256)
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(256))
    def process_bind_param(self, value, dialect):
        if value == None:
            return None

        if not typeMatch(value, Coordinate) or value.lat == None or value.lng == None:
            raise Exception("'{0}' is invalid format for coordinate.".format(str(value)))

        return str(value.stringify())
    def process_result_value(self, value, dialect):
        if value == None:
            return None
        # TODO: seems dangerous
        return Coordinate(eval(value))

class ParcelNumberArray(types.TypeDecorator):
    impl = types.String(32)

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.String(32))

    def process_bind_param(self, value, dialect):
        if value == None:
            return None
        if type(value) != list:
            raise Exception("'{0}' is invalid format for Array.".format(str(value)))
        return str(value)

    def process_result_value(self, value, dialect):
        if value == None:
            return None
        return eval(value)

# sqlAlchemy classes
class Parcel(Base):
    __tablename__ = 'parcels'
    id = Column(Integer, primary_key=True)
    tabs = Column(String(256))
    propertyAddress = Column(String(512))
    owner = Column(String(256))
    ownerAddress = Column(String(512))
    schoolDistrict = Column(String(256))
    legalDescription = Column(String(8192))
    mapNumber = Column(String(64))
    occupancy = Column(String(64))
    yearBuilt = Column(Integer)
    landValue = Column(Currency)
    landImprovements = Column(Currency)
    dimensions = Column(String(256))
    taxableValue = Column(Currency)
    parcelNumber = Column(String(64))
    bedrooms = Column(Integer)
    propertyClass = Column(String(64))
    buildingClass = Column(String(64))
    water = Column(String(64))
    sewer = Column(String(64))
    style = Column(String(64))
    acreage = Column(Numeric)
    zoningCode = Column(String(64))
    builtInInformation = Column(String(128))
    numFullBaths = Column(Integer)
    rental = Column(Boolean)
    assessedValue = Column(Currency)
    cool = Column(String(32))
    dishwasher = Column(String(32))
    numHalfBaths = Column(Integer)
    renZone = Column(String(32))
    heat = Column(String(128))
    footage = Column(Integer)
    garageSize = Column(Integer)
    floorSize = Column(Integer)
    foundationSize = Column(Integer)
    basementSize = Column(Integer)
    sales = relationship("Sale", back_populates="parcel", cascade="delete")
    taxes = relationship("Tax", back_populates="parcel", cascade="delete")
    certificates = relationship("Certificate", back_populates="parcel", cascade="delete")
    __table_args__ = (UniqueConstraint('parcelNumber'),)
    createDate = Column(types.DateTime)
    lat = Column(Numeric(33,30))
    long = Column(Numeric(33,30))
    municipality_id = Column(Integer)

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True)
    parcelId = Column(Integer, ForeignKey('parcels.id'))
    parcel = relationship("Parcel", back_populates="sales")
    date = Column(Date)
    price = Column(Currency)
    grantee = Column(String(256))
    grantor = Column(String(256))
    instrument = Column(String(64))
    terms = Column(String(128))
    __table_args__ = (UniqueConstraint('parcelId', 'date', 'price', ),)
    createDate = Column(types.DateTime)


class Tax(Base):
    __tablename__ = 'taxes'
    id = Column(Integer, primary_key=True)
    parcelId = Column(Integer, ForeignKey('parcels.id'))
    parcel = relationship("Parcel", back_populates="taxes")
    season = Column(String(32))
    year = Column(Integer)
    propertyClass = Column(String(64))
    due = Column(Currency)
    paid = Column(Currency)
    datePaid = Column(Date)
    taxableValue = Column(Currency)
    assessedValue = Column(Currency)
    taxDetails = relationship("TaxDetail", back_populates="tax", cascade="delete")
    __table_args__ = (UniqueConstraint('parcelId', 'season', 'year'),)
    createDate = Column(types.DateTime)

class TaxDetail(Base):
    __tablename__ = 'taxDetails'
    id = Column(Integer, primary_key=True)
    taxId = Column(Integer, ForeignKey('taxes.id'))
    tax = relationship("Tax", back_populates="taxDetails")
    milage = Column(String(32))
    authority = Column(String(256))
    due = Column(Currency)
    paid = Column(Currency)
    __table_args__ = (UniqueConstraint('taxId', 'authority', 'due'),)
    createDate = Column(types.DateTime)

class Certificate(Base):
    __tablename__ = 'certificates'
    id = Column(Integer, primary_key=True)
    parcelId = Column(Integer, ForeignKey('parcels.id'))
    parcel = relationship("Parcel", back_populates="certificates")
    type = Column(String(128))
    number = Column(String(64))
    status = Column(String(64))
    issued = Column(Date)
    inspected = Column(Date)
    __table_args__ = (UniqueConstraint('parcelId', 'number', 'issued'),)
    createDate = Column(types.DateTime)

class Municipality(Base):
    __tablename__ = 'municipalities'
    id = Column(Integer, primary_key=True)
    name = Column(String(64))