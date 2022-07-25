"""
Copyright (c) 2021 Adam Solchenberger asolchenberger@gmail.com, Jason Engman engmanj@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import logging
import numpy as np
from gi.repository import Gdk, GdkPixbuf, GObject, Gtk
from classes.database import PenSettings

class Pen(object):
  __log = logging.getLogger("ProcessPlot.classes.Pen")
  orm_model = PenSettings
  @classmethod
  def get_params_from_orm(cls, result):
    """
    pass in an orm result (database query result) and this will update the params dictionary
    with the table columns. the params object is used to pass into a widget's init
    """
    params = {
    "id": result.id,
    "chart_id": result.chart_id,
    "tag_id": result.tag_id,
    "connection_id": result.connection_id,
    "visible": result.visible,
    "color": result.color,
    "weigth": result.weight,
    "scale_minimum": result.scale_minimum,
    "scale_maximum": result.scale_maximum,
    "scale_lock": result.scale_lock,
    "scale_auto": result.scale_auto,
    }
    return params
  @GObject.Property(type=int, flags=GObject.ParamFlags.READABLE)
  def id(self):
    return self._id 
  @GObject.Property(type=int, flags=GObject.ParamFlags.READWRITE)
  def chart_id(self):
    return self._chart_id  
  @chart_id.setter
  def chart_id(self, value):
    self._chart_id = value
    #self.move()
  @GObject.Property(type=int, flags=GObject.ParamFlags.READWRITE)
  def tag_id(self):
    return self._tag_id  
  @tag_id.setter
  def tag_id(self, value):
    self._tag_id = value
    #self.move()
  @GObject.Property(type=int, flags=GObject.ParamFlags.READWRITE)
  def connection_id(self):
    return self._connection_id
  @connection_id.setter
  def connection_id(self, value):
    self._connection_id = value
    #self.resize()
  @GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READABLE)
  def visible(self):
    return self._visible  
  @visible.setter
  def visible(self, value):
    self._visible = value
    #self.resize()
  @GObject.Property(type=str, flags=GObject.ParamFlags.READWRITE)
  def color(self):
    return self._color  
  @color.setter
  def color(self, value):
    self._color = value
    #self.resize()
  @GObject.Property(type=int, flags=GObject.ParamFlags.READWRITE)
  def weight(self):
    return self._weight
  @weight.setter
  def weight(self, value):
    self._weight = value
    #self.resize()
  @GObject.Property(type=str, flags=GObject.ParamFlags.READWRITE)
  def scale_minimum(self):
    return self._scale_minimum 
  @scale_minimum.setter
  def scale_minimum(self, value):
    self._scale_minimum = value
    #self.resize()
  @GObject.Property(type=str, flags=GObject.ParamFlags.READWRITE)
  def scale_maximum(self):
    return self._scale_maximum 
  @scale_maximum.setter
  def scale_maximum(self, value):
    self._scale_maximum = value
    #self.resize()
  @GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READABLE)
  def scale_lock(self):
    return self._scale_lock 
  @scale_lock.setter
  def scale_lock(self, value):
    self._scale_lock = value
    #self.resize()
  @GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READABLE)
  def scale_auto(self):
    return self._scale_auto
  @scale_auto.setter
  def scale_auto(self, value):
    self._scale_auto = value
    #self.resize()
  
  def __init__(self, chart, params) -> None:
    super().__init__()
    self.chart = chart
    self.app = chart.app
    self.buffer = np.ndarray(shape=(2,0xFFFFF), dtype=float)
    self.params = params
    self.initialize_params()
    
  def initialize_params(self, *args):
    #private settings
    try:
      self._chart_id = self.params.chart_id
      self._connection_id = self.params.connection_id
      self._tag_id = self.params.tag_id
      self._color = self.params.color
      self._visible = self.params.visible
      self._weight = self.params.weight
      self._scale_minimum = self.params.scale_minimum
      self._scale_maximum = self.params.scale_maximum
      self._scale_lock = self.params.scale_lock
      self._scale_auto = self.params.scale_auto
    except:
      pass