import logging, sys, uuid, time
from datetime import datetime
import json, requests

class DataManager(object):
  __log = logging.getLogger("ProcessPlot.classes.DataManager")
  def __init__(self, app) -> None:
    super().__init__()
    self.app = app
    self.db = app.data_db
    self.db_session = self.db.session
    self.values_orm = self.db.models["values"]
    #self.get_data("3cbb1b41-0b52-495b-83da-26232d692d81", start_time=1638149396.066287, end_time=1638151580.236583)
    #self.add_fake_data()



  def add_fake_data(self):
    """get some USGS river flow data"""
    USGS_url = "https://nwis.waterservices.usgs.gov/nwis/iv/?site=05398000&format=json,1.1"
    start_tm = "&startDT=2021-11-02T00:00"
    end_tm = "&endDT=2021-12-08T00:00"
    r = requests.get(f'{USGS_url}{start_tm}{end_tm}').json()
    samples = r["value"]["timeSeries"][0]["values"][0]["value"]
    data = []
    for sample in samples:
      data.append(
        (datetime.timestamp(datetime.strptime(sample["dateTime"].replace("T"," ")[:-10],"%Y-%m-%d %H:%M:%S")),
        float(sample["value"])))
    self.add_data("3cbb1b41-0b52-495b-83da-26232d692d81",data=data)

  
  def add_data(self, point_id, data=[]):
    """data comes in a list of tuples (time, val)"""
    for ts, val in data:
      row = self.values_orm(point_id=point_id, timestamp=ts, value=val)
      self.db_session.add(row)
    self.db_session.commit()

  def get_data(self, point_id, start_time=0.0, end_time=time.time()):
    ret_vals = []
    tbl = self.values_orm
    samples = self.db_session.query(tbl)\
      .filter(tbl.point_id==point_id)\
      .filter(tbl.timestamp > start_time)\
      .filter(tbl.timestamp <= end_time)\
      .order_by(tbl.timestamp)\
      .all()
    if samples:
      for sample in samples:
        ret_vals.append((float(sample.timestamp), float(sample.value)))
    #self.__log.debug(f"{ret_vals}")
    return ret_vals




