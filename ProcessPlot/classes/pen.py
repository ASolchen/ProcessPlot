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
from OpenGL.GL import *
from OpenGL.GLU import *

MAX_PLOT_POINTS = 0xFFFFF
LOAD_INTERVAL = 0.5

class Pen(object):
  __log = logging.getLogger("ProcessPlot.classes.Pen")
  
  def __init__(self, chart, pen_id, point_id=None) -> None:
    super().__init__()
    self.chart = chart
    self.app = chart.app
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
    
    
    
      
    

