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


from ctypes import set_errno
import logging, time
import numpy as np
from gi.repository import Gdk, GdkPixbuf, GObject, Gtk
from classes.database import PenSettings
from OpenGL.GL import *
from OpenGL.GLU import *

MAX_PLOT_POINTS = 0xFFFFF
LOAD_INTERVAL = 0.5

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

    self.data_manager = self.app.data_manager
    self.shader_program = None
    self.id = pen_id
    self.point_id = point_id
    self.color = (1.0,0.0,0.0,1.0)
    self.width = 8
    self.visible = True
    self.last_data_load = time.time()
    self.val_min = 0.0
    self.val_max = 4000.0
    self.vao = None
    self.vbos = None
    self.active_vao = 0
    self.gl_ready = False
    self.initialize()
    #self.__log.debug(f"Pen {self.id} created on chart {self.chart} for point {self.point_id}")
  
  def initialize(self):
    """wipes all pen data and sets time pointer back to zero"""
    self.buffer = np.ndarray(shape=(2,MAX_PLOT_POINTS), dtype=float)
    self.time_ptr = 0.0 # drawn up to time
    self.sample_ptr = 0 # next sample stores here in the memory buffer
    self.gl_sample_ptr = 0 # draw up to this sample in the the GL buffer

  def get_data(self):
    """
    uses chart time and span to ask data_manager
    for data and 
    adds data to the pen buffer. Also moves time pointer fwd
    """
    import random
    self.buffer[0][0:100] = [random.random() for r in range(100)]
    self.buffer[1][0:100] = [random.random() for r in range(100)]
    self.sample_ptr = 100
    return
    end = self.chart.end_time + (0.5* self.chart.span)
    start = max(self.time_ptr, end - (2* self.chart.span))
    data = self.data_manager.get_data(self.point_id, start_time=start, end_time=end)
    for sample in data:
      #add to buffer
      self.buffer[0][self.sample_ptr] = sample[0] - self.chart.time_base_point
      self.buffer[1][self.sample_ptr] = sample[1]
      self.sample_ptr += 1
    if len(data):
      self.time_ptr = data[-1][0]
    
    
  def fill_gpu(self):
    """called when GL context is current, load the GPU"""
    if not self.visible or \
       self.gl_sample_ptr >= self.sample_ptr or \
       not self.gl_ready:
      return # nothing to load or load to
    # bind to the active VAO
    glBindVertexArray(self.vaos[self.active_vao])
    #stuff new data in the active "time" VBO
    glBindBuffer(GL_ARRAY_BUFFER, self.vbos[self.active_vao][0])
    glBufferSubData(GL_ARRAY_BUFFER,
                    self.gl_sample_ptr *  sizeof(GLfloat), #start
                    (self.sample_ptr - self.gl_sample_ptr) * sizeof(GLfloat),
                                self.buffer[0][self.gl_sample_ptr:self.sample_ptr])
    time_attrib = glGetAttribLocation(self.shader_program, 'time')
    glVertexAttribPointer(time_attrib, 1, GL_FLOAT, False, 0, ctypes.c_void_p(0))
    glEnableVertexAttribArray(time_attrib)
    #stuff new data in the active "value" VBO
    glBindBuffer(GL_ARRAY_BUFFER, self.vbos[self.active_vao][1])
    glBufferSubData(GL_ARRAY_BUFFER,
                    self.gl_sample_ptr *  sizeof(GLfloat), #start
                    (self.sample_ptr - self.gl_sample_ptr) * sizeof(GLfloat),
                                self.buffer[1][self.gl_sample_ptr:self.sample_ptr])
    val_attrib = glGetAttribLocation(self.shader_program, 'value')
    glVertexAttribPointer(val_attrib, 1, GL_FLOAT, False, 0, ctypes.c_void_p(0))
    glEnableVertexAttribArray(val_attrib)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    #move pointer up
    self.gl_sample_ptr = self.sample_ptr
    self.last_data_load = time.time()
    

    
  def init_gl(self):
    """create all GL objects needed for pen rendering"""
    self.shader_program = self.chart.shaders.pen_shader
    self.vbos = []
    self.vaos = glGenVertexArrays(2) 
    #even buffers for time, odd ones for values
    #buffers 0,1 used until over 1/2 full, then buffers 2,3 fill from charts current start.
    #once non-active set is fill, active set swaps 
    for idx, vao in enumerate(self.vaos):
      glBindVertexArray(self.vaos[idx])
      self.vbos.append(glGenBuffers(2)) # Generate buffers to hold vertices
      for vbo_idx, vbo in enumerate(self.vbos[idx]):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbos[idx][vbo_idx])
        glBufferData(GL_ARRAY_BUFFER, MAX_PLOT_POINTS * sizeof(GLfloat), None, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0) #unbind the buffer
      glBindVertexArray(0)
    self.gl_ready = True

  def render(self, *args):
    """GL context is current, render the pen line"""
    if not self.chart.shaders:
      return #can't do anything until shader is compiled by chart
    if not self.gl_ready: 
      self.init_gl()
    
    glBindVertexArray(self.vaos[self.active_vao])
    #get color attrib from shader program, pass in the color
    c_attrib = glGetAttribLocation(self.shader_program, 'in_color')
    if c_attrib >= 0:
      glVertexAttrib4f(c_attrib, *self.color)
    else:
      self.__log.error("Pen failed to bind to GL color attibute")
    #get the scaling attrib from the shader, pass in the chart time scale and this pens value scale
    scl_attrib = glGetAttribLocation(self.shader_program, 'scale')
    if scl_attrib >= 0:
      """       glVertexAttrib4f(scl_attrib,
	          (self.chart.end_time - self.chart.span) - self.chart.time_base_point,
	          self.chart.end_time - self.chart.time_base_point,
	          self.val_min,
	          self.val_max) """
      glVertexAttrib4f(scl_attrib,
	          -100.0,
	          100.0,
	          -100.0,
	          100.0)
    else:
      self.__log.error("Pen failed to bind to GL scale attibute")
    #use the shader to draw the line
    glUseProgram(self.shader_program)
    #use the active set of vbos to draw the linestrip
    glLineWidth(self.width)
    glDrawArrays(GL_LINE_STRIP, 0, self.gl_sample_ptr)
    
    #unbind vao and program
    glBindVertexArray(0)
    glUseProgram(0)
    if self.last_data_load < time.time()-LOAD_INTERVAL:
      self.fill_gpu()
    
