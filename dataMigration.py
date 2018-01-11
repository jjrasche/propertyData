#!/usr/bin/env python

import getopt
import sys
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

def make_session(connection_string):
    engine = create_engine(connection_string, echo=False, convert_unicode=True)
    Session = sessionmaker(bind=engine)
    return Session(), engine

source, sengine = make_session("sqlite:///property_data.db")
smeta = MetaData(bind=sengine)
destination, dengine = make_session("e")

def pull_data(tables):
    for table_name in tables:
        print 'Processing', table_name
        print 'Pulling schema from source server'
        table = Table(table_name, smeta, autoload=True)
        print 'Creating ' + table_name + ' on destination server'
        # table.metadata.create_all(dengine)
        NewRecord = quick_mapper(table)
        columns = table.columns.keys()
        print 'Transferring ' + table_name + ' records'
        all = source.query(table).all()
        total = source.query(table).count()
        count = 0;

        for record in all:
            try:
                data = dict(
                    [(str(column), getattr(record, column)) for column in columns]
                )
                destination.merge(NewRecord(**data))
                count += 1
                percentDone = (count/float(total))*100
                if percentDone % 1 == 0:
                    print percentDone
            except Exception, e:
                print e.message
                raise e

    print 'Committing changes'
    destination.commit()

def print_usage():
    print """
Usage: %s -f source_server -t destination_server table [table ...]
    -f, -t = driver://user[:password]@host[:port]/database

Example: %s -f oracle://someuser:PaSsWd@db1/TSH1 \\
    -t mysql://root@db2:3307/reporting table_one table_two
    """ % (sys.argv[0], sys.argv[0])

def quick_mapper(table):
    Base = declarative_base()
    class GenericMapper(Base):
        __table__ = table
    return GenericMapper

# if __name__ == '__main__':
#     optlist, tables = getopt.getopt(sys.argv[1:], 'f:t:')
#
#     options = dict(optlist)
#     if '-f' not in options or '-t' not in options or not tables:
#         print_usage()
#         raise SystemExit, 1


pull_data(["parcels", "sales", "certificates", "taxes", "taxDetails"]);