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

import gi, os

from numpy import maximum
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
import re
from Public.widgets.checkbox import CheckBoxWidget

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),  'Public')


class BaseSettingsPopoup(Gtk.Dialog):

  def __init__(self, parent, title,app):
    super().__init__(title=title, transient_for = parent,flags=0) 
    self.app = app
    self.set_default_size(1500, 700)
    self.set_decorated(False)
    self.set_border_width(10)
    self.set_keep_above(False)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.content_area = self.get_content_area()

    self.dialog_window = Gtk.Box(width_request=600,orientation=Gtk.Orientation.VERTICAL)
    self.content_area.add(self.dialog_window)
    ### -title bar- ####
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=600)
    self.dialog_window.pack_start(self.title_bar,0,0,1)
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    ### -content area- ####
    self.base_area = Gtk.Box(spacing = 10,orientation=Gtk.Orientation.VERTICAL,margin = 20)
    self.scroll = Gtk.ScrolledWindow(width_request = 1400,height_request = 600)
    self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    self.scroll.add(self.base_area)
    self.dialog_window.pack_start(self.scroll,1,1,1)
    ### -footer- ####
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    self.footer_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=600)
    self.dialog_window.pack_start(self.footer_bar,0,0,1)

    self.build_header(title)
    self.build_base()
    self.build_footer()
    self.show_all()

  def add_style(self, item,style):
    sc = item.get_style_context()
    for sty in style:
      sc.add_class(sty)

  def close_popup(self, button):
    self.destroy()

  def build_header(self,title):
    #header
    title = Gtk.Label(label=title)
    sc = title.get_style_context()
    sc.add_class('text-black-color')
    sc.add_class('font-18')
    sc.add_class('font-bold')
    self.title_bar.pack_start(title,1,1,1)
    self.pin_button = Gtk.Button(width_request = 20)
    self.pin_button.connect('clicked',self.close_popup)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Close.png', 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.pin_button.add(image)
    self.title_bar.pack_end(self.pin_button,0,0,1)
    sc = self.pin_button.get_style_context()
    sc.add_class('exit-button')

  def build_base(self):
    pass

  def build_footer(self):
    pass

#build calendar picker, chart settings popup, time window / range to display,


class PenSettingsPopup(BaseSettingsPopoup):

  def __init__(self, parent,app):
    self.chart_filter = 'All'
    self.unsaved_changes_present = False
    self.unsaved_pen_rows = {}
    self.pen_column_names = ['id', 'chart_id', 'tag_id', 'connection_id', 'visible', 
                      'color', 'weight','scale_minimum','scale_maximum', 
                      'scale_lock', 'scale_auto']
    super().__init__(parent,"Pen Settings",app)
    self.app = app
  
  def build_header(self,title):
    #header
    db_c_num = 'All'
    selections = ['All',"Chart 1",'Chart 2','Chart 3',"Chart 4",'Chart 5','Chart 6',"Chart 7",'Chart 8','Chart 9',
                  "Chart 10",'Chart 11','Chart 12',"Chart 13",'Chart 14','Chart 15','Chart 16']
    self.c_num = Gtk.ComboBoxText()
    self.c_num.set_entry_text_column(0)
    for x in selections:
        self.c_num.append_text(x)
    try:
      idx = selections.index(str(db_c_num))
    except IndexError:
      idx = 0
    self.c_num.set_active(idx)
    sc = self.c_num.get_style_context()
    sc.add_class('ctrl-combo')
    self.c_num.connect("changed", self.filter_disp_chart)
    self.title_bar.pack_start(self.c_num,0,0,1)

    self.add_button = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/AddPen.png', 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.add_button.add(image)
    sc = self.add_button.get_style_context()
    sc.add_class('ctrl-button')
    self.title_bar.pack_start(self.add_button,0,0,0)
    self.add_button.connect('clicked',self.create_new_pen)

    title = Gtk.Label(label=title,width_request = 1000)
    sc = title.get_style_context()
    sc.add_class('text-black-color')
    sc.add_class('font-18')
    sc.add_class('font-bold')
    self.title_bar.pack_start(title,1,1,1)

    self.pin_button = Gtk.Button(width_request = 20)
    self.pin_button.connect('clicked',self.close_popup)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Close.png', 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.pin_button.add(image)
    self.title_bar.pack_end(self.pin_button,0,0,1)
    sc = self.pin_button.get_style_context()
    sc.add_class('exit-button')

  def build_base(self):
    self.db_session = self.app.settings_db.session
    self.db_model = self.app.settings_db.models['pen']
    self.Tbl = self.db_model
    self.pen_settings = []
    self.pen_row_num = 1
    #header = self.db_session.query(self.Tbl).first()
    #self.pen_column_names = header.__table__.columns
    self.pen_grid = Gtk.Grid(column_homogeneous=False,column_spacing=20,row_spacing=10)
    self.base_area.add(self.pen_grid)
    #header
    self.add_column_names()
    self.add_pen_rows(self.chart_filter)
    self.show_all()
  
  def build_footer(self):
    self.ok_button = Gtk.Button(width_request = 100)
    self.ok_button.connect('clicked',self.saveall_pen_rows)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Return.png', 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    box = Gtk.Box()
    lbl = Gtk.Label('OK')
    sc = lbl.get_style_context()
    sc.add_class('font-14')
    sc.add_class('font-bold')
    box.pack_start(lbl,1,1,1)
    box.pack_start(image,0,0,0)
    self.ok_button.add(box)
    self.footer_bar.pack_end(self.ok_button,0,0,1)
    sc = self.ok_button.get_style_context()
    sc.add_class('ctrl-button')

  def filter_disp_chart(self,chart_filter,*args):
    temp = chart_filter.get_active_text()
    val = temp.strip('Chart ')
    self.chart_filter = val
    self.remove_pen_rows()
    self.add_column_names()
    self.add_pen_rows(self.chart_filter)

  def add_column_names(self,*args):
    labels = ['Chart','Enabled','Connection', 'Tag', 'Color',
      'Width', 'Scale Min', 'Scale Max', 'Auto Scale','Lock Scale','Save',''] # may want to create a table in the db for column names
    for l_idx in range(len(labels)):
        l = Gtk.Label(labels[l_idx])
        sc = l.get_style_context()
        sc.add_class('text-black-color')
        sc.add_class('font-14')
        sc.add_class('font-bold')
        self.pen_grid.attach(l, l_idx, 0, 1, 1)

  def create_delete_button(self,pen_id,row,*args):
    self.delete_button = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Delete.png', 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.delete_button.add(image)
    sc = self.delete_button.get_style_context()
    sc.add_class('ctrl-button')
    self.pen_grid.attach(self.delete_button,11,row,1,1)
    self.delete_button.connect('clicked',self.confirm,pen_id)
  
  def delete_row(self,row_id,*args):
    settings = self.db_session.query(self.Tbl).filter(self.Tbl.id == row_id).first()
    self.db_session.query(self.Tbl).filter(self.Tbl.id == row_id).delete()
    self.db_session.commit()
    self.remove_pen_rows()
    self.add_column_names()
    self.add_pen_rows(self.chart_filter)
    self.delete_pen_object(row_id,settings.chart_id)

  def add_pen_rows(self,chart_filter,*args):
    #pen row
    if chart_filter == 'All':
      settings = self.db_session.query(self.Tbl).order_by(self.Tbl.id)
    else:
      settings = self.db_session.query(self.Tbl).filter(self.Tbl.chart_id == int(chart_filter)).order_by(self.Tbl.id) 
    params = {}
    if len(settings.all()) == 0:
      self.pen_grid.set_column_homogeneous(True)
    else:
      self.pen_grid.set_column_homogeneous(False)      
    for pen in settings:
      for c in self.pen_column_names:
        params[c] = getattr(pen, c)
      row = Pen_row(params,self.pen_grid,self.pen_row_num,self.app,self)
      self.create_delete_button(params['id'],self.pen_row_num)
      params.clear()
      self.pen_row_num += 1
      self.pen_settings.append(row)
    self.show_all()

  def remove_pen_rows(self,*args):
    rows = self.pen_grid.get_children()
    for items in rows:
      self.pen_grid.remove(items)
  
  def create_new_pen(self,*args):
    if self.chart_filter == 'All':
      c_id = 1
    else:
      c_id = int(self.chart_filter)
    new = self.Tbl(chart_id = c_id)
    self.db_session.add(new)
    self.db_session.commit()    
    self.db_session.refresh(new)  #Retrieves newly created pen id from the database (new.id)
    self.insert_pen_row()
    self.create_pen_object(new.id,c_id)

  def create_pen_object(self,id,chart_id,*args):
    self.app.charts[chart_id].add_pen(id)
  
  def delete_pen_object(self,id,chart_id,*args):
    self.app.charts[chart_id].delete_pen(id)

  def insert_pen_row(self,*args):
    self.pen_grid.set_column_homogeneous(False) 
    self.pen_grid.insert_row(1)
    last_pen = self.db_session.query(self.Tbl).order_by(self.Tbl.id.desc()).first()
    params = {}
    for c in self.pen_column_names:
      params[c] = getattr(last_pen, c)
    row = Pen_row(params,self.pen_grid,1,self.app,self)
    self.create_delete_button(params['id'],1)
    params.clear()
    self.pen_row_num += 1
    self.pen_settings.append(row)
    self.show_all()

  def confirm(self, button,pen_id,msg="Are you sure you want to delete this pen?", args=[]):
    popup = PopupConfirm(self, msg=msg)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      self.delete_row(pen_id)
      return True
    else:
      return False

  def unsaved_changes(self,status,pen_row,id,*args):
    #This method holds references to pen rows for saveall changes on OK button
    self.unsaved_changes_present = status
    if status:
      self.unsaved_pen_rows[id] = pen_row
    else:
      del self.unsaved_pen_rows[id]

  def saveall_pen_rows(self,*args):
    #when clicking ok button, save all unsaved settings, clear unsaved dictionary, and close popup
    for key,pen_row in self.unsaved_pen_rows.items():
      pen_row.update_db()
    self.unsaved_changes_present = False
    self.unsaved_pen_rows = {}
    self.close_popup(None)

  def close_popup(self, button,msg="Abandon Pen Settings Changes?"):
    if self.unsaved_changes_present:
      popup = PopupConfirm(self, msg=msg)
      response = popup.run()
      popup.destroy()
      if response == Gtk.ResponseType.YES:
        self.destroy()
        return True
      else:
        return False
    else:
      self.destroy()


class Pen_row(object):
  def __init__(self,params,pen_grid,row_num,app,parent,*args):
    self.app = app
    self.parent = parent
    self.db_settings_session = self.app.settings_db.session
    self.db_settings_model = self.app.settings_db.models['pen']
    self.Pen_Settings_Tbl = self.db_settings_model

    self.db_conn_session = self.app.connections_db.session
    self.db_conn_model = self.app.connections_db.models['connections']
    self.Connections_Tbl = self.db_conn_model

    self.db_conn_session = self.app.connections_db.session
    self.db_conn_model = self.app.connections_db.models['tags']
    self.Tags_Tbl = self.db_conn_model

    self.params = params
    self.pen_grid = pen_grid
    self.pen_row_num = row_num
    self.id = self.params['id']
    self.chart_id = self.params['chart_id']
    if self.params['connection_id'] == None:
      self.db_conn_id = 0
    else:
      self.db_conn_id = self.params['connection_id']
    if self.params['tag_id'] == None:
      self.db_tag_id = 0
    else:
      self.db_tag_id = self.params['tag_id']
    self.unsaved_changes = False      #Need to pass this up so that confirm closing popup with unsaved changes
    self.connections_available = {}
    self.tags_available = {}
    self.get_available_connections()
    self.get_available_tags(self.db_conn_id)
    self.build_row()
    #Rows start at 1 because row 0 is titles
    #Grid : Left,Top,Width,Height

  def build_row(self,*args):
    #Chart Select
    db_chart_number = str(self.params['chart_id'])
    selections = []
    for num in range(self.app.charts_number):
      selections.append(str(num+1))
    self.chart_number = Gtk.ComboBoxText(width_request = 20)
    for x in selections:
        self.chart_number.append_text(x)
    try:
      idx = selections.index(str(db_chart_number))
    except IndexError:
      idx = 0
    sc = self.chart_number.get_style_context()
    sc.add_class('ctrl-combo')
    self.chart_number.set_active(idx)
    self.pen_grid.attach(self.chart_number,0,self.pen_row_num,1,1)
    self.chart_number.connect("changed", self.row_changed)

    #Display Status
    db_display_status = bool(self.params['visible'])
    box= Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    wid =CheckBoxWidget(30,30,image,db_display_status)
    self.display_status = wid.return_self()
    sc = self.display_status.get_style_context()
    sc.add_class('check-box')
    box.set_center_widget(self.display_status)
    self.pen_grid.attach(box,1,self.pen_row_num,1,1)
    self.display_status.connect("toggled", self.row_changed)

    #Connection Select
    if self.db_conn_id in self.connections_available.keys():
      params = self.connections_available[self.db_conn_id]
    else:
      params = self.connections_available[0]
    self.conn_select = Gtk.ComboBoxText(width_request = 300)
    for key, val in self.connections_available.items():
      self.conn_select.append_text(val['desc'])
    self.conn_select.set_active(int(params['count']))
    sc = self.conn_select.get_style_context()
    sc.add_class('ctrl-combo')
    self.pen_grid.attach(self.conn_select,2,self.pen_row_num,1,1)
    self.conn_select.connect("changed", self.row_changed)
    self.conn_select.connect("changed",self.new_connection_selelcted)


    #Tag Select
    if self.db_tag_id in self.tags_available.keys():
      params = self.tags_available[self.db_tag_id]
    else:
      params = self.tags_available[0]
    self.tag_select = Gtk.ComboBoxText(hexpand = True)
    for key, val in self.tags_available.items():
      self.tag_select.append_text(val['desc'])
    self.tag_select.set_active(int(params['count']))
    sc = self.tag_select.get_style_context()
    sc.add_class('ctrl-combo')
    self.pen_grid.attach(self.tag_select,3,self.pen_row_num,1,1)
    self.tag_select.connect("changed", self.row_changed)

    #color
    db_color = str(self.params['color']) #example:#0000FF
    rgbcolor = Gdk.RGBA()
    rgbcolor.parse(db_color)
    rgbcolor.to_string()
    self.color_button = Gtk.ColorButton(width_request = 20)
    self.color_button.set_rgba (rgbcolor)
    sc = self.color_button.get_style_context()
    sc.add_class('ctrl-button')
    self.pen_grid.attach(self.color_button,4,self.pen_row_num,1,1)
    self.color_button.connect('color-set',self.row_changed)

    #line width
    db_line_width = str(self.params['weight']) 
    but = Gtk.Button(width_request = 20)
    self.line_width = Gtk.Label()
    self.line_width.set_label(db_line_width)
    self.add_style(self.line_width,['borderless-num-display','font-14','text-black-color'])
    but.add(self.line_width)
    sc = but.get_style_context()
    sc.add_class('ctrl-button')
    but.connect('clicked',self.open_numpad,self.line_width,{'min':0,'max':16,'type':int,'polarity':False})
    self.pen_grid.attach(but,5,self.pen_row_num,1,1)
    but.connect('clicked',self.row_changed)

    #scale minimum
    db_scale_minimum = str(self.params['scale_minimum']) 
    but = Gtk.Button(width_request = 100)
    self.scale_minimum = Gtk.Label()
    self.scale_minimum.set_label(db_scale_minimum)
    self.add_style(self.scale_minimum,['borderless-num-display','font-14','text-black-color'])
    but.add(self.scale_minimum)
    sc = but.get_style_context()
    sc.add_class('ctrl-button')
    but.connect('clicked',self.open_numpad,self.scale_minimum,{'min':-32768,'max':32768,'type':float,'polarity':True})
    self.pen_grid.attach(but,6,self.pen_row_num,1,1)
    but.connect('clicked',self.row_changed)


    #scale maximum
    db_scale_maximum = str(self.params['scale_maximum']) 
    but = Gtk.Button(width_request = 100)
    self.scale_maximum = Gtk.Label()
    self.scale_maximum.set_label(db_scale_maximum)
    self.add_style(self.scale_maximum,['borderless-num-display','font-14','text-black-color'])
    but.add(self.scale_maximum)
    sc = but.get_style_context()
    sc.add_class('ctrl-button')
    but.connect('clicked',self.open_numpad,self.scale_maximum,{'min':-32768,'max':32768,'type':float,'polarity':True})
    self.pen_grid.attach(but,7,self.pen_row_num,1,1)
    but.connect('clicked',self.row_changed)

    #Autoscale Status
    db_autoscale_status = bool(self.params['scale_auto'])
    box= Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    wid =CheckBoxWidget(30,30,image,db_autoscale_status)
    self.autoscale_status = wid.return_self()
    sc = self.autoscale_status.get_style_context()
    sc.add_class('check-box')
    box.set_center_widget(self.autoscale_status)
    self.pen_grid.attach(box,8,self.pen_row_num,1,1)
    self.autoscale_status.connect("toggled", self.row_changed)

    #Lockscale Status
    db_lockscale_status = bool(self.params['scale_lock'])
    box= Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    wid =CheckBoxWidget(30,30,image,db_lockscale_status)
    self.lockscale_status = wid.return_self()
    sc = self.lockscale_status.get_style_context()
    sc.add_class('check-box')
    box.set_center_widget(self.lockscale_status)
    self.pen_grid.attach(box,9,self.pen_row_num,1,1)
    self.lockscale_status.connect("toggled", self.row_changed)

    #Save Button
    self.save_button = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Save.png', 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.save_button.add(image)
    sc = self.save_button.get_style_context()
    sc.add_class('ctrl-button')
    self.pen_grid.attach(self.save_button,10,self.pen_row_num,1,1)
    self.save_button.connect('clicked',self.save_settings)
    
  def open_numpad(self,button,widget_obj,params,*args):
    numpad = ValueEnter(self,widget_obj,params)
    response = numpad.run()
    if response == Gtk.ResponseType.NO:
      pass
    else:
      pass
      #callback(args)
    numpad.destroy()
  
  def row_changed(self,*args):
    self.add_style(self.save_button,['exit-button'])
    self.parent.unsaved_changes(True,self,self.id)
  
  def row_updated(self,*args):
    self.add_style(self.save_button,['ctrl-button'])
    self.parent.unsaved_changes(False,self,self.id)

  def new_connection_selelcted(self, *args):
    pass
    c_temp = self.conn_select.get_active_text()
    id = 0
    for key, val in self.connections_available.items():
      if val['desc'] == c_temp:
        id = int(val['id'])
    self.db_conn_id = id
    self.get_available_tags(self.db_conn_id)
    self.tag_select.remove_all()
    for key, val in self.tags_available.items():
      self.tag_select.append_text(val['desc'])
    self.tag_select.set_active(0)
  
  def save_settings(self,button,*args):
    self.update_db()
    self.row_updated()

  def update_db(self,*args):
    p_settings = {}
    p_settings['id'] = self.id
    settings = self.db_settings_session.query(self.Pen_Settings_Tbl).filter(self.Pen_Settings_Tbl.id == self.id).first()  # save the current settings
    if settings:
      chart_id= int(self.chart_number.get_active_text())
      settings.chart_id = chart_id
      p_settings['chart_id'] = chart_id

      #search list to match tag name with id number
      t_temp = self.tag_select.get_active_text()
      t_id = 0
      for key, val in self.tags_available.items():
        if val['desc'] == t_temp:
          t_id = int(val['id'])
      settings.tag_id = t_id
      p_settings['tag_id'] = t_id

      #search list to match connection name with id number
      c_temp = self.conn_select.get_active_text()
      c_id = 0
      for key, val in self.connections_available.items():
        if val['desc'] == c_temp:
          c_id = int(val['id'])
      settings.connection_id = c_id
      p_settings['connection_id'] = c_id

      visible = int(self.display_status.get_active())
      settings.visible = visible
      p_settings['visible'] = visible

      weight = self.line_width.get_label()
      settings.weight = weight
      p_settings['weight'] = weight

      rgba_color = self.color_button.get_rgba()
      red = int(rgba_color.red*255)
      green = int(rgba_color.green*255)
      blue = int(rgba_color.blue*255)
      hex_color =  '#{r:02x}{g:02x}{b:02x}'.format(r=red,g=green,b=blue)
      settings.color = hex_color
      p_settings['color'] = hex_color
      
      minimum = self.scale_minimum.get_label()
      settings.scale_minimum = minimum
      p_settings['scale_minimum'] = minimum

      maximum = self.scale_maximum.get_label()
      settings.scale_maximum = maximum
      p_settings['scale_maximum'] = maximum

      lock = int(self.lockscale_status.get_active())
      settings.scale_lock = lock
      p_settings['scale_lock'] = lock

      auto = int(self.autoscale_status.get_active())
      settings.scale_auto = auto
      p_settings['scale_auto'] = auto


    self.db_settings_session.commit()
    self.update_pen_object(p_settings)

  def update_pen_object(self,p_settings,*args):
    self.app.charts[self.chart_id].pens[self.id]._chart_id = p_settings['chart_id']
    self.app.charts[self.chart_id].pens[self.id]._tag_id = p_settings['tag_id']
    self.app.charts[self.chart_id].pens[self.id]._connection_id = p_settings['connection_id']
    self.app.charts[self.chart_id].pens[self.id]._visible = p_settings['visible']
    self.app.charts[self.chart_id].pens[self.id]._weight = p_settings['weight']
    self.app.charts[self.chart_id].pens[self.id]._color = p_settings['color']
    self.app.charts[self.chart_id].pens[self.id]._scale_minimum = p_settings['scale_minimum']
    self.app.charts[self.chart_id].pens[self.id]._scale_maximum = p_settings['scale_maximum']
    self.app.charts[self.chart_id].pens[self.id]._scale_lock = p_settings['scale_lock']
    self.app.charts[self.chart_id].pens[self.id]._scale_auto = p_settings['scale_auto']
    p_obj = self.app.charts[self.chart_id].pens[self.id]
    #print(p_obj)
    #print(self.app.charts[self.chart_id].pens)
    #print(self.app.charts[p_settings['chart_id']].pens)

    if p_settings['chart_id'] != self.chart_id:
      #chart ID was changed so need to move pen object into other chart object
      self.app.charts[p_settings['chart_id']].pens[self.id] = p_obj
      del self.app.charts[self.chart_id].pens[self.id]
      #print(self.app.charts[self.chart_id].pens)
      #print(self.app.charts[p_settings['chart_id']].pens)
  
  def add_style(self, item,style):
    sc = item.get_style_context()
    for items in sc.list_classes():
      #remove all default styles
      sc.remove_class(items)
    for sty in style:
      #add new styles
      sc.add_class(sty)

  def get_available_connections(self,*args):
    connections = self.db_conn_session.query(self.Connections_Tbl).order_by(self.Connections_Tbl.id)
    self.connections_available = {0:{'id':0,'type':0,'desc':"","count":0}}
    d = {}
    count = 1
    for con in connections:
        d['id'] = con.id
        d['type'] = con.connection_type
        d['desc'] = con.description
        d['count'] = count
        self.connections_available[int(con.id)] = d
        d = {}
        count += 1

  def get_available_tags(self,c_id,*args):
    tags = self.db_conn_session.query(self.Tags_Tbl).filter(self.Tags_Tbl.connection_id == int(c_id)).order_by(self.Tags_Tbl.id)
    self.tags_available = {0:{'id':0,'type':0,'desc':"","count":0}}
    d = {}
    count = 1
    for tag in tags:
        d['id'] = tag.id
        d['c_id'] = tag.connection_id
        d['desc'] = tag.description
        d['datatype'] = tag.datatype
        d['count'] = count
        self.tags_available[int(tag.id)] = d
        d = {}
        count += 1
  

class PointSettingsPopup(BaseSettingsPopoup):

  def __init__(self, parent):
      super().__init__(parent, "Point Settings")


class ConnectionSettingsPopup(BaseSettingsPopoup):

  def __init__(self, parent):
      super().__init__(parent, "Connection Settings")


class ValueEnter(Gtk.Dialog):
  #Need to add check for value exceeding min,max range based on type
  def __init__(self, parent,obj,params):
    super().__init__(flags=0) 

    self.widget_obj = obj
    self.first_key_pressed = False #the user hasn't typed anything yet
    self.lbl = "Numpad"
    self.min = params['min']  #minimum value acceptable
    self.max = params['max']  #maximum value acceptable
    self.num_polarity = params['polarity']#whether value can be +/-
    self.num_type = params['type']  #whether number is int or float
    self.initial_value = 0
    self.set_default_size(600, 400)
    self.set_border_width(10)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.set_keep_above(True)
    self.set_decorated(False)
    self.content_area = self.get_content_area()

    self.dialog_window = Gtk.Box(width_request=600,orientation=Gtk.Orientation.VERTICAL)
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=600)

    #header
    title = Gtk.Label(label=self.lbl)
    sc = title.get_style_context()
    sc.add_class('text-black-color')
    sc.add_class('font-18')
    sc.add_class('font-bold')
    self.title_bar.pack_start(title,1,1,1)
    self.pin_button = Gtk.Button(width_request = 20)
    self.pin_button.connect('clicked',self.close_popup)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Close.png', 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.pin_button.add(image)
    self.title_bar.pack_end(self.pin_button,0,0,1)
    sc = self.pin_button.get_style_context()
    sc.add_class('exit-button')
    self.dialog_window.pack_start(self.title_bar,0,0,1)
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    #self.dialog_window.pack_start(divider,0,0,1)
    self.content_area.add(self.dialog_window )
    self.build_base()
    self.show_all()

  def build_base(self,*args):
    grid = Gtk.Grid(column_spacing=4, row_spacing=4, column_homogeneous=True, row_homogeneous=True,)
    pop_lbl = Gtk.Label("{}".format(self.lbl))
    self.add_style(pop_lbl,['borderless-num-display','font-14','text-black-color'])
    grid.attach(pop_lbl,0,0,2,1)
    self.dialog_window.pack_start(grid,1,1,1)
    sep = Gtk.Label(height_request=3)
    self.dialog_window.pack_start(sep,1,1,1)

    try:
      if isinstance(self.widget_obj, Gtk.Label):
        value = self.num_type(self.widget_obj.get_label())
      if isinstance(self.widget_obj, Gtk.Entry):
        value = self.num_type(self.widget_obj.get_text())
      self.initial_value = value
    except ValueError:
      value = 0

    #value = 0
    self.val_label = Gtk.Label(str(value))
    self.add_style(self.val_label,['numpad-display','font-16'])
    grid.attach(self.val_label,2,0,1,1)
    min_str = "-"+chr(0x221e) if type(self.min) == type(None) else self.min
    max_str = chr(0x221e) if type(self.max) == type(None) else self.max
    min_max_lbl = Gtk.Label(u"({} ~ {})".format(min_str, max_str))
    self.add_style(min_max_lbl,['font-14'])
    grid.attach(min_max_lbl,3,0,1,1)
    key = []
    for k in range(10):
      b = Gtk.Button(str(k), can_focus=False, can_default=False)
      #b.get_style_context().add_class("keypad_key")
      b.connect("clicked", self.btn_pressed)
      key.append(b)
      self.add_style(b,['numpad-bg','keypad_key'])
    grid.attach(key[7],0,2,1,1)
    grid.attach(key[8],1,2,1,1)
    grid.attach(key[9],2,2,1,1)
  
    grid.attach(key[4],0,3,1,1)
    grid.attach(key[5],1,3,1,1)
    grid.attach(key[6],2,3,1,1)

    grid.attach(key[1],0,4,1,1)
    grid.attach(key[2],1,4,1,1)
    grid.attach(key[3],2,4,1,1)

    grid.attach(key[0],0,5,2,1)

    period_key = Gtk.Button(".", can_focus=False, can_default=False)
    period_key.connect("clicked", self.add_period)
    self.add_style(period_key,['numpad-bg','keypad_key'])
    if self.num_type == float:
      grid.attach(period_key,2,5,1,1)

    PM_key = Gtk.Button("+/-")
    PM_key.connect("clicked", self.add_plus_minus)
    self.add_style(PM_key,['numpad-bg','keypad_key'])
    if self.num_polarity:
      grid.attach(PM_key,3,5,1,1)
    
    clear_key = Gtk.Button("CLEAR", can_focus=False, can_default=False)
    clear_key.connect("clicked", self.init_val)
    self.add_style(clear_key,['numpad-cmd-bg','keypad_enter'])
    grid.attach(clear_key,3,2,1,1)

    delete_key = Gtk.Button("DEL", can_focus=False, can_default=False)
    delete_key.connect("clicked", self.del_num)
    self.add_style(delete_key,['numpad-cmd-bg','keypad_enter'])
    grid.attach(delete_key,3,3,1,1)

    enter_key = Gtk.Button("ENTER", can_focus=False, can_default=False)
    enter_key.connect("clicked", self.accept_val)
    self.add_style(enter_key,['numpad-cmd-bg','keypad_enter'])
    grid.attach(enter_key,3,4,1,1)


    self.signals = []
    self.signals.append(self.connect('key-release-event', self.key_pressed))
    self.show_all()

    #Add style to dialog buttons
    a = self.get_action_area()
    b = a.get_children()
    for but in b:
      self.add_style(but,['dialog-buttons','font-16'])

  def key_pressed(self, popup, key_event):
    if key_event.get_keycode().keycode == 13:#Enter
      self.accept_val(None)
    if key_event.get_keycode().keycode == 8:#Backspace
      self.first_key_pressed = True #they want to use the number in there
      self.del_num(None)
    elif key_event.string == "-" or key_event.string == "+":
      self.add_plus_minus(None)
    elif key_event.string in "0123456789" and len(key_event.string)==1:
      self.update_val(key_event.string)
    elif key_event.string == ".":
      self.add_period(None)
    else:
      pass

  def add_style(self, item,style):
    sc = item.get_style_context()
    for sty in style:
      sc.add_class(sty)


  def btn_pressed(self, key):
    num = int(key.get_label())
    self.update_val(num)

  def update_val(self, num):
    if not self.first_key_pressed:
      val = str(num)
      self.first_key_pressed = True
    else:
      old_val = self.val_label.get_text()
      if old_val == '0':
        val = str(num)
      else:
        val = old_val+str(num)
    
    
    if self.check_limits(val):
      self.val_label.set_text(val)
  
  def check_limits(self, val):
    try:
      val = float(val)
    except ValueError:
      return False
    if not type(self.min) == type(None) and val < self.min:
      return False    
    if not type(self.max) == type(None) and val > self.max:
      return False
    return True
  
  def init_val(self, key):
    self.val_label.set_text('')
  
  def del_num(self,*args):
    val = self.val_label.get_text()
    val = (val)[:-1]
    if not val:
      val = '0'
    self.val_label.set_text(val)

  def add_period(self,*args):
    if not self.first_key_pressed:
      self.update_val("0")
    val = self.val_label.get_text()
    if "." not in val:
      val = val+"."
      self.val_label.set_text(val)

  def add_plus_minus(self,*args):
    val = self.val_label.get_text()
    if "-" not in val:
      val = "-"+val
    else:
      val = val.replace('-',"")
    if self.check_limits(val):
      self.val_label.set_text(val)

  def cleanup(self):
    for signal in self.signals:
      self.disconnect(signal)

  def accept_val(self, key):
    self.cleanup()
    try:
      if isinstance(self.widget_obj, Gtk.Label):
        self.widget_obj.set_label((self.val_label.get_text()))
        value = self.val_label.get_text()
      if isinstance(self.widget_obj, Gtk.Entry):
        self.widget_obj.set_text(str(self.val_label.get_text()))
        value = self.val_label.get_text()
      else:
        value = 0
    except ValueError:
      value = 0
      pass
    self.destroy()
    if str(self.initial_value) != str(value):
      pass
    else:
      pass

  def close_popup(self, button):
    self.destroy()


class PopupConfirm(Gtk.Dialog):
  def __init__(self, parent, msg='Do you really want to do this?'):
      Gtk.Dialog.__init__(self, "Confirm?", parent, Gtk.DialogFlags.MODAL,
                          (Gtk.STOCK_YES, Gtk.ResponseType.YES,
                            Gtk.STOCK_NO, Gtk.ResponseType.NO)
                          )
      self.set_default_size(300, 200)
      self.set_border_width(10)
      sc = self.get_style_context()
      sc.add_class("dialog-border")
      self.set_keep_above(True)
      self.set_decorated(False)
      box = Gtk.Box()
      box.set_spacing(10)
      box.set_orientation(Gtk.Orientation.VERTICAL)
      c = self.get_content_area()
      c.add(box)
      box.pack_start(Gtk.Image(stock=Gtk.STOCK_DIALOG_WARNING), 0, 0, 0)
      confirm_msg = Gtk.Label(msg + '\n\n')
      sc = confirm_msg.get_style_context()
      sc.add_class('borderless-num-display')
      sc.add_class('text-black-color')
      sc.add_class('font-20')
      box.pack_start(confirm_msg, 0, 0, 0)
      sep = Gtk.Label(height_request=3)
      c.pack_start(sep,1,1,1)
      self.show_all()
      #Add style to dialog buttons
      a = self.get_action_area()
      b = a.get_children()
      for but in b:
        sc = but.get_style_context()
        sc.add_class("dialog-buttons")
        sc.add_class("font-16")