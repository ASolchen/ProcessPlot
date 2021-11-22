import os, logging 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql.sqltypes import Numeric


# see videosbelow for help:
# https://www.youtube.com/watch?v=jaKMm9njcJc&list=PL4iRawDSyRvVd1V7A45YtAGzDk6ljVPm1




SettingsBase = declarative_base()
class AppSettings(SettingsBase):
    __tablename__ = 'app_settings'
    id = Column(Integer, primary_key=True)
    last_save = Column(DateTime)
    charts = Column(Integer)
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
    visible = Column(Boolean)
    color = Column(String) #rgb in json
    weight = Column(Numeric) # width

    #other cols

DataBase = declarative_base()
class Values(DataBase):
    __tablename__ = 'values'
    id = Column(Integer, primary_key=True)
    point_id = Column(Integer)
    timestamp = Column(DateTime)
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