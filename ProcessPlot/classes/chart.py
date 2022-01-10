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

from OpenGL.GL import *
from OpenGL.GLU import *
import logging, os, time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Gio
from OpenGL.GL import *
from OpenGL.GL import shaders
from classes.shaders import BasicVertShader, BasicFragShader, PenVertShader
from classes.pen import Pen
import json

__all__ = ['Chart']
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),  'Public')




class Shaders(GObject.Object):
  '''do not instantiate if context is not current'''

  def __init__(self):
    super(Shaders, self).__init__()
    self.compile_shaders()


  def compile_shaders(self):
    vert_shader = shaders.compileShader(BasicVertShader, GL_VERTEX_SHADER)
    frag_shader = shaders.compileShader(BasicFragShader, GL_FRAGMENT_SHADER)
    self.overlay_shader_prog = shaders.compileProgram(vert_shader, frag_shader)
    pen_vert_shader = shaders.compileShader(PenVertShader, GL_VERTEX_SHADER)
    self.pen_shader = shaders.compileProgram(pen_vert_shader, frag_shader)
    


class Chart(Gtk.GLArea):
  __log = logging.getLogger("ProcessPlot.classes.Chart")

  def __init__(self, app, db_id=None):
    super(Chart, self).__init__()
    self.app = app
    self.db_id = db_id # None means it's new and isn't to be looked up in the db, if saved, gets an id.
    self.db_model = app.settings_db.models['chart']
    self.db_session = app.settings_db.session
    #settings
    self.pens = {1: Pen(self, 1,point_id="3cbb1b41-0b52-495b-83da-26232d692d81")}
    self.is_running = True
    self.end_time = time.time()
    self.span = 1000000.0
    self.bg_color = (0.1, 0.1, 0.1, 1.0)
    self.h_grids = 0
    self.v_grids = 0
    #settings
    self.init_time_base()
    self.load_settings()
    self.context_realized = False
    self.context = None
    self.shaders = None
    self.vaos = []
    self.connect("realize", self.on_realize)
    self.connect("render", self.on_render)
    GObject.timeout_add(100, self.trigger_render)
    GObject.timeout_add(1000, self.get_data)

  def init_time_base(self):
    self.time_base_point = self.end_time - (0.5*self.span) # all OpenGL X vals (time) reference this point, move this on any buffer flushing (zoom, or big time move)

  def on_realize(self, area):
    self.context_realized = True
    #self.__log.info(f"GL Context Realized - {self}")

  def on_render(self, area, ctx):
    #self.__log.debug("Rendering....")
    if self.context == ctx == None:
      return
    elif self.context == None and ctx != None:
      self.context = ctx
      try:
        self.shaders = Shaders()
      except RuntimeError as e:
        self.__log.error(f'OpenGL Error - {e}')
        self.shaders = None
      if self.shaders:
        self.init_vaos()
    if self.shaders:
      self.render()
  
  def load_settings(self):
    if not self.db_id:
      return
    tbl = self.db_model
    settings = self.db_session.query(tbl).filter(tbl.id == self.db_id).first() # find one with this id
    if settings:
      self.bg_color = json.loads(settings.bg_color) #rgb in json
      self.h_grids = settings.h_grids
      self.v_grids = settings.v_grids
    # add fake pen for testing, this should be looked up in db
    self.pens["pen_id"] = Pen(self, "pen_id", point_id="data_point_id")
    
  def save_settings(self):
    tbl = self.db_model
    entry = None
    if self.db_id:
      entry = self.db_session.query(tbl).filter(tbl.id==self.db_id).first()
    if entry: # update it
      entry.bg_color = json.dumps(self.bg_color)
      entry.h_grids= self.h_grids
      entry.v_grids=self.v_grids
    else: #create it
      entry = tbl(
        bg_color = json.dumps(self.bg_color),
        h_grids= self.h_grids,
        v_grids=self.v_grids
      )
      self.db_session.add(entry)
    # or 
    # entry1 = model(bla= "blah")
    # entry2 = model(bla= "blah, blah")
    # self.db_session.add_all([entry1, entry2])
    self.db_session.commit()
    self.db_id = entry.id
    
  def init_vaos(self):
    self.vaos = glGenVertexArrays(1)

  def render(self, *args):
    glClearColor(*self.bg_color)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for p in self.pens:
      self.pens[p].render()
    glFlush()

  def trigger_render(self, *args):
    self.queue_render()
    if self.is_running:
      self.end_time = time.time()
    return True
  
  def toggle_running(self, *args):
    self.is_running = not self.is_running

  def get_data(self, *args):
    if self.vaos:
      for p in self.pens:
        self.pens[p].get_data()
    return True
    



class ChartEventBox(Gtk.EventBox):
  
  __log = logging.getLogger("ProcessPlot.classes.Chart")
  def __init__(self, chart) -> None:
    super().__init__()
    self.chart = chart
    self.add(chart)
    self.set_property("visible-window", False)
    self.set_above_child(True)
    sc = self.get_style_context()
    self.last_event = None
    sc.add_class('dialog-border')
  
  def do_button_release_event(self, *args):
    """testing event by setting bg to random color"""
    self.last_event = args
    self.chart.toggle_running()
    #self.__log.info(f'Event window clicked: args: {args}')
    

class ChartDebugBox(Gtk.Fixed):
  """shows chart debug info"""
  __log = logging.getLogger("ProcessPlot.classes.Chart")

  def __init__(self, chart_box) -> None:
    super().__init__()
    self.chart = chart_box.chart
    self.eventbox = chart_box.eventbox
    self.put(Gtk.Label(label="** Chart Debug Info **"), 10, 10)
    self.labels = {
      "time": Gtk.Label("Chart End:"),
      "span": Gtk.Label("Chart Span:"),
      "mode": Gtk.Label("Chart Running:"),
      "last_event": Gtk.Label("Last Event:"),
    }
    for idx, l in enumerate(self.labels):
      self.put(self.labels[l], 10, 30+20*idx)
    GObject.timeout_add(500, self.update)

  def update(self):
    t = time.ctime(self.chart.end_time)
    t = f"{t[:-5]}.{str(self.chart.end_time%1.0)[2:5]}{t[-5:]}"
    self.labels["time"].set_property("label", f"Chart End: {t}")
    self.labels["span"].set_property("label", f"Chart Span: {self.chart.span} sec")
    self.labels["mode"].set_property("label", f"Chart Running: {self.chart.is_running}")
    self.labels["last_event"].set_property("label", f"Last Event: {self.eventbox.last_event}")
    return True


class ChartControls(Gtk.Box):
  """holds chart control buttons"""
  __log = logging.getLogger("ProcessPlot.classes.Chart")
  
  def __init__(self, chart) -> None:
      super().__init__(orientation=Gtk.Orientation.VERTICAL)
      self.app = chart.app
      self.chart = chart
      settings_button = Gtk.Button(width_request = 30)
      #settings_button.connect('clicked', )
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/settings.png'), 20, -1, True)
      image = Gtk.Image(pixbuf=p_buf)
      settings_button.add(image)
      sc = settings_button.get_style_context()
      sc.add_class('ctrl-button')
      play_button = Gtk.Button(width_request = 30)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/play.png'), 30, -1, True)
      image = Gtk.Image(pixbuf=p_buf)
      play_button.add(image)
      sc = play_button.get_style_context()
      sc.add_class('ctrl-button')
      play_button.connect('clicked', chart.toggle_running)






      button_row = Gtk.Box()
      for widget in [
        (Gtk.Box(),1,1,1),
        (settings_button,0,0,1),
        (play_button,0,0,1),
        (Gtk.Box(),1,1,1)]:
        button_row.pack_start(*widget)
      for widget_row in [
        (Gtk.Box(),1,1,1),
        (Gtk.Box(),1,1,1),
        (Gtk.Box(),1,1,1),
        (button_row,0,0,1),
      ]:
        self.pack_start(*widget_row)


class ChartBox(Gtk.Overlay):
  """Use to put overlay and eventbox on the chart"""
  __log = logging.getLogger("ProcessPlot.classes.Chart")
  def __init__(self, app, chart_id) -> None:
    super().__init__()
    self.app = app
    self.chart = Chart(self.app, chart_id)
    self.eventbox = ChartEventBox(self.chart)
    self.add(self.eventbox)
    self.add_overlay(ChartControls(self.chart))
    # if debugging, add debug info to charts
    if logging.getLogger("ProcessPlot.classes.Chart").getEffectiveLevel() <= logging.DEBUG:
      debug = ChartDebugBox(self)
      self.add_overlay(debug)
      self.set_overlay_pass_through(debug, True) # allow inputs to pass through this widget


class ChartArea(Gtk.Box):
  __log = logging.getLogger("ProcessPlot.classes.ChartArea")
  def __init__(self, app, db_id=None):
    super(ChartArea, self).__init__(orientation=Gtk.Orientation.VERTICAL, spacing=40)
    self.app = app
    #settings
    self.charts = 1
    self.cols = 1
    self.rows = 1
    self.chart_map = '[1]' # json list(rows) of lists(cols) that map ids of charts to row 
    #settings
    self.db_model = self.app.settings_db.models['chart_layout']
    self.db_session = app.settings_db.session
    self.load_settings()
    self.save_settings()

  def build_charts(self):
    for child in self.get_children():
      self.remove(child)
    if self.charts == 2:
      v_pane = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)
      v_pane.pack1(ChartBox(self.app, 1),1,1)
      v_pane.pack2(ChartBox(self.app, 2),1,1)
      self.pack_start(v_pane,1,1,1)
      self.show_all()
      return
    if self.charts == 4:
      top_pane = Gtk.Paned(wide_handle=True)
      top_pane.pack1(ChartBox(self.app,1),1,1)
      top_pane.pack2(ChartBox(self.app,2),1,1)
      bot_pane = Gtk.Paned(wide_handle=True)
      bot_pane.pack1(ChartBox(self.app,3),1,1)
      bot_pane.pack2(ChartBox(self.app,4),1,1)
      v_pane = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)
      v_pane.pack1(top_pane,1,1)
      v_pane.pack2(bot_pane,1,1)
      self.pack_start(v_pane,1,1,1)
      self.show_all()
      return
    if self.charts == 8:
      topl_pane = Gtk.Paned(wide_handle=True)
      topl_pane.pack1(ChartBox(self.app,1),1,1)
      topl_pane.pack2(ChartBox(self.app,2),1,1)
      topr_pane = Gtk.Paned(wide_handle=True)
      topr_pane.pack1(ChartBox(self.app,3),1,1)
      topr_pane.pack2(ChartBox(self.app,4),1,1)
      top_pane = Gtk.Paned(wide_handle=True)
      top_pane.pack1(topl_pane,1,1)
      top_pane.pack2(topr_pane,1,1)
      botl_pane = Gtk.Paned(wide_handle=True)
      botl_pane.pack1(ChartBox(self.app,5),1,1)
      botl_pane.pack2(ChartBox(self.app,6),1,1)
      botr_pane = Gtk.Paned(wide_handle=True)
      botr_pane.pack1(ChartBox(self.app,7),1,1)
      botr_pane.pack2(ChartBox(self.app,8),1,1)
      bot_pane = Gtk.Paned(wide_handle=True)
      bot_pane.pack1(botl_pane,1,1)
      bot_pane.pack2(botr_pane,1,1)
      v_pane = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)
      v_pane.pack1(top_pane,1,1)
      v_pane.pack2(bot_pane,1,1)
      self.pack_start(v_pane,1,1,1)
      self.show_all()
      return
    if self.charts == 16:
      r1_left_pane = Gtk.Paned(wide_handle=True)
      r1_left_pane.pack1(ChartBox(self.app,1),1,1)
      r1_left_pane.pack2(ChartBox(self.app,2),1,1)
      r1_right_pane = Gtk.Paned(wide_handle=True)
      r1_right_pane.pack1(ChartBox(self.app,3),1,1)
      r1_right_pane.pack2(ChartBox(self.app,4),1,1)
      r1_pane = Gtk.Paned(wide_handle=True)
      r1_pane.pack1(r1_left_pane,1,1)
      r1_pane.pack2(r1_right_pane,1,1)
      r2_left_pane = Gtk.Paned(wide_handle=True)
      r2_left_pane.pack1(ChartBox(self.app,5),1,1)
      r2_left_pane.pack2(ChartBox(self.app,6),1,1)
      r2_right_pane = Gtk.Paned(wide_handle=True)
      r2_right_pane.pack1(ChartBox(self.app,7),1,1)
      r2_right_pane.pack2(ChartBox(self.app,8),1,1)
      r2_pane = Gtk.Paned(wide_handle=True)
      r2_pane.pack1(r2_left_pane,1,1)
      r2_pane.pack2(r2_right_pane,1,1)
      r1_r2_pane = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)
      r1_r2_pane.pack1(r1_pane,1,1)
      r1_r2_pane.pack2(r2_pane,1,1)

      r3_left_pane = Gtk.Paned(wide_handle=True)
      r3_left_pane.pack1(ChartBox(self.app,9),1,1)
      r3_left_pane.pack2(ChartBox(self.app,10),1,1)
      r3_right_pane = Gtk.Paned(wide_handle=True)
      r3_right_pane.pack1(ChartBox(self.app,11),1,1)
      r3_right_pane.pack2(ChartBox(self.app,12),1,1)
      r3_pane = Gtk.Paned(wide_handle=True)
      r3_pane.pack1(r3_left_pane,1,1)
      r3_pane.pack2(r3_right_pane,1,1)
      r4_left_pane = Gtk.Paned(wide_handle=True)
      r4_left_pane.pack1(ChartBox(self.app,13),1,1)
      r4_left_pane.pack2(ChartBox(self.app,14),1,1)
      r4_right_pane = Gtk.Paned(wide_handle=True)
      r4_right_pane.pack1(ChartBox(self.app,15),1,1)
      r4_right_pane.pack2(ChartBox(self.app,16),1,1)
      r4_pane = Gtk.Paned(wide_handle=True)
      r4_pane.pack1(r4_left_pane,1,1)
      r4_pane.pack2(r4_right_pane,1,1)
      r3_r4_pane = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)
      r3_r4_pane.pack1(r3_pane,1,1)
      r3_r4_pane.pack2(r4_pane,1,1)
      v_pane = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, wide_handle=True)
      v_pane.pack1(r1_r2_pane,1,1)
      v_pane.pack2(r3_r4_pane,1,1)
      self.pack_start(v_pane,1,1,1)
      self.show_all()
      return
    #default
    self.pack_start(ChartBox(self.app, 1),1,1,1)
    self.show_all()
    #self.__log.info(f"ChartArea built - {self}")
  
  def load_settings(self):
    settings = self.db_session.query(self.db_model).order_by(self.db_model.id.desc()).first() # last one saved?
    if settings:
      self.charts = settings.charts
      self.rows = settings.rows
      self.cols = settings.cols
      self.chart_map = settings.chart_map
    self.build_charts()

  
  def save_settings(self):
    entry = self.db_model(
      charts = self.charts,
      cols = self.cols,
      rows = self.rows,
      chart_map = self.chart_map
    )
    self.db_session.add(entry)
    # or 
    # entry1 = model(bla= "blah")
    # entry2 = model(bla= "blah, blah")
    # self.db_session.add_all([entry1, entry2])
    self.db_session.commit()


