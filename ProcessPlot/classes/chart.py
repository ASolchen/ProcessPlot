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
from classes.pen import Pen
import json, ast
from classes.popup import ChartSettingsPopup, TimeSpanPopup

__all__ = ['Chart']
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),  'Public')

FRAG_SHADER ='''#version 150
    in vec4 color;
    out vec4 fColor;

    void main () {
      fColor = color;
    }'''

VERT_SHADER='''#version  150
in vec2 vert;
in vec4 in_color;
out vec4 color;
void main () {
  color = in_color;
  gl_Position = vec4(vert, -.99f, 1.0f);
}'''


class Shaders(GObject.Object):
  '''do not instantiate if context is not current'''

  def __init__(self):
    super(Shaders, self).__init__()
    self.compile_shaders()


  def compile_shaders(self):
    vert_shader = shaders.compileShader(VERT_SHADER, GL_VERTEX_SHADER)
    frag_shader = shaders.compileShader(FRAG_SHADER, GL_FRAGMENT_SHADER)
    self.overlay_shader_prog = shaders.compileProgram(vert_shader, frag_shader)
    


class Chart(Gtk.GLArea):
  __log = logging.getLogger("ProcessPlot.classes.Chart")

  def __init__(self, app, db_id=None):
    super(Chart, self).__init__()
    self.app = app
    self.db_id = db_id # None means it's new and isn't to be looked up in the db, if saved, gets an id.
    self.db_model = app.settings_db.models['chart']
    self.db_session = app.settings_db.session

    self.db_pen_session = app.settings_db.session
    self.db_pen_model = app.settings_db.models['pen']
    self.Pen_Settings_Tbl = self.db_pen_model

    #settings
    self.pens = {}
    self.is_running = True
    self.end_time = time.time()
    self.span = 100.0
    self.bg_color = [0.1,0.1,0.1,1.0] #default to dark gray
    self.grid_color = [1.0,1.0,1.0,1.0] #default to white
    self.h_grids = 2
    self.v_grids = 2
    self.marker1_color = [1.0,0.0,0.0,1.0] #default to red
    self.marker2_color = [0.0,1.0,0.0,1.0] #default to blue
    self.marker1_width = 1
    self.marker2_width = 1
    self.time_span = 1
    self.start_hour = 12
    self.start_minute = 1
    self.start_second = 1
    self.start_year = 2022
    self.start_month = 1
    self.start_day = 1
    #settings
    self.load_settings()
    self.load_pen_settings()
    self.context_realized = False
    self.context = None
    self.shaders = None
    self.vaos = []
    self.connect("realize", self.on_realize)
    self.connect("render", self.on_render)
    GObject.timeout_add(100, self.trigger_render)


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
      except RuntimeError:
        print('OpenGL Error - Data logging only')
        self.shaders = None
      if self.shaders:
        self.init_vaos()
    if self.shaders:
      self.render()
  
  def load_settings(self):
    #loading chart settings
    if not self.db_id:
      return
    tbl = self.db_model
    settings = self.db_session.query(tbl).filter(tbl.id == self.db_id).first() # find one with this id
    if settings:
      self.bg_color = json.loads(settings.bg_color) #rgb in json
      self.h_grids = settings.h_grids
      self.v_grids = settings.v_grids
      self.grid_color = json.loads(settings.grid_color) #rgb in json
      self.marker1_width = settings.marker1_width
      self.marker1_color = json.loads(settings.marker1_color) #rgb in json
      self.marker2_width = settings.marker2_width
      self.marker2_color = json.loads(settings.marker2_color) #rgb in json
      self.time_span = settings.time_span
      self.start_hour = settings.start_hour
      self.start_minute = settings.start_minute
      self.start_second = settings.start_second
      self.start_year = settings.start_year
      self.start_month = settings.start_month
      self.start_day = settings.start_day
    else:
      #create chart settings in db if they don't exist
      new = tbl(id = self.db_id)
      self.db_session.add(new)
      self.db_session.commit()    
      self.db_session.refresh(new)  #Retrieves newly created chart settings from the database (new.id)

      self.bg_color = json.loads(new.bg_color) #rgb in json
      self.h_grids = new.h_grids
      self.v_grids = new.v_grids
      self.grid_color = json.loads(new.grid_color) #rgb in json
      self.marker1_width = new.marker1_width
      self.marker1_color = json.loads(new.marker1_color) #rgb in json
      self.marker2_width = new.marker2_width
      self.marker2_color = json.loads(new.marker2_color) #rgb in json
      self.time_span = new.time_span
      self.start_hour = new.start_hour
      self.start_minute = new.start_minute
      self.start_second = new.start_second
      self.start_year = new.start_year
      self.start_month = new.start_month
      self.start_day = new.start_day

  def reload_chart(self):
    self.load_settings()
    
  def load_pen_settings(self):
    ##### chart number ----- self.db_id
    #loading pen settings
    if not self.db_id:
      return
    #separate pen settings based on chart number
    settings = self.db_session.query(self.Pen_Settings_Tbl).filter(self.Pen_Settings_Tbl.chart_id == self.db_id).order_by(self.Pen_Settings_Tbl.id) # find one with this id
    if settings:
      for params in settings:
        self.pens[params.id] = Pen(self,params)
  
  def save_settings(self):
    tbl = self.db_model
    entry = None
    if self.db_id:
      entry = self.db_session.query(tbl).filter(tbl.id==self.db_id).first()
    if entry: # update it
      entry.bg_color = json.dumps(self.bg_color)
      entry.h_grids= self.h_grids
      entry.v_grids=self.v_grids
      entry.grid_color = json.dumps(self.grid_color)
      entry.marker1_width=self.marker1_width
      entry.marker1_color = json.dumps(self.marker1_color)
      entry.marker2_width=self.marker2_width
      entry.marker2_color = json.dumps(self.marker2_color)
      entry.time_span=self.time_span
      entry.start_hour=self.start_hour
      entry.start_minute=self.start_minute
      entry.start_second=self.start_second
      entry.start_year=self.start_year
      entry.start_month=self.start_month
      entry.start_day=self.start_day
    else: #create it
      entry = tbl(
        bg_color = json.dumps(self.bg_color),
        h_grids= self.h_grids,
        v_grids=self.v_grids,
        grid_color = json.dumps(self.grid_color),
        marker1_width=self.marker1_width,
        marker1_color = json.dumps(self.marker1_color),
        marker2_width=self.marker2_width,
        marker2_color = json.dumps(self.marker2_color),
        time_span = self.time_span,
        start_hour = self.start_hour,
        start_minute = self.start_minute,
        start_second = self.start_second,
        start_year = self.start_year,
        start_month = self.start_month,
        start_day = self.start_day,
      )
      self.db_session.add(entry)
    self.db_session.commit()
    self.db_id = entry.id
    
  def init_vaos(self):
    self.vaos = glGenVertexArrays(1)

  def render(self, *args):
    glClearColor(*self.bg_color)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glFlush()

  def trigger_render(self, *args):
    self.queue_render()
    if self.is_running:
      self.end_time = time.time()
    return True
  
  def toggle_running(self, *args):
    self.is_running = not self.is_running

  def add_pen(self,pen_id,*args):
    params = self.db_session.query(self.Pen_Settings_Tbl).filter(self.Pen_Settings_Tbl.id == pen_id).first # find one with this id
    self.pens[pen_id] = Pen(self,params)

  def delete_pen(self,pen_id,*args):
    del self.pens[pen_id]


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
  
  def __init__(self, chart,app) -> None:
      super().__init__(orientation=Gtk.Orientation.VERTICAL)
      self.app = app
      self.chart = chart
      #Chart settings button
      settings_button = Gtk.Button(width_request = 30)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/settings.png'), 30, -1, True)
      image = Gtk.Image(pixbuf=p_buf)
      settings_button.add(image)
      sc = settings_button.get_style_context()
      sc.add_class('ctrl-button')
      settings_button.connect('clicked',self.open_chart_settings)
      #Chart play button
      play_button = Gtk.Button(width_request = 30)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/play.png'), 30, -1, True)
      image = Gtk.Image(pixbuf=p_buf)
      play_button.add(image)
      sc = play_button.get_style_context()
      sc.add_class('ctrl-button')
      play_button.connect('clicked', chart.toggle_running)
      #TimeSpan Button
      clock_button = Gtk.Button(width_request = 30)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/Clock.png'), 40, -1, True)
      image = Gtk.Image(pixbuf=p_buf)
      clock_button.add(image)
      sc = clock_button.get_style_context()
      sc.add_class('ctrl-button')
      clock_button.connect('clicked',self.open_chart_timespan)
      button_row = Gtk.Box()
      for widget in [
        (Gtk.Box(),1,1,1),
        (settings_button,0,0,1),
        (play_button,0,0,1),
        (clock_button,0,0,1),
        (Gtk.Box(),1,1,1)]:
        button_row.pack_start(*widget)
      for widget_row in [
        (Gtk.Box(),1,1,1),
        (Gtk.Box(),1,1,1),
        (Gtk.Box(),1,1,1),
        (Gtk.Box(),1,1,1),
        (button_row,0,0,1),
      ]:
        self.pack_start(*widget_row)
      
  def open_chart_settings(self,*args):
    popup = ChartSettingsPopup(self.app,self.chart)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      return True
    else:
      return False

  def open_chart_timespan(self,*args):
    #self.clock_button.connect('clicked',self.open_popup,"timespan",self.app)
    popup = TimeSpanPopup(self.app,self.chart)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      return True
    else:
      return False

class ChartBox(Gtk.Overlay):
  """Use to put overlay and eventbox on the chart"""
  __log = logging.getLogger("ProcessPlot.classes.Chart")
  def __init__(self, app, chart_id) -> None:
    super().__init__()
    self.app = app
    self.chart = Chart(self.app, chart_id)
    self.app.charts[chart_id] = self.chart  #As charts are created add reference to them up on APP
    self.app.charts_number +=1
    self.eventbox = ChartEventBox(self.chart)
    self.add(self.eventbox)
    self.add_overlay(ChartControls(self.chart,self.app))
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
  
  def build_hidden_charts(self):
    #This allows pens to be saved to hidden charts
    for chrt in range(self.charts,16):
      ChartBox(self.app, chrt+1)

  def build_charts(self):
    #self.app.charts = {} # When charts are rebuilt then clear dictionary holding reference
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
      self.build_hidden_charts()
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
      self.build_hidden_charts()
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
      self.build_hidden_charts()
      return
    #default
    self.pack_start(ChartBox(self.app, 1),1,1,1)
    self.show_all()
    self.build_hidden_charts()
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


