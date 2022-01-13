import os, logging 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base, relationship, backref
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql.sqltypes import Float, Numeric


# see videos below for help:
# https://www.youtube.com/watch?v=jaKMm9njcJc&list=PL4iRawDSyRvVd1V7A45YtAGzDk6ljVPm1




SettingsBase = declarative_base()
class AppSettings(SettingsBase):
    __tablename__ = 'app_settings'
    id = Column(Integer, primary_key=True)
    last_save = Column(DateTime)
    headless = Column(Boolean)
    #other cols

class UiSettings(SettingsBase):
    __tablename__ = 'ui_settings'
    id = Column(Integer, primary_key=True)
    dark_mode = Column(Boolean)
    charts = Column(Integer)
    headless = Column(Boolean)
    screen_width = Column(Integer)
    screen_height = Column(Integer)
    #other cols

class ChartLayoutSettings(SettingsBase):
    __tablename__ = 'chart_layout_settings'
    id = Column(Integer, primary_key=True)
    cols = Column(Integer)
    rows = Column(Integer) 
    chart_map = Column(String) #save a list of the chart ids to place in each spot
    charts = Column(Integer)
    #other cols

class ChartSettings(SettingsBase):
    __tablename__ = 'chart_settings'
    id = Column(Integer, primary_key=True)
    bg_color = Column(String) #rgb in json
    h_grids = Column(Integer)
    v_grids = Column(Integer)
    #other cols

class PenSettings(SettingsBase):
    __tablename__ = 'pen_settings'
    id = Column(Integer, primary_key=True)
    chart_id = Column(Integer,default=1)
    connection_id = Column(Integer)
    tag_id = Column(Integer)
    visible = Column(Boolean,default=1)
    color = Column(String, default = '#0000ff') #rgb in json
    weight = Column(String, default='1') # width
    scale_minimum = Column(String,default='0')
    scale_maximum = Column(String,default='100')
    scale_lock = Column(Boolean,default=0)
    scale_auto = Column(Boolean,default=0)
    #other cols


DataBase = declarative_base()
class Values(DataBase):
    __tablename__ = 'values'
    id = Column(Integer, primary_key=True)
    point_id = Column(Integer)
    timestamp = Column(Numeric)
    value = Column(Numeric)

    
class SettingsDb():
    __log = logging.getLogger("ProcessPlot.classes.database")
    def __init__(self) -> None:
        super(SettingsDb, self).__init__()
        my_dir = os.path.dirname(__file__)
        main_dir = os.path.dirname(my_dir)
        engine = create_engine('sqlite:///'+ main_dir + "/settings/settings.db") #should create a .db file next to main.py
        self.models = {
            "app": AppSettings,
            "ui": UiSettings,
            "chart_layout": ChartLayoutSettings,
            "chart": ChartSettings,
            "pen": PenSettings,
        }
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.__log.debug('Opening database session for settings database')
        SettingsBase.metadata.create_all(engine) #creates all the tables above
        self.__log.debug(f"Database models created for settings database")

    def close(self):
        self.__log.debug('Closing settings database session')
        self.session.close()

'''
class Connections(SettingsBase):
    __tablename__ = 'connections'
    id = Column(Integer, primary_key=True)
    connection = Column(String)
    connection_type_id = Column(Integer)
    description = Column(String)

class ConnectionType(SettingsBase):
    __tablename__ = 'connection_type'
    id = Column(Integer, primary_key=True)
    connection_type = Column(String)
    protcol = Column(String)
    description = Column(String)

class ModbusTCP_ConnectParams(SettingsBase):
    __tablename__ = 'modbusTCP_ConnectParams'
    id = Column(String, ForeignKey(Connections.id, ondelete='CASCADE'), primary_key=True)
    host = Column(String)
    port = Column(Integer)
    stationID = Column(Integer)
    pollrate = Column(Integer)
    autoconnect = Column(Boolean)
    status = Column(Boolean)
    description = Column(String)
'''
ConnectionsBase = declarative_base()

class ConnectionTable(ConnectionsBase): # this table holds all tag values being subscribed to
  __tablename__ = 'connections'
  id = Column(String, primary_key=True)
  connection_type = Column(Integer, nullable=False)
  description = Column(String)

class ConnectionParamsModbusRTU(ConnectionsBase):
  __tablename__= 'connection-params-modbusRTU'
  relationship('ConnectionTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(ConnectionTable.id, ondelete='CASCADE'), primary_key=True)
  pollrate = Column(Float, default=0.5)
  auto_connect = Column(Boolean, default=False)
  status = Column(Integer) #what is this?
  port = Column(String)
  station_id = Column(Integer, default=1)
  baudrate = Column(Integer, default=9600)
  timeout = Column(Float, default=3.0)
  stop_bit = Column(Integer, default=1)
  parity = Column(String, default='N')
  byte_size = Column(Integer, default=8)
  retries = Column(Integer, default=3)
  
class ConnectionParamsModbusTCP(ConnectionsBase):
  __tablename__= 'connection-params-modbusTCP'
  relationship('ConnectionTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(ConnectionTable.id, ondelete='CASCADE'), primary_key=True)
  pollrate = Column(Float, default=0.5)
  auto_connect = Column(Boolean, default=False)
  status = Column(Integer) #what is this?
  host = Column(String, default='127.0.0.1')
  port = Column(Integer, default=502)
  station_id = Column(Integer, default=1)

class ConnectionParamsEthernetIP(ConnectionsBase):
  __tablename__= 'connection-params-ethernetIP'
  relationship('ConnectionTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(ConnectionTable.id, ondelete='CASCADE'), primary_key=True)
  pollrate = Column(Float, default=0.5)
  auto_connect = Column(Boolean, default=False)
  status = Column(Integer) #what is this?
  host = Column(String, default='127.0.0.1') #uses pycomm3 syntax for PLC path
  port = Column(Integer, default=44818)

class ConnectionParamsOPC(ConnectionsBase):
  __tablename__= 'connection-params-opc'
  relationship('ConnectionTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(ConnectionTable.id, ondelete='CASCADE'), primary_key=True)
  pollrate = Column(Float, default=0.5)
  auto_connect = Column(Boolean, default=False)
  status = Column(Integer) #what is this?
  host = Column(String, default='opc.tcp://127.0.0.1:49320') #uses pyopc url syntax for path

class ConnectionParamsGrbl(ConnectionsBase):
  __tablename__= 'connection-params-grbl'
  relationship('ConnectionTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(ConnectionTable.id, ondelete='CASCADE'), primary_key=True)
  pollrate = Column(Float, default=0.5)
  auto_connect = Column(Boolean, default=False)
  status = Column(Integer) #what is this?
  port = Column(String, default='/dev/ttyACM0')

class ConnectionParamsLocal(ConnectionsBase):
  __tablename__= 'connection-params-local'
  relationship('ConnectionTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(ConnectionTable.id, ondelete='CASCADE'), primary_key=True)

class TagTable(ConnectionsBase): # this table holds all tag values being subscribed to
  __tablename__ = 'tags'
  id = Column(String, primary_key=True)
  connection_id = Column(String, ForeignKey(ConnectionTable.id))
  description = Column(String)
  datatype = Column(String)
  value = Column(String) # used for retenitive tags

class TagParamsLocal(ConnectionsBase):
  __tablename__= 'tag-params-local'
  relationship('TagTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(TagTable.id, ondelete='CASCADE'), primary_key=True)
  address = Column(String, nullable=False)

class TagParamsEthernetIP(ConnectionsBase):
  __tablename__= 'tag-params-ethernetIP'
  relationship('TagTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(TagTable.id, ondelete='CASCADE'), primary_key=True)
  address = Column(String, nullable=False)

class TagParamsModbus(ConnectionsBase):
  __tablename__= 'tag-params-modbus'
  relationship('TagTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(TagTable.id, ondelete='CASCADE'), primary_key=True)
  address = Column(Integer, nullable=False)
  bit = Column(Integer, default=0)
  word_swapped = Column(Boolean, default=False)
  byte_swapped = Column(Boolean, default=False)

class TagParamsOPC(ConnectionsBase):
  __tablename__= 'tag-params-opc'
  relationship('TagTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(TagTable.id, ondelete='CASCADE'), primary_key=True)
  node_id = Column(String, nullable=False)

class TagParamsGrbl(ConnectionsBase):
  __tablename__= 'tag-params-grbl'
  relationship('TagTable', backref=backref('children', passive_deletes=True))
  id = Column(String, ForeignKey(TagTable.id, ondelete='CASCADE'), primary_key=True)
  address = Column(String, nullable=False)

class ConnectionsDb():
    __log = logging.getLogger("ProcessPlot.classes.database")
    def __init__(self) -> None:
        super(ConnectionsDb, self).__init__()
        my_dir = os.path.dirname(__file__)
        main_dir = os.path.dirname(my_dir)
        engine = create_engine('sqlite:///'+ main_dir + "/data/connections.db") #should create a .db file next to main.py
        self.models = {
                "connections": ConnectionTable,
                "connection-params-ethernetIP":  ConnectionParamsEthernetIP,
                "connection-params-modbusRTU": ConnectionParamsModbusRTU,
                "connection-params-modbusTCP": ConnectionParamsModbusTCP,
                "connection-params-opc": ConnectionParamsOPC,
                "connection-params-grbl": ConnectionParamsGrbl,
                "connection-params-local": ConnectionParamsLocal,
                "tags": TagTable,
                "tag-params-local":  TagParamsLocal,
                "tag-params-ethernetIP":  TagParamsEthernetIP,
                "tag-params-modbus": TagParamsModbus,
                "tag-params-opc": TagParamsOPC,
                "tag-params-grbl": TagParamsGrbl
        }
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.__log.debug('Opening database session for connections database')
        ConnectionsBase.metadata.create_all(engine) #creates all the tables above
        self.__log.debug(f"Database models created for connections database")

    def close(self):
        self.__log.debug('Closing settings database session')
        self.session.close()

DataBase = declarative_base()
class Values(DataBase):
    __tablename__ = 'values'
    id = Column(Integer, primary_key=True)
    point_id = Column(Integer)
    timestamp = Column(DateTime)
    value = Column(Numeric)

class DataDb():
    __log = logging.getLogger("ProcessPlot.classes.database")
    def __init__(self) -> None:
        super(DataDb, self).__init__()
        my_dir = os.path.dirname(__file__)
        main_dir = os.path.dirname(my_dir)
        engine = create_engine('sqlite:///'+ main_dir + "/data/data.db") #should create a .db file next to main.py
        self.models = {
            "values": Values,
        }
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.__log.debug('Opening database session for data database')
        DataBase.metadata.create_all(engine) #creates all the tables above
        self.__log.debug(f"Database models created for data database")

    def close(self):
        self.__log.debug('Closing data database session')
        self.session.close()

