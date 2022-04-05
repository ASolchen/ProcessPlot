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

from logging.config import valid_ident
from pkgutil import iter_modules

from urllib.parse import non_hierarchical
import gi, os, json

from ProcessLink.process_link import process_link
from numpy import maximum, nonzero
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
#build popup for chart settings


class PenSettingsPopup(BaseSettingsPopoup):

  def __init__(self, parent,app):
    self.app = app
    self.chart_filter = 'All'
    self.unsaved_changes_present = False
    self.unsaved_pen_rows = {}
    self.pen_column_names = ['id', 'chart_id', 'tag_id', 'connection_id', 'visible', 
                      'color', 'weight','scale_minimum','scale_maximum', 
                      'scale_lock', 'scale_auto']
    self.db_session = self.app.settings_db.session
    self.db_model = self.app.settings_db.models['pen']
    self.Tbl = self.db_model
    super().__init__(parent,"Pen Settings",app)


  
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
    db_conx = str(self.params['connection_id'])
    self.conn_select = Gtk.ComboBoxText(width_request = 200, halign = Gtk.Align.CENTER )
    i = 0
    for key, val in self.connections_available.items():
      self.conn_select.append_text(val['id'])
      if val['id'] == db_conx:
        i = key
    self.conn_select.set_active(i)
    sc = self.conn_select.get_style_context()
    sc.add_class('ctrl-combo')
    self.pen_grid.attach(self.conn_select,2,self.pen_row_num,1,1)
    self.conn_select.connect("changed", self.row_changed)
    self.conn_select.connect("changed",self.new_connection_selelcted)

    #Tag Select
    db_tag = str(self.params['tag_id'])
    i = 0
    self.tag_select = Gtk.ComboBoxText(hexpand = True)
    for key, val in self.tags_available.items():
      self.tag_select.append_text(val['id'])
      if val['id'] == db_tag:
        i = key
    self.tag_select.set_active(i)
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
    c_temp = self.conn_select.get_active_text()
    id = ''
    for key, val in self.connections_available.items():
      if val['id'] == c_temp:
        id = str(val['id'])
    self.db_conn_id = id
    self.get_available_tags(self.db_conn_id)
    self.tag_select.remove_all()
    for key, val in self.tags_available.items():
      self.tag_select.append_text(val['id'])
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

      #get tag ID
      t_id = self.tag_select.get_active_text()
      settings.tag_id = t_id
      p_settings['tag_id'] = t_id

      #get connection ID
      c_id = self.conn_select.get_active_text()
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

    if p_settings['chart_id'] != self.chart_id:
      #chart ID was changed so need to move pen object into other chart object
      self.app.charts[p_settings['chart_id']].pens[self.id] = p_obj
      del self.app.charts[self.chart_id].pens[self.id]
  
  def add_style(self, item,style):
    sc = item.get_style_context()
    for items in sc.list_classes():
      #remove all default styles
      sc.remove_class(items)
    for sty in style:
      #add new styles
      sc.add_class(sty)

  def get_available_connections(self,*args):

    conx_items = ['id', 'connection_type', 'description']
    new_params = {}
    count = 1
    self.connections_available = {0: {'id': '', 'connection_type': 0, 'description': ''}}
    for conx_id,conx_obj in self.app.link.get('connections').items():
      for c in conx_items:
        new_params[c] = getattr(conx_obj, c)
      self.connections_available[count] = new_params
      new_params = {}
      count += 1

  def get_available_tags(self,c_id,*args):
    tag_items = ['id', 'connection_id', 'description','datatype','tag_type']
    new_params = {}
    count = 1
    self.tags_available = {0: {'id': '', 'datatype': 0, 'description': '','c_id':None}}
    conx_obj = self.app.link.get("connections").get(c_id)
    for tag_id,tag_obj in conx_obj.get('tags').items():
      for c in tag_items:
        new_params[c] = getattr(tag_obj, c)
      self.tags_available[count] = new_params
      new_params = {}
      count += 1


class TagMainPopup(Gtk.Dialog):

  def __init__(self, parent,app):
    super().__init__(transient_for = parent,flags=0) 
    self.unsaved_changes_present = False
    self.unsaved_conn_rows = {}
    self.tags_available = {}
    self.connections_available = {}
    self.app = app
    self.set_default_size(1050, 800)
    self.set_decorated(False)
    self.set_border_width(10)
    self.set_keep_above(False)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.content_area = self.get_content_area()
    self.get_available_tags('c_id')
    self.get_available_connections()
    self.tag_filter_val = ''

    self.dialog_window = Gtk.Box(width_request=800,orientation=Gtk.Orientation.VERTICAL)
    self.content_area.add(self.dialog_window)
    ### -title bar- ####
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=1050)
    self.dialog_window.pack_start(self.title_bar,0,0,1)
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    ### -content area- ####
    self.base_area = Gtk.Box(spacing = 10,orientation=Gtk.Orientation.VERTICAL,margin = 20)
    self.scroll = Gtk.ScrolledWindow(width_request = 850,height_request = 600)
    self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    self.scroll.add(self.base_area)
    self.dialog_window.pack_start(self.scroll,1,1,1)
    ### -footer- ####
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    self.footer_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=800)
    self.dialog_window.pack_start(self.footer_bar,0,0,1)

    self.build_header("Tag Browser")
    self.build_base()
    self.build_footer()
    self.show_all()

  def build_header(self,title):
    #header
    self.tag_sort = Gtk.ComboBoxText()
    self.tag_sort.set_entry_text_column(0)
    for x in self.connections_available:
      self.tag_sort.append_text(self.connections_available[x]['id'])
    self.tag_sort.set_active(0)
    sc = self.tag_sort.get_style_context()
    sc.add_class('ctrl-combo')
    self.tag_sort.connect("changed", self.filter_tags)
    self.title_bar.pack_start(self.tag_sort,0,0,1)
    self.add_button2 = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/AddTag.png', 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.add_button2.add(image)
    sc = self.add_button2.get_style_context()
    sc.add_class('ctrl-button')
    self.title_bar.pack_start(self.add_button2,0,0,0)
    self.add_button2.connect('clicked',self.add_tag_popup,None,self.connections_available)

    title = Gtk.Label(label=title,width_request = 500)
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
    self.connection_settings = []
    self.row_num = 1
    self.grid = Gtk.Grid(column_homogeneous=False,column_spacing=2,row_spacing=2)
    self.grid.set_name('tag_grid_css')
    #self.base_area.add(self.grid)
    self.listbox = Gtk.ListBox(halign =Gtk.Align.FILL,valign = Gtk.Align.FILL)
    self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
    self.add_style(self.listbox,['config-list-box'])
    #self.base_area.add(self.listbox)

#######################
    tag_icon = GdkPixbuf.Pixbuf.new_from_file_at_size('./ProcessPlot/Public/images/Tag.png', 20, 20)
    settings_icon = GdkPixbuf.Pixbuf.new_from_file_at_size('./ProcessPlot/Public/images/settings.png', 20, 20)
    delete_icon = GdkPixbuf.Pixbuf.new_from_file_at_size('./ProcessPlot/Public/images/Delete.png', 20, 20)
    
    self.liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str , str, str , str,GdkPixbuf.Pixbuf,GdkPixbuf.Pixbuf)
    self.treeview = Gtk.TreeView(self.liststore)
    self.treeview.connect('button-press-event' , self.tree_item_clicked)

    self.tvcolumn = Gtk.TreeViewColumn('')
    self.tvcolumn1 = Gtk.TreeViewColumn('Tagname')
    self.tvcolumn2 = Gtk.TreeViewColumn('Connection')
    self.tvcolumn3 = Gtk.TreeViewColumn('Address')
    self.tvcolumn4 = Gtk.TreeViewColumn('Description')
    self.tvcolumn_settings = Gtk.TreeViewColumn('')
    self.tvcolumn_delete = Gtk.TreeViewColumn('')

    # the background
    self.liststore.append([tag_icon,'icon', 'Open Big File','Open Bigger File', 'Open Biggest File',settings_icon,delete_icon])
    self.liststore.append([tag_icon,'icon2', 'Open Big File2','Open Bigger File2', 'Open Biggest File2',settings_icon,delete_icon])
    self.liststore.append([tag_icon,'icon3', 'Open Big File3','Open Bigger File3', 'Open Biggest File3',settings_icon,delete_icon])
    self.liststore.insert(0, [tag_icon,'icon4', 'Open Big File4','Open Bigger File4', 'Open Biggest File4',settings_icon,delete_icon])

    # make treeview searchable
    self.treeview.set_search_column(2)

    # Allow sorting on the column
    self.tvcolumn.set_sort_column_id(2)

    # Allow drag and drop reordering of rows
    self.treeview.set_reorderable(True)

    # add columns to treeview
    self.treeview.append_column(self.tvcolumn)
    self.treeview.append_column(self.tvcolumn1)
    self.treeview.append_column(self.tvcolumn2)
    self.treeview.append_column(self.tvcolumn3)
    self.treeview.append_column(self.tvcolumn4)
    self.treeview.append_column(self.tvcolumn_settings)
    self.treeview.append_column(self.tvcolumn_delete)

    # create a CellRenderers to render the data
    self.cellpb = Gtk.CellRendererPixbuf()
    self.cell1 = Gtk.CellRendererText()
    self.cell2 = Gtk.CellRendererText()
    self.cell3 = Gtk.CellRendererText()
    self.cell4 = Gtk.CellRendererText()
    self.cell_settings = Gtk.CellRendererPixbuf()
    self.cell_delete = Gtk.CellRendererPixbuf()

    # add the cells to the columns - 2 in the first
    self.tvcolumn.pack_start(self.cellpb, False)
    self.tvcolumn1.pack_start(self.cell1, True)
    self.tvcolumn2.pack_start(self.cell2, True)
    self.tvcolumn3.pack_start(self.cell3, True)
    self.tvcolumn4.pack_start(self.cell4, True)
    self.tvcolumn_settings.pack_end(self.cell_settings, False)
    self.tvcolumn_delete.pack_end(self.cell_delete, False)

    self.tvcolumn.set_attributes(self.cellpb,pixbuf=0)
    self.tvcolumn.set_max_width(30)
    self.tvcolumn1.set_attributes(self.cell1, text=1)
    self.tvcolumn1.set_expand(True)
    self.tvcolumn2.set_attributes(self.cell2, text=2)
    self.tvcolumn2.set_expand(True)
    self.tvcolumn3.set_attributes(self.cell3, text=3)
    self.tvcolumn3.set_expand(True)
    self.tvcolumn4.set_attributes(self.cell4, text=4)
    self.tvcolumn4.set_expand(True)
    self.tvcolumn_settings.set_attributes(self.cell_settings,pixbuf=5)
    self.tvcolumn_settings.set_max_width(30)
    self.tvcolumn_delete.set_attributes(self.cell_delete,pixbuf=6)
    self.tvcolumn_delete.set_max_width(30)
    self.base_area.add(self.treeview)

    #header
    self.add_column_names()
    self.add_tag_rows(self.tag_filter_val)
    self.show_all()

  def tree_item_clicked(self, treeview, event):
    pthinfo = treeview.get_path_at_pos(event.x, event.y)
    if event.button == 1: #left click
      if pthinfo != None:
        path,column,cellx,celly = pthinfo
        treeview.grab_focus()
        treeview.set_cursor(path,column,0)
        print(column.get_title())
        #update currently active display
        selection = treeview.get_selection()
        tree_model, tree_iter = selection.get_selected()
        #If selected column is delete icon then initial delete of tag
        if column is self.tvcolumn_delete:
          if tree_iter != None:
            self.liststore.remove(tree_iter)
      else:
        #unselect row in treeview
        selection = treeview.get_selection()
        selection.unselect_all()
    elif event.button == 3: #right click
      if pthinfo != None:
        path,col,cellx,celly = pthinfo
        treeview.grab_focus()
        treeview.set_cursor(path,col,0)
        rect = Gdk.Rectangle()
        rect.x = event.x
        rect.y = event.y + 10
        rect.width = rect.height = 1
        selection = treeview.get_selection()
        tree_model, tree_iter = selection.get_selected()
        popover = Gtk.Popover(width_request = 200)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if tree_iter is not None:
          #gathers the Tag name/Connection column text in the row clicked on
          t_id = tree_model[tree_iter][1]
          c_id = tree_model[tree_iter][2]
          print('Tagname',t_id,c_id)
          #popover to add display
          edit_btn = Gtk.ModelButton(label="Edit", name=t_id)
          #cb = lambda btn: self.open_widget_popup(btn)
          #edit_btn.connect("clicked", cb)
          vbox.pack_start(edit_btn, False, True, 10)
          delete_btn = Gtk.ModelButton(label="Delete", name=t_id)
          #cb = lambda btn: self.open_widget_popup(btn)
          #delete_btn.connect("clicked", cb)
          vbox.pack_start(delete_btn, False, True, 10)
        popover.add(vbox)
        popover.set_position(Gtk.PositionType.RIGHT)
        popover.set_relative_to(treeview)
        popover.set_pointing_to(rect)
        popover.show_all()
        sc = popover.get_style_context()
        sc.add_class('popover-bg')
        sc.add_class('font-16')
        return
      else:
        return
    selection = treeview.get_selection()
    tree_model, tree_iter = selection.get_selected()

  def build_footer(self):
    self.ok_button = Gtk.Button(width_request = 100)
    self.ok_button.connect('clicked',self.close_popup)
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

  def add_tag_rows(self,filter,*args):
    even_row = False
    for tags in self.tags_available:
      for tag in self.tags_available[tags]:
        conx_id = tags
        if filter == '' or filter == conx_id:
          TagsListRow(self.tags_available[tags][tag],self.listbox,self.row_num,self.app,self,conx_id,even_row)
          if even_row:
            even_row = False
          else:
            even_row = True
    self.show_all()


    # for tags in self.tags_available:
    #   for tag in self.tags_available[tags]:
    #     conx_id = tags
    #     if filter == '' or filter == conx_id:
    #       row = Tag_row(self.tags_available[tags][tag],self.grid,self.row_num,self.app,self,conx_id)
    #       self.create_delete_button(self.tags_available[tags][tag]['id'],conx_id,self.row_num)
    #     self.row_num += 1
    #   #self.connection_settings.append(row)
    # self.show_all()
    # #Spaces out column headers when no data available
    # if len(self.tags_available) <= 1:
    #   self.grid.set_column_homogeneous(True)
    # else:
    #   self.grid.set_column_homogeneous(False)

  def add_column_names(self,*args):
    labels = ['','Tag Name', 'Connection', 'Description','Address','',''] # may want to create a table in the db for column names
    for l_idx in range(len(labels)):
        l = Gtk.Label(labels[l_idx])
        sc = l.get_style_context()
        sc.add_class('text-black-color')
        sc.add_class('font-14')
        sc.add_class('font-bold')
        #self.grid.attach(l, l_idx, 0, 1, 1)
    l_row = Gtk.ListBoxRow()
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, height_request = 30)
    l_row.add(hbox)
    for l in labels:
      if l == '':
        lbl = Gtk.Label(label=l, xalign=0.5, yalign = 0.5, width_request = 20)
      else:     
        lbl = Gtk.Label(label=l, xalign=0.5, yalign = 0.5, width_request = 175)         
      hbox.pack_start(lbl, True, True, 0)
      self.add_style(lbl,['font-16','font-bold','text-black-color'])
    self.listbox.add(l_row)

  def get_available_tags(self,c_id,*args):
    self.tags_available = {}
    new_params = {}
    count = 1
    self.conx_tags = {}
    for conx_id,conx_obj in self.app.link.get('connections').items():
      tag_items = conx_obj.return_tag_parameters()  #return list of tag parameters from the specific connection
      for tag_id,tag_obj in conx_obj.get('tags').items():
        for c in tag_items:
          new_params[c] = getattr(tag_obj, c)
        self.conx_tags[count] = new_params
        new_params = {}
        count += 1
      self.tags_available[conx_id]= self.conx_tags
      self.conx_tags = {}
      count = 1

  def get_available_connections(self,*args):

    conx_items = ['id', 'connection_type', 'description']
    new_params = {}
    count = 1
    self.connections_available = {0: {'id': '', 'connection_type': 0, 'description': ''}}
    for conx_id,conx_obj in self.app.link.get('connections').items():
      for c in conx_items:
        new_params[c] = getattr(conx_obj, c)
      self.connections_available[count] = new_params
      new_params = {}
      count += 1

  # def create_delete_button(self,tag_id,conx_id,row,*args):
  #   self.delete_button = Gtk.Button(width_request = 20)
  #   p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Delete.png', 20, -1, True)
  #   image = Gtk.Image(pixbuf=p_buf)
  #   self.delete_button.add(image)
  #   sc = self.delete_button.get_style_context()
  #   sc.add_class('ctrl-button')
  #   self.grid.attach(self.delete_button,5,row,1,1)
  #   self.delete_button.connect('clicked',self.confirm_delete,tag_id,conx_id)

  def filter_tags(self,*args):
    self.tag_filter_val = self.tag_sort.get_active_text()
    self.remove_all_rows()
    #self.add_column_names()
    self.add_tag_rows(self.tag_filter_val)

  def remove_all_rows(self,*args):
    rows = self.listbox.get_children()
    for row in rows:
      self.listbox.remove(row)

  def delete_row(self,t_id,c_id,*args):
    conx_obj = self.app.link.get("connections").get(c_id)
    if conx_obj != None:
      tag_obj = conx_obj.get('tags').get(t_id)
      self.app.link.delete_tag(tag_obj,t_id,c_id)
    #self.remove_all_rows()
    #self.add_column_names()
    #self.get_available_tags('c_id')
    #self.add_tag_rows(self.tag_filter_val)
    self.show_all()

  def confirm_delete(self, button,tag_id,conx_id,row,msg="Are you sure you want to delete this tag?", args=[]):
    popup = PopupConfirm(self, msg=msg)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      self.delete_row(tag_id,conx_id)
      self.listbox.remove(row)
      return True
    else:
      return False

  def add_tag_popup(self,button,duplicate_name_params,*args):
    popup = AddTagPopup(self,duplicate_name_params,self.connections_available)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      results = (popup.get_result())
      self.check_duplicate_name(results)
      return True
    else:
      return False

  def get_tag_params(self,tag_id,conx_id):
    new_params = {}
    conx_obj = self.app.link.get("connections").get(conx_id)
    if conx_obj != None:
      tag_items = conx_obj.return_tag_parameters()  #return list of tag parameters from the specific connection
      tag_obj = conx_obj.get('tags').get(tag_id)
      if tag_obj != None:
        for c in tag_items:
          new_params[c] = getattr(tag_obj, c)
        return new_params

  def check_duplicate_name(self,results,*args):
    dup = False
    conx_obj = self.app.link.get('connections').get(results['connection_id'])
    if conx_obj != None:
      for tag_id,tag_obj in conx_obj.get('tags').items():
          if tag_id == results['id']:
            dup = True
    if dup:
      self.add_tag_popup(None,results,self.connections_available)
    else:
      self.create_tag(results)
      self.open_settings_popup(results['id'],results['connection_id'])

  def open_settings_popup(self,tag_id,conx_id,*args):
    params = self.get_tag_params(tag_id,conx_id)
    popup = TagSettingsPopup(self,params)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      results = (popup.get_result())
      self.update_tag(results)
      return True
    else:
      return False

  def create_tag(self,params,*args):
    #sNEED TO HAVE IT PASS IN SOMEThing FOR THE ADDRESS EXCEPT 12
    conx_obj = self.app.link.get('connections').get(params['connection_id'])
    conx_obj.new_tag({"id": params['id'],
                            "connection_id": params['connection_id'],
                            "description": params['description'],
                            "datatype": params['datatype'],
                            "address": 12
    })
    tag_obj = conx_obj.get('tags').get(params['id'])
    if tag_obj != None:
      self.app.link.save_tag(tag_obj)
    params = self.get_tag_params(params['id'],params['connection_id'])
    self.insert_tag_row(None,params)

  def update_tag(self,params,*args):
    conx_obj = self.app.link.get('connections').get(params['connection_id'])
    if conx_obj != None:
      tag_obj = conx_obj.get('tags').get(params['id'])
      if tag_obj != None:
        for key, val in params.items():
          if key == 'id' or key == 'description' or key == 'connection_id' or val == None:
            pass
          else:
            try:
              tag_obj.set(key,val)
            except KeyError as e:
              print(e,key)
        self.app.link.save_tag(tag_obj)

  def insert_tag_row(self,button,params,*args):
    TagsListRow(params,self.listbox,1,self.app,self,params['connection_id'],even_row=False)
    self.show_all()

  def add_style(self, wid, style):
    #style should be a list
    sc = wid.get_style_context()
    for sty in style:
      sc.add_class(sty)

  def close_popup(self, button):
    self.destroy()


class TagsListRow(object):
  ##############NEED TO WORK ON FILTERING BASED ON CONNECTION
    def __init__(self,params,list_box,row_num,app,parent,conx_id,even_row,*args):
        super(TagsListRow, self).__init__()
        self.listbox = list_box
        self.conx_id = conx_id
        self.id = params['id']
        self.app = app
        self.parent = parent
        self.even_row = even_row
        self.params = params
        self.columns = ['id', 'connection_id', 'description','address']
        self.lst_height = 20
        self.row = Gtk.ListBoxRow()
        self.list_box_data()


    def open_tag_settings(self, button,*args):
      self.parent.open_settings_popup(self.id,self.conx_id)

    def delete_tag(self, button,*args):
      self.parent.confirm_delete(None,self.id,self.conx_id,self.row)

    def list_box_data(self):
      hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, height_request = self.lst_height)
      self.row.add(hbox)
      #icon
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Tag.png', 20, -1, True)
      icon = Gtk.Image(pixbuf=p_buf)
      hbox.pack_start(icon, False, False, 0)

      for col in self.columns:
        if col in self.params.keys():
          lbl = Gtk.Label(label=str(self.params[col]), xalign=0.5, yalign = 0.5, width_request = 175)
          lbl.set_use_markup(True)
          lbl.set_max_width_chars(20)
          lbl.set_line_wrap(True)
        else:
          lbl = Gtk.Label(label='', xalign=0.5, yalign = 0.5, width_request = 175)          
        hbox.pack_start(lbl, True, True, 0)
        self.add_style(lbl,['font-14','font-bold'])
      if self.even_row:
        self.add_style(self.row,['list-box-even-row'])
      else:
        self.add_style(self.row,['list-box-odd-row'])

      #tag settings button
      self.driver_settings_button = Gtk.Button(height_request = self.lst_height, width_request = self.lst_height)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/settings.png', self.lst_height, -1, True)
      icon = Gtk.Image(pixbuf=p_buf)
      self.driver_settings_button.add(icon)
      self.parent.add_style(self.driver_settings_button,["ctrl-button"])
      self.driver_settings_button.connect("clicked", self.open_tag_settings)
      hbox.pack_start(self.driver_settings_button, False, False, 0)

      #tag delete button
      self.tag_delete_button = Gtk.Button(height_request = self.lst_height, width_request = self.lst_height)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Delete.png', self.lst_height, -1, True)
      icon = Gtk.Image(pixbuf=p_buf)
      self.tag_delete_button.add(icon)
      self.parent.add_style(self.tag_delete_button,["ctrl-button"])
      self.tag_delete_button.connect("clicked", self.delete_tag)
      hbox.pack_start(self.tag_delete_button, False, False, 0)
      
      self.listbox.add(self.row)

    def add_style(self, item,style):
      sc = item.get_style_context()
      for sty in style:
        sc.add_class(sty)

# class Tag_row(object):
#   def __init__(self,params,grid,row_num,app,parent,conx_id,*args):
#     self.height_request = 15
#     self.app = app
#     self.parent = parent
#     self.grid = grid
#     self.row_num = row_num
#     self.params = params
#     self.conx_id = conx_id
#     if self.params != None:
#       self.id = self.params['id']
#     self.unsaved_changes = False      #Need to pass this up so that confirm closing popup with unsaved changes
#     self.build_row()

#   def build_row(self,*args):
#     #icon
#     p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Tag.png', 20, -1, True)
#     icon = Gtk.Image(pixbuf=p_buf,height_request = self.height_request)
#     self.grid.attach(icon,0,self.row_num,1,1)   

#     #tag_name
#     db_name = str(self.params['id'])
#     self.tag_name = Gtk.Label(width_request = 250,height_request = self.height_request)#hexpand = True
#     self.tag_name.set_label(db_name)
#     self.add_style(self.tag_name,["font-16","ctrl-lbl","font-bold"])
#     self.grid.attach(self.tag_name,1,self.row_num,1,1) 

#     #Connection Name
#     db_conx_driver = self.params['connection_id']
#     self.conx_driver = Gtk.Label(width_request = 200,height_request = self.height_request)#hexpand = True
#     #if db_conx_driver in self.conx_Typedata.keys():
#     self.conx_driver.set_label(db_conx_driver)
#     self.add_style(self.conx_driver,["font-16","ctrl-lbl","font-bold"])
#     self.grid.attach(self.conx_driver,2,self.row_num,1,1)

#     #Tag Description
#     db_tag_desc = self.params['description']
#     if db_tag_desc == None:
#       db_tag_desc = ''
#     self.tag_desc = Gtk.Label(width_request = 250,height_request = self.height_request)#hexpand = True
#     self.tag_desc.set_label(db_tag_desc)
#     self.add_style(self.tag_desc,["font-16","ctrl-lbl","font-bold"])
#     self.grid.attach(self.tag_desc,3,self.row_num,1,1)

#     #Tag Address
    
#     #Tag Settings Button
#     self.driver_settings_button = Gtk.Button(height_request = self.height_request)
#     p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/settings.png', 20, -1, True)
#     icon = Gtk.Image(pixbuf=p_buf)
#     self.driver_settings_button.add(icon)
#     self.parent.add_style(self.driver_settings_button,["ctrl-button"])
#     self.driver_settings_button.connect("clicked", self.open_settings)
#     self.grid.attach(self.driver_settings_button,4,self.row_num,1,1)
#     if self.params != None:
#       self.driver_settings_button.set_sensitive(True)
#     else:
#       self.driver_settings_button.set_sensitive(False)

#   def driver_selected(self,obj,*args):
#     if not obj.get_active_text():
#       self.driver_settings_button.set_sensitive(False)
#     else:
#       self.driver_settings_button.set_sensitive(True)

#   def open_settings(self,button,*args):
#     self.parent.open_settings_popup(self.id,self.conx_id)

#   def add_style(self, item,style):
#     sc = item.get_style_context()
#     for sty in style:
#       sc.add_class(sty)


class AddTagPopup(Gtk.Dialog):
  def __init__(self, parent,params,conx_type):
    Gtk.Dialog.__init__(self, '',parent, Gtk.DialogFlags.MODAL,
                        (Gtk.STOCK_SAVE, Gtk.ResponseType.YES,
                          Gtk.STOCK_CANCEL, Gtk.ResponseType.NO)
                        )
    self.params = params
    self.conx_type = conx_type
    self.datatypes = ['INT','FLOAT','DINT','UINT','BOOLEAN','SINT']
    self.set_default_size(200, 150)
    self.set_border_width(10)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.set_keep_above(True)
    self.set_decorated(False)
    self.connect("response", self.on_response)
    self.content_area = self.get_content_area()
    self.result = {}

    self.dialog_window = Gtk.Box(width_request=600,orientation=Gtk.Orientation.VERTICAL)
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=600)

    #header
    title = Gtk.Label(label='Create New Tag')
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
    if self.params:
      self.same_name(self.params)
    self.show_all()

  def build_base(self,*args):
    grid = Gtk.Grid(column_spacing=4, row_spacing=4, column_homogeneous=True, row_homogeneous=True,)
    self.pop_lbl = Gtk.Label('')
    self.add_style(self.pop_lbl,['text-red-color','font-14','font-bold'])
    grid.attach(self.pop_lbl,0,0,3,1)
    self.dialog_window.pack_start(grid,1,1,1)

    #Tag name entry
    lbl = Gtk.Label('Tag Name')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,1,1,1) 
    self.tag_name = Gtk.Entry(max_length = 100,width_request = 300,height_request = 30)
    self.tag_name.set_placeholder_text('Enter Tag Name')
    self.tag_name.set_alignment(0.5)
    self.add_style(self.tag_name,["entry","font-12"])
    self.tag_name.connect("notify::text-length", self.enable_new)
    grid.attach(self.tag_name,1,1,2,1)    

    #Connection Driver
    lbl = Gtk.Label('Connection Driver')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,2,1,1) 
    self.conx_driver = Gtk.ComboBoxText(width_request = 200,height_request = 30)#hexpand = True
    self.add_style(self.conx_driver,["font-18","list-select","font-bold"])
    for conx in self.conx_type:
       self.conx_driver.append_text(self.conx_type[conx]['id'])
    self.conx_driver.set_active(0)
    grid.attach(self.conx_driver,1,2,2,1)

   #Tag description entry
    lbl = Gtk.Label('Tag Description')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,3,1,1) 
    self.tag_descr = Gtk.Entry(max_length = 100,width_request = 300,height_request = 30)
    self.tag_descr.set_placeholder_text('Enter Tag Description')
    self.tag_descr.set_alignment(0.5)
    self.add_style(self.tag_descr,["entry","font-12"])
    self.tag_descr.connect("notify::text-length", self.enable_new)
    grid.attach(self.tag_descr,1,3,2,1)

    #Tag Datatype
    lbl = Gtk.Label('Tag Datatype')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,4,1,1) 
    self.tag_datatype = Gtk.ComboBoxText(width_request = 200,height_request = 30,halign = Gtk.Align.CENTER)#hexpand = True
    self.add_style(self.tag_datatype,["font-18","list-select","font-bold"])
    for dt in self.datatypes:
       self.tag_datatype.append_text(dt)
    self.tag_datatype.set_active(0)
    grid.attach(self.tag_datatype,1,4,2,1)    
    sep = Gtk.Label(height_request=3)
    self.dialog_window.pack_start(sep,1,1,1)

  def add_style(self, item,style):
    sc = item.get_style_context()
    for sty in style:
      sc.add_class(sty)

  def enable_new(self, obj, prop):
    enable = (obj.get_property('text-length') > 0)
    if enable:
      self.add_style(obj,["entry","font-18","font-bold"])
    else:
      self.add_style(obj,["entry","font-12"])

  def close_popup(self, button):
    self.destroy()
  
  def on_response(self, widget, response_id):
    #{'id': '2', 'connection_type': 4, 'description': 'EthernetIP'}
    self.result['id'] = self.tag_name.get_text ()
    self.result['connection_id'] = self.conx_driver.get_active_text()
    self.result['description'] = self.tag_descr.get_text ()
    self.result['datatype'] = self.tag_datatype.get_active_text()
  
  def get_result(self):
    return self.result
  
  def same_name(self,results):
    self.pop_lbl.set_label('Name Already Exists')
    self.tag_name.set_text('')
    val = 0
    for conx in self.conx_type:
      self.conx_driver.append_text(self.conx_type[conx]['id'])
      if self.conx_type[conx]['id'] == results['connection_id']:
        self.conx_driver.set_active(val)
      val +=1
    self.tag_descr.set_text(results['description'])
    val = 0
    for dt in self.datatypes:
      self.tag_datatype.append_text(dt)
      if dt == results['datatype']:
        self.tag_datatype.set_active(val)
      val += 1


class TagSettingsPopup(Gtk.Dialog):
  def __init__(self, parent,params):
    Gtk.Dialog.__init__(self, '',parent, Gtk.DialogFlags.MODAL,
                        (Gtk.STOCK_SAVE, Gtk.ResponseType.YES)
                        )
    self.params = params
    self.datatypes = ['INT','FLOAT','DINT','UINT','BOOLEAN','SINT']
    self.set_default_size(500, 400)
    self.set_border_width(10)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.set_keep_above(True)
    self.set_decorated(False)
    self.connect("response", self.on_response)
    self.content_area = self.get_content_area()
    self.result = {}

    self.dialog_window = Gtk.Box(width_request=500,orientation=Gtk.Orientation.VERTICAL)
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=500)

    #header
    tit = self.params['tag_type']
    title = Gtk.Label(label=f'{tit} - Tag')
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
    #self.title_bar.pack_end(self.pin_button,0,0,1)
    sc = self.pin_button.get_style_context()
    sc.add_class('exit-button')
    self.dialog_window.pack_start(self.title_bar,0,0,1)
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    self.content_area.add(self.dialog_window )
    self.build_base()
    self.show_all()

  def build_base(self,*args):
    row = 0
    grid = Gtk.Grid(column_spacing=4, row_spacing=4, column_homogeneous=True, row_homogeneous=True,)
    self.dialog_window.pack_start(grid,1,1,1)

    #Tag name entry
    lbl = Gtk.Label('Tag Name')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,row,1,1) 
    self.conx_name = Gtk.Label(width_request = 300,height_request = 30)
    self.conx_name.set_text(self.params['id'])
    self.conx_name.set_alignment(0.5,0.5)
    self.add_style(self.conx_name,["label","font-18","font-bold"])
    #self.conx_name.connect("notify::text-length", self.enable_new)
    grid.attach(self.conx_name,1,row,2,1)   
    row+=1 

    #Tag description entry
    lbl = Gtk.Label('Tag Description')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,row,1,1) 
    self.conx_descr = Gtk.Label(width_request = 300,height_request = 30)
    self.conx_descr.set_text(self.params['description'])
    self.conx_descr.set_alignment(0.5,0.5)
    self.add_style(self.conx_descr,["label","font-18","font-bold"])
    #self.conx_descr.connect("notify::text-length", self.enable_new)
    grid.attach(self.conx_descr,1,row,2,1) 
    row+=1 

    #Tag Datatype
    db_dt = str(self.params['datatype'])
    lbl = Gtk.Label('Tag Datatype')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,row,1,1) 
    self.tag_datatype = Gtk.ComboBoxText(width_request = 200,height_request = 30,halign = Gtk.Align.CENTER)#hexpand = True
    self.add_style(self.tag_datatype,["font-18","list-select","font-bold"])
    found = None
    val = 0
    for dt in self.datatypes:
      self.tag_datatype.append_text(dt)
      if dt == db_dt:
         found = val
      val+= 1
    if found:
      self.tag_datatype.set_active(found)
    else:
      self.tag_datatype.set_active(0)
    grid.attach(self.tag_datatype,1,row,2,1)
    row+=1

    #Tag Address entry
    if 'address' in self.params.keys(): 
      db_host = str(self.params['address'])
      lbl = Gtk.Label('Tag Address')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      self.tag_address = Gtk.Entry(max_length = 100,width_request = 300,height_request = 30)
      self.tag_address.set_alignment(0.5)
      self.add_style(self.tag_address,["entry","font-18","font-bold"])
      self.tag_address.set_text(db_host)
      grid.attach(self.tag_address,1,row,2,1)
      row+=1 

    #Bit
    if 'bit' in self.params.keys():
      db_tag_bit = str(self.params['baudrate'])
      lbl = Gtk.Label('Baudrate')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      self.tag_bit = Gtk.ComboBoxText(width_request = 200,height_request = 30)#hexpand = True
      self.add_style(self.tag_bit,["font-18","list-select","font-bold"])
      br = None
      val = 0
      bit_num = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16']
      for item in bit_num:
        self.tag_bit.append(str(val),item)
        if item == db_tag_bit:
          br = val
        val+= 1
      if br:
        self.tag_bit.set_active(br)
      else:
        self.tag_bit.set_active(0)
      grid.attach(self.tag_bit,1,row,2,1)
      row+=1 

    #Word Swap
    if 'word_swapped' in self.params.keys(): 
      db_word_swapped = str(self.params['word_swapped'])
      lbl = Gtk.Label('Word Swapped')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      bx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign = Gtk.Align.CENTER)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 20, -1, True)
      image = Gtk.Image(pixbuf=p_buf)
      wid =CheckBoxWidget(30,30,image,db_word_swapped)
      self.word_swapped = wid.return_self()
      bx.pack_start(self.word_swapped,0,0,0)
      grid.attach(bx,1,row,2,1)
      row+=1

    #Byte Swap
    if 'byte_swapped' in self.params.keys(): 
      db_byte_swapped = str(self.params['byte_swapped'])
      lbl = Gtk.Label('Byte Swapped')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      bx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign = Gtk.Align.CENTER)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 20, -1, True)
      image = Gtk.Image(pixbuf=p_buf)
      wid =CheckBoxWidget(30,30,image,db_byte_swapped)
      self.byte_swapped = wid.return_self()
      bx.pack_start(self.byte_swapped,0,0,0)
      grid.attach(bx,1,row,2,1)
      row+=1

    
    sep = Gtk.Label(height_request=3)
    self.dialog_window.pack_start(sep,1,1,1)

  def add_style(self, item,style):
    sc = item.get_style_context()
    for sty in style:
      sc.add_class(sty)

  def enable_new(self, obj, prop):
    enable = (obj.get_property('text-length') > 0)
    if enable:
      self.add_style(obj,["entry","font-18","font-bold"])
    else:
      self.add_style(obj,["entry","font-12"])

  def close_popup(self, button):
    self.destroy()
  
  def on_response(self, widget, response_id):
    self.result['id'] = self.conx_name.get_text()
    self.result['connection_id'] = self.params['connection_id']
    self.result['description'] = self.conx_descr.get_text ()
    if 'bit' in self.params.keys():
      self.result['bit'] = self.tag_bit.get_active_text()
    else:
      self.result['bit'] = None
    if 'address' in self.params.keys():
      self.result['address'] = self.tag_address.get_text()
    else:
      self.result['address'] = None
    if 'datatype' in self.params.keys():
      self.result['datatype'] = self.tag_datatype.get_active_text()
    else:
      self.result['datatype'] = None
    if 'word_swapped' in self.params.keys():
      self.result['word_swapped'] = self.word_swapped.get_active()
    else:
      self.result['word_swapped'] = None
    if 'byte_swapped' in self.params.keys():
      self.result['byte_swapped'] = self.byte_swapped.get_active()
    else:
      self.result['byte_swapped'] = None
  
  def get_result(self):
    return self.result

  def open_numpad(self,button,widget_obj,params,*args):
    numpad = ValueEnter(self,widget_obj,params)
    response = numpad.run()
    if response == Gtk.ResponseType.NO:
      pass
    else:
      pass
      #callback(args)
    numpad.destroy()


class ConnectionsMainPopup(Gtk.Dialog):

  def __init__(self, parent,app):
    super().__init__(transient_for = parent,flags=0) 
    self.unsaved_changes_present = False
    self.unsaved_conn_rows = {}
    self.conn_column_names = ['id', 'connection_type', 'description']
    #self.connections_available = {}
    self.app = app
    self.conx_type = self.app.link.get('connection_types')
    self.app = app
    self.set_default_size(500, 800)
    self.set_decorated(False)
    self.set_border_width(10)
    self.set_keep_above(False)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.content_area = self.get_content_area()

    self.dialog_window = Gtk.Box(width_request=800,orientation=Gtk.Orientation.VERTICAL)
    self.content_area.add(self.dialog_window)
    ### -title bar- ####
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=800)
    self.dialog_window.pack_start(self.title_bar,0,0,1)
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    ### -content area- ####
    self.base_area = Gtk.Box(spacing = 10,orientation=Gtk.Orientation.VERTICAL,margin = 20)
    self.scroll = Gtk.ScrolledWindow(width_request = 800,height_request = 600)
    self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    self.scroll.add(self.base_area)
    self.dialog_window.pack_start(self.scroll,1,1,1)
    ### -footer- ####
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    self.footer_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=800)
    self.dialog_window.pack_start(self.footer_bar,0,0,1)

    self.build_header("Connection Settings")
    self.build_base()
    self.build_footer()
    self.show_all()

  def build_header(self,title):
    #header
    self.add_button2 = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/AddConnection.png', 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.add_button2.add(image)
    sc = self.add_button2.get_style_context()
    sc.add_class('ctrl-button')
    self.title_bar.pack_start(self.add_button2,0,0,0)
    self.add_button2.connect('clicked',self.add_connection_popup,None,self.conx_type)

    title = Gtk.Label(label=title,width_request = 500)
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
    self.connection_settings = []
    self.conn_row_num = 1
    self.conn_grid = Gtk.Grid(column_homogeneous=False,column_spacing=5,row_spacing=5)
    self.base_area.add(self.conn_grid)
    #header
    self.add_column_names()
    self.add_connection_rows()
    self.show_all()

  def build_footer(self):
    self.ok_button = Gtk.Button(width_request = 100)
    self.ok_button.connect('clicked',self.close_popup)
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

  def remove_all_rows(self,*args):
    rows = self.conn_grid.get_children()
    for items in rows:
      self.conn_grid.remove(items)

  def create_delete_button(self,conx_id,row,*args):
    self.delete_button = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Delete.png', 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.delete_button.add(image)
    sc = self.delete_button.get_style_context()
    sc.add_class('ctrl-button')
    self.conn_grid.attach(self.delete_button,5,row,1,1)
    self.delete_button.connect('clicked',self.confirm_delete,conx_id)

  def add_connection_rows(self,*args):
    new_params = {}
    for conx_id,conx_obj in self.app.link.get('connections').items():
      for c in self.conn_column_names:
        new_params[c] = getattr(conx_obj, c)
      row = Connection_row(new_params,self.conn_grid,self.conn_row_num,self.app,self,self.conx_type)
      self.create_delete_button(new_params['id'],self.conn_row_num)
      new_params.clear()
      self.conn_row_num += 1
      self.connection_settings.append(row)
    self.show_all()
    #Spaces out column headers when no data available
    if len(new_params) != 0:
      self.conn_grid.set_column_homogeneous(True)
    else:
      self.conn_grid.set_column_homogeneous(False)
  
  def insert_connection_row(self,button,params,*args):
    #if params = None then insert blank row
    self.conn_grid.set_column_homogeneous(False) 
    self.conn_grid.insert_row(1)
    row = Connection_row(params,self.conn_grid,1,self.app,self,self.conx_type)
    self.create_delete_button(None,1)
    self.conn_row_num += 1
    self.connection_settings.append(row)
    self.show_all()

  def add_column_names(self,*args):
    labels = ['','Connection Name', 'Connection Driver', 'Connection Description', '',''] # may want to create a table in the db for column names
    for l_idx in range(len(labels)):
        l = Gtk.Label(labels[l_idx])
        sc = l.get_style_context()
        sc.add_class('text-black-color')
        sc.add_class('font-14')
        sc.add_class('font-bold')
        self.conn_grid.attach(l, l_idx, 0, 1, 1)
  
  def scroll_to_bottom(self, adjust):
    max = adjust.get_upper()
    adjust.set_value(max)
    self.scroll.set_vadjustment(adjust)
    return False

  def add_style(self, wid, style):
    #style should be a list
    sc = wid.get_style_context()
    for sty in style:
      sc.add_class(sty)

  def confirm_delete(self, button,conx_id,msg="Are you sure you want to delete this connection?", args=[]):
    popup = PopupConfirm(self, msg=msg)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      self.delete_row(conx_id)
      return True
    else:
      return False

  def delete_row(self,id,*args):
    conx_obj = self.app.link.get("connections").get(id)
    if conx_obj != None:
      self.app.link.delete_connection(conx_obj,id)
    self.remove_all_rows()
    self.add_column_names()
    self.add_connection_rows()
    self.show_all()

  def create_connection(self,params,*args):
    #should be passing in description and connection_type as a dictionary
    new_conx = self.app.link.new_connection({"id": params['id'],
                            "connection_type": params['connection_type'],
                            "description": params['description']
                            })
    conx_obj = self.app.link.get("connections").get(params['id'])
    if conx_obj != None:
      self.app.link.save_connection(conx_obj)
    self.insert_connection_row(None,params)

  def update_connection(self,params,*args):
    conx_obj = self.app.link.get("connections").get(params['id'])
    if conx_obj != None:
      for key, val in params.items():
        if key == 'id' or key == 'description' or key == 'connection_type' or val == None:
          pass
        else:
          try:
            conx_obj.set(key,val)
          except KeyError as e:
            print(e,key)
      self.app.link.save_connection(conx_obj)

  def add_connection_popup(self,button,bad_name,*args):
    popup = AddConnectionPopup(self,bad_name,self.conx_type)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      results = (popup.get_result())
      self.check_duplicate_name(results)
      return True
    else:
      return False
  
  def get_connection_params(self,conx_id):
    conx_obj = self.app.link.get("connections").get(conx_id)
    if conx_obj != None:
      return self.app.link.get_connection_params(conx_obj,conx_id)

  def check_duplicate_name(self,results,*args):
    dup = False
    for conx_id,conx_obj in self.app.link.get('connections').items():
      if conx_id == results['id']:
        dup = True
    if dup:
      self.add_connection_popup(None,results,self.conx_type)
    else:
      self.create_connection(results)
      self.open_settings_popup(results['id'])
  
  def open_settings_popup(self,conx_id,*args):
    params = self.get_connection_params(conx_id)
    popup = ConnectionSettingsPopup(self,params)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      results = (popup.get_result())
      self.update_connection(results)
      return True
    else:
      return False

  def close_popup(self, button):
    self.destroy()


class Connection_row(object):
  def __init__(self,params,conn_grid,row_num,app,parent,conx_types,*args):
    self.app = app
    self.parent = parent
    self.conx_type = conx_types
    self.conn_grid = conn_grid
    self.conn_row_num = row_num
    self.params = params
    if self.params != None:
      self.id = self.params['id']
    self.unsaved_changes = False      #Need to pass this up so that confirm closing popup with unsaved changes
    self.build_row()
    #Rows start at 1 because row 0 is titles
    #Grid : Left,Top,Width,Height
    #{'id': '2', 'connection_type': 4, 'description': 'EthernetIP'}

  def build_row(self,*args):
    #icon
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Connect.png', 25, -1, True)
    icon = Gtk.Image(pixbuf=p_buf,height_request = 30)
    self.conn_grid.attach(icon,0,self.conn_row_num,1,1)

    #Connection name entry
    db_conx_name = str(self.params['id'])
    self.conx_name = Gtk.Label(width_request = 200,height_request = 25)#hexpand = True
    self.conx_name.set_label(db_conx_name)
    self.add_style(self.conx_name,["font-18","ctrl-lbl","font-bold"])
    self.conn_grid.attach(self.conx_name,1,self.conn_row_num,1,1)    

    #Connection Driver
    #self.conx_Typedata = {0:'', 1: 'Local', 2: 'ModbusTCP', 3: 'ModbusRTU', 4: 'EthernetIP', 5: 'ADS', 6: 'GRBL', 7: 'OPCUA'}
    db_conx_driver = self.params['connection_type']
    self.conx_driver = Gtk.Label(width_request = 200,height_request = 25)#hexpand = True
    #if db_conx_driver in self.conx_Typedata.keys():
    self.conx_driver.set_label(db_conx_driver)
    self.add_style(self.conx_driver,["font-18","ctrl-lbl","font-bold"])
    self.conn_grid.attach(self.conx_driver,2,self.conn_row_num,1,1)

    #Connection Description
    db_conx_desc = self.params['description']
    self.conx_desc = Gtk.Label(width_request = 200,height_request = 25)#hexpand = True
    self.conx_desc.set_label(db_conx_desc)
    self.add_style(self.conx_desc,["font-18","ctrl-lbl","font-bold"])
    self.conn_grid.attach(self.conx_desc,3,self.conn_row_num,1,1)
    
    #Connection Settings Button
    self.driver_settings_button = Gtk.Button(height_request = 25)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/settings.png', 25, -1, True)
    icon = Gtk.Image(pixbuf=p_buf)
    self.driver_settings_button.add(icon)
    self.parent.add_style(self.driver_settings_button,["ctrl-button"])
    self.driver_settings_button.connect("clicked", self.open_settings)
    self.conn_grid.attach(self.driver_settings_button,4,self.conn_row_num,1,1)
    if self.params != None:
      self.driver_settings_button.set_sensitive(True)
    else:
      self.driver_settings_button.set_sensitive(False)

  def enable_new(self, obj, prop):
    enable = (obj.get_property('text-length') > 0)
    self.save_button.set_sensitive(enable)
    if enable:
      self.parent.add_style(self.conx_name,["entry","font-18","font-bold"])
    else:
      self.parent.add_style(self.conx_name,["entry","font-12"])

  def driver_selected(self,obj,*args):
    if not obj.get_active_text():
      self.driver_settings_button.set_sensitive(False)
    else:
      self.driver_settings_button.set_sensitive(True)

  def open_settings(self,button,*args):
    self.parent.open_settings_popup(self.id)

  def add_style(self, item,style):
    sc = item.get_style_context()
    for sty in style:
      sc.add_class(sty)


class AddConnectionPopup(Gtk.Dialog):
  def __init__(self, parent,params,conx_type):
    Gtk.Dialog.__init__(self, '',parent, Gtk.DialogFlags.MODAL,
                        (Gtk.STOCK_SAVE, Gtk.ResponseType.YES,
                          Gtk.STOCK_CANCEL, Gtk.ResponseType.NO)
                        )
    self.params = params
    self.conx_type = conx_type
    self.set_default_size(200, 150)
    self.set_border_width(10)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.set_keep_above(True)
    self.set_decorated(False)
    self.connect("response", self.on_response)
    self.content_area = self.get_content_area()
    self.result = {}

    self.dialog_window = Gtk.Box(width_request=600,orientation=Gtk.Orientation.VERTICAL)
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=600)

    #header
    title = Gtk.Label(label='Create New Connection')
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
    if self.params:
      self.same_name(self.params)
    self.show_all()

  def build_base(self,*args):
    grid = Gtk.Grid(column_spacing=4, row_spacing=4, column_homogeneous=True, row_homogeneous=True,)
    self.pop_lbl = Gtk.Label('')
    self.add_style(self.pop_lbl,['text-red-color','font-14','font-bold'])
    grid.attach(self.pop_lbl,0,0,3,1)
    self.dialog_window.pack_start(grid,1,1,1)

    #Connection name entry
    lbl = Gtk.Label('Connection Name')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,1,1,1) 
    self.conx_name = Gtk.Entry(max_length = 100,width_request = 300,height_request = 30)
    self.conx_name.set_placeholder_text('Enter Connection Name')
    self.conx_name.set_alignment(0.5)
    self.add_style(self.conx_name,["entry","font-12"])
    self.conx_name.connect("notify::text-length", self.enable_new)
    grid.attach(self.conx_name,1,1,2,1)    

    #Connection Driver
    lbl = Gtk.Label('Connection Driver')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,2,1,1) 
    self.conx_driver = Gtk.ComboBoxText(width_request = 200,height_request = 30)#hexpand = True
    self.add_style(self.conx_driver,["font-18","list-select","font-bold"])
    val = 0
    for key in self.conx_type:
      self.conx_driver.append(str(val),key)
      val+= 1
    self.conx_driver.set_active(0)
    grid.attach(self.conx_driver,1,2,2,1)

   #Connection description entry
    lbl = Gtk.Label('Connection Description')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,3,1,1) 
    self.conx_descr = Gtk.Entry(max_length = 100,width_request = 300,height_request = 30)
    self.conx_descr.set_placeholder_text('Enter Connection Description')
    self.conx_descr.set_alignment(0.5)
    self.add_style(self.conx_descr,["entry","font-12"])
    self.conx_descr.connect("notify::text-length", self.enable_new)
    grid.attach(self.conx_descr,1,3,2,1)  
    
    sep = Gtk.Label(height_request=3)
    self.dialog_window.pack_start(sep,1,1,1)

  def add_style(self, item,style):
    sc = item.get_style_context()
    for sty in style:
      sc.add_class(sty)

  def enable_new(self, obj, prop):
    enable = (obj.get_property('text-length') > 0)
    if enable:
      self.add_style(obj,["entry","font-18","font-bold"])
    else:
      self.add_style(obj,["entry","font-12"])

  def close_popup(self, button):
    self.destroy()
  
  def on_response(self, widget, response_id):
    #{'id': '2', 'connection_type': 4, 'description': 'EthernetIP'}
    self.result['id'] = self.conx_name.get_text ()
    self.result['connection_type'] = self.conx_driver.get_active_text()
    self.result['description'] = self.conx_descr.get_text ()
  
  def get_result(self):
    return self.result
  
  def same_name(self,results):
    self.pop_lbl.set_label('Name Already Exists')
    self.conx_name.set_text('')
    val = 0
    for key in self.conx_type:
      if results['connection_type'] == key:
        self.conx_driver.set_active(val)
      val+= 1
    self.conx_descr.set_text(results['description'])


class ConnectionSettingsPopup(Gtk.Dialog):
  def __init__(self, parent,params):
    Gtk.Dialog.__init__(self, '',parent, Gtk.DialogFlags.MODAL,
                        (Gtk.STOCK_SAVE, Gtk.ResponseType.YES)
                        )
    self.params = params
    self.set_default_size(500, 400)
    self.set_border_width(10)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.set_keep_above(True)
    self.set_decorated(False)
    self.connect("response", self.on_response)
    self.content_area = self.get_content_area()
    self.result = {}

    self.dialog_window = Gtk.Box(width_request=500,orientation=Gtk.Orientation.VERTICAL)
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=500)

    #header
    tit = self.params['connection_type']
    title = Gtk.Label(label=f'{tit} Connection')
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
    #self.title_bar.pack_end(self.pin_button,0,0,1)
    sc = self.pin_button.get_style_context()
    sc.add_class('exit-button')
    self.dialog_window.pack_start(self.title_bar,0,0,1)
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    self.content_area.add(self.dialog_window )
    self.build_base()
    self.show_all()

  def build_base(self,*args):
    row = 0
    grid = Gtk.Grid(column_spacing=4, row_spacing=4, column_homogeneous=True, row_homogeneous=True,)
    self.dialog_window.pack_start(grid,1,1,1)

    #Connection name entry
    lbl = Gtk.Label('Connection Name')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,row,1,1) 
    self.conx_name = Gtk.Label(width_request = 300,height_request = 30)
    self.conx_name.set_text(self.params['id'])
    self.conx_name.set_alignment(0.5,0.5)
    self.add_style(self.conx_name,["label","font-18","font-bold"])
    #self.conx_name.connect("notify::text-length", self.enable_new)
    grid.attach(self.conx_name,1,row,2,1)   
    row+=1 

    #Connection description entry
    lbl = Gtk.Label('Connection Description')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    grid.attach(lbl,0,row,1,1) 
    self.conx_descr = Gtk.Label(width_request = 300,height_request = 30)
    self.conx_descr.set_text(self.params['description'])
    self.conx_descr.set_alignment(0.5,0.5)
    self.add_style(self.conx_descr,["label","font-18","font-bold"])
    #self.conx_descr.connect("notify::text-length", self.enable_new)
    grid.attach(self.conx_descr,1,row,2,1) 
    row+=1 

    #Pollrate
    if 'pollrate' in self.params.keys():    
      db_poll_rate = str(self.params['pollrate'])
      lbl = Gtk.Label('Connection Pollrate')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      but = Gtk.Button(width_request = 100)
      self.pollrate = Gtk.Label()
      self.pollrate.set_label(db_poll_rate)
      self.add_style(self.pollrate,['borderless-num-display','font-14','text-black-color'])
      but.add(self.pollrate)
      sc = but.get_style_context()
      sc.add_class('ctrl-button')
      but.connect('clicked',self.open_numpad,self.pollrate,{'min':-32768,'max':32768,'type':float,'polarity':True})
      grid.attach(but,1,row,2,1)
      row+=1 

    #Auto Connect
    if 'auto_connect' in self.params.keys(): 
      db_auto_connect = str(self.params['auto_connect'])
      lbl = Gtk.Label('Auto Connect on Start')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      bx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign = Gtk.Align.CENTER)
      p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 20, -1, True)
      image = Gtk.Image(pixbuf=p_buf)
      wid =CheckBoxWidget(30,30,image,db_auto_connect)
      self.auto_connect = wid.return_self()
      bx.pack_start(self.auto_connect,0,0,0)
      grid.attach(bx,1,row,2,1)
      row+=1

    #Connection host entry
    if 'host' in self.params.keys(): 
      db_host = str(self.params['host'])
      lbl = Gtk.Label('Connection Host')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      self.conx_host = Gtk.Entry(max_length = 100,width_request = 300,height_request = 30)
      self.conx_host.set_alignment(0.5)
      self.add_style(self.conx_host,["entry","font-18","font-bold"])
      self.conx_host.set_text(db_host)
      grid.attach(self.conx_host,1,row,2,1)
      row+=1 

    #Port
    if 'port' in self.params.keys(): 
      db_port = str(self.params['port'])
      lbl = Gtk.Label('Connection Port')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      but = Gtk.Button(width_request = 100)
      self.conx_port = Gtk.Label()
      self.conx_port.set_label(db_port)
      self.add_style(self.conx_port,['borderless-num-display','font-14','text-black-color'])
      but.add(self.conx_port)
      sc = but.get_style_context()
      sc.add_class('ctrl-button')
      but.connect('clicked',self.open_numpad,self.conx_port,{'min':0,'max':65536,'type':int,'polarity':True})
      grid.attach(but,1,row,2,1)
      row+=1 

    #Station ID
    if 'station_id' in self.params.keys(): 
      db_station_id = str(self.params['station_id'])
      lbl = Gtk.Label('Station ID')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      but = Gtk.Button(width_request = 100)
      self.station_id = Gtk.Label()
      self.station_id.set_label(db_station_id)
      self.add_style(self.station_id,['borderless-num-display','font-14','text-black-color'])
      but.add(self.station_id)
      sc = but.get_style_context()
      sc.add_class('ctrl-button')
      but.connect('clicked',self.open_numpad,self.station_id,{'min':0,'max':255,'type':int,'polarity':True})
      grid.attach(but,1,row,2,1)
      row+=1 

    #Connection Baudrate
    if 'baudrate' in self.params.keys():
      db_baudrate = str(self.params['baudrate'])
      lbl = Gtk.Label('Baudrate')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      self.baudrate = Gtk.ComboBoxText(width_request = 200,height_request = 30)#hexpand = True
      self.add_style(self.baudrate,["font-18","list-select","font-bold"])
      br = None
      val = 0
      b_rates = ['1200','2400','4800','9600','19200','38400','57600','115200']
      for item in b_rates:
        self.baudrate.append(str(val),item)
        if item == db_baudrate:
          br = val
        val+= 1
      if br:
        self.baudrate.set_active(br)
      else:
        self.baudrate.set_active(0)
      grid.attach(self.baudrate,1,row,2,1)
      row+=1 

    #Timeout
    if 'timeout' in self.params.keys(): 
      db_timeout = str(self.params['timeout'])
      lbl = Gtk.Label('Timeout (sec)')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      but = Gtk.Button(width_request = 100)
      self.timeout = Gtk.Label()
      self.timeout.set_label(db_timeout)
      self.add_style(self.timeout,['borderless-num-display','font-14','text-black-color'])
      but.add(self.timeout)
      sc = but.get_style_context()
      sc.add_class('ctrl-button')
      but.connect('clicked',self.open_numpad,self.timeout,{'min':0,'max':100,'type':int,'polarity':True})
      grid.attach(but,1,row,2,1)
      row+=1 

    #Stop Bit
    if 'stop_bit' in self.params.keys():
      db_stop_bit = str(self.params['stop_bit'])
      lbl = Gtk.Label('Stop bits')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      self.stop_bit = Gtk.ComboBoxText(width_request = 200,height_request = 30)#hexpand = True
      self.add_style(self.stop_bit,["font-18","list-select","font-bold"])
      sb = None
      val = 0
      s_bits = ['0','1','2']
      for item in s_bits:
        self.stop_bit.append(str(val),item)
        if item == db_stop_bit:
          sb = val
        val+= 1
      if sb:
        self.stop_bit.set_active(sb)
      else:
        self.stop_bit.set_active(0)
      grid.attach(self.stop_bit,1,row,2,1)
      row+=1 

    #parity
    if 'parity' in self.params.keys():
      db_parity = str(self.params['parity'])
      lbl = Gtk.Label('Parity')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      self.parity = Gtk.ComboBoxText(width_request = 200,height_request = 30)#hexpand = True
      self.add_style(self.parity,["font-18","list-select","font-bold"])
      process_link = None
      val = 0
      p_type = ['N','O','E']
      for item in p_type:
        self.parity.append(str(val),item)
        if item == db_parity:
          p = val
        val+= 1
      if p:
        self.parity.set_active(p)
      else:
        self.parity.set_active(0)
      grid.attach(self.parity,1,row,2,1)
      row+=1 

    #byte_size
    if 'byte_size' in self.params.keys():
      db_byte_size = str(self.params['byte_size'])
      lbl = Gtk.Label('Byte Size')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      self.byte_size = Gtk.ComboBoxText(width_request = 200,height_request = 30)#hexpand = True
      self.add_style(self.byte_size,["font-18","list-select","font-bold"])
      bs = None
      val = 0
      b_size = ['8','7']
      for item in b_size:
        self.byte_size.append(str(val),item)
        if item == db_byte_size:
          bs = val
        val+= 1
      if bs:
        self.byte_size.set_active(bs)
      else:
        self.byte_size.set_active(0)
      grid.attach(self.byte_size,1,row,2,1)
      row+=1 

    #Retries
    if 'retries' in self.params.keys(): 
      db_retries = str(self.params['retries'])
      lbl = Gtk.Label('Retries')
      self.add_style(lbl,["Label","font-16",'font-bold'])
      grid.attach(lbl,0,row,1,1) 
      but = Gtk.Button(width_request = 100)
      self.retries = Gtk.Label()
      self.retries.set_label(db_retries)
      self.add_style(self.retries,['borderless-num-display','font-14','text-black-color'])
      but.add(self.retries)
      sc = but.get_style_context()
      sc.add_class('ctrl-button')
      but.connect('clicked',self.open_numpad,self.retries,{'min':0,'max':10,'type':int,'polarity':True})
      grid.attach(but,1,row,2,1)
      row+=1 
    
    sep = Gtk.Label(height_request=3)
    self.dialog_window.pack_start(sep,1,1,1)

  def add_style(self, item,style):
    sc = item.get_style_context()
    for sty in style:
      sc.add_class(sty)

  def enable_new(self, obj, prop):
    enable = (obj.get_property('text-length') > 0)
    if enable:
      self.add_style(obj,["entry","font-18","font-bold"])
    else:
      self.add_style(obj,["entry","font-12"])

  def close_popup(self, button):
    self.destroy()
  
  def on_response(self, widget, response_id):
    self.result['id'] = self.conx_name.get_text()
    self.result['connection_type'] = self.params['connection_type']
    self.result['description'] = self.conx_descr.get_text ()
    if 'pollrate' in self.params.keys():
      self.result['pollrate'] = self.pollrate.get_text()
    else:
      self.result['pollrate'] = None
    if 'auto_connect' in self.params.keys():
      self.result['auto_connect'] = self.auto_connect.get_active()
    else:
      self.result['auto_connect'] = None
    if 'host' in self.params.keys():
      self.result['host'] = self.conx_host.get_text()
    else:
      self.result['host'] = None
    if 'port' in self.params.keys():
      self.result['port'] = self.conx_port.get_text()
    else:
      self.result['port'] = None
    if 'station_id' in self.params.keys():
      self.result['station_id'] = self.station_id.get_text()
    else:
      self.result['station_id'] = None
    if 'baudrate' in self.params.keys():
      self.result['baudrate'] = self.baudrate.get_active_text()
    else:
      self.result['baudrate'] = None
    if 'timeout' in self.params.keys():
      self.result['timeout'] = self.timeout.get_text()
    else:
      self.result['timeout'] = None
    if 'stop_bit' in self.params.keys():
      self.result['stop_bit'] = self.stop_bit.get_active_text()
    else:
      self.result['stop_bit'] = None
    if 'parity' in self.params.keys():
      self.result['parity'] = self.parity.get_active_text()
    else:
      self.result['parity'] = None
    if 'byte_size' in self.params.keys():
      self.result['byte_size'] = self.byte_size.get_active_text()
    else:
      self.result['byte_size'] = None
    if 'retries' in self.params.keys():
      self.result['retries'] = self.retries.get_text()
    else:
      self.result['retries'] = None
  
  def get_result(self):
    return self.result

  def open_numpad(self,button,widget_obj,params,*args):
    numpad = ValueEnter(self,widget_obj,params)
    response = numpad.run()
    if response == Gtk.ResponseType.NO:
      pass
    else:
      pass
      #callback(args)
    numpad.destroy()
  

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

################################ Fix OK button to save before closing
class ChartSettingsPopup(Gtk.Dialog):
  def __init__(self, app,chart):
    Gtk.Dialog.__init__(self, '',None, Gtk.DialogFlags.MODAL,
                        (Gtk.STOCK_OK, Gtk.ResponseType.YES)
                        )
    self.chart = chart
    self.c_id = self.chart.db_id
    self.app = app
    self.db_session = self.app.settings_db.session
    self.db_model = self.app.settings_db.models['chart']
    self.Tbl = self.db_model
    self.set_default_size(300, 300)
    self.set_border_width(10)
    sc = self.get_style_context()
    sc.add_class("dialog-border")
    self.set_keep_above(False)
    self.set_decorated(False)
    self.content_area = self.get_content_area()
    self.dialog_window = Gtk.Box(width_request=300,orientation=Gtk.Orientation.VERTICAL)
    self.title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=300)
    self.content_area.add(self.dialog_window )
    self.bg_color = [1.0,1.0,1.0,1.0] #default to white
    self.grid_color = [1.0,1.0,1.0,1.0] #default to white
    self.marker1_color = [1.0,0.0,0.0,1.0] #default to red
    self.marker2_color = [0.0,1.0,0.0,1.0] #default to blue
    self.h_grids = 2
    self.v_grids = 2
    self.marker1_width = 1
    self.marker2_width = 1
    self.build_header()
    self.load_chart_settings()
    self.build_base()
    self.show_all()

  def build_header(self,*args):
    #Save Button
    self.save_button = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Save.png', 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.save_button.add(image)
    sc = self.save_button.get_style_context()
    sc.add_class('ctrl-button')
    bx = Gtk.Box()
    bx.pack_end(self.save_button,0,0,0)
    self.title_bar.pack_start(bx,0,0,0)
    self.save_button.connect('clicked',self.save_settings)

    #title
    title = Gtk.Label(label='Chart Settings')
    sc = title.get_style_context()
    sc.add_class('text-black-color')
    sc.add_class('font-18')
    sc.add_class('font-bold')
    self.title_bar.pack_start(title,1,1,1)

    #exit button
    self.exit_button = Gtk.Button(width_request = 20)
    self.exit_button.connect('clicked',self.close_popup)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/Close.png', 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.exit_button.add(image)
    self.title_bar.pack_end(self.exit_button,0,0,1)
    sc = self.exit_button.get_style_context()
    sc.add_class('exit-button')

    self.dialog_window.pack_start(self.title_bar,0,0,1)
    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.dialog_window.pack_start(divider,0,0,1)
    self.grid = Gtk.Grid(column_spacing=3, row_spacing=4, column_homogeneous=False, row_homogeneous=True,)
    self.dialog_window.pack_start(self.grid,1,1,1)

  def build_base(self,*args):
    #Chart Select
    lbl = Gtk.Label('Chart Number')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    self.grid.attach(lbl,0,1,1,1) 
    self.chart_select = Gtk.ComboBoxText(width_request = 200,height_request = 30)#hexpand = True
    self.add_style(self.chart_select,["font-18","list-select","font-bold"])
    selections = []
    for num in range(16):
      self.chart_select.append(str(num+1),str(num+1))
    self.chart_select.set_active((self.c_id-1))
    self.grid.attach(self.chart_select,1,1,1,1)
    self.chart_select.connect("changed", self.new_chart_selected)

    #color
    lbl = Gtk.Label('Background Color')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    self.grid.attach(lbl,0,2,1,1) 
    rgbcolor = Gdk.RGBA()
    rgbcolor.red = float(self.bg_color[0])
    rgbcolor.green = float(self.bg_color[1])
    rgbcolor.blue = float(self.bg_color[2])
    rgbcolor.alpha = float(self.bg_color[3])
    bx = Gtk.Box()
    self.color_button = Gtk.ColorButton(width_request = 50)
    self.color_button.set_rgba (rgbcolor)
    sc = self.color_button.get_style_context()
    sc.add_class('ctrl-button')
    bx.set_center_widget(self.color_button)
    self.grid.attach(bx,1,2,1,1)
    #self.color_button.connect('color-set',self.row_changed)

    #Horizontal Grid LInes
    lbl = Gtk.Label('Horizontal Grid Lines')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    self.grid.attach(lbl,0,3,1,1) 
    but = Gtk.Button(width_request = 20)
    self.hor_grid = Gtk.Label()
    self.hor_grid.set_label(str(self.h_grids))
    self.add_style(self.hor_grid,['borderless-num-display','font-14','text-black-color'])
    but.add(self.hor_grid)
    sc = but.get_style_context()
    sc.add_class('ctrl-button')
    but.connect('clicked',self.open_numpad,self.hor_grid,{'min':0,'max':8,'type':int,'polarity':False})
    self.grid.attach(but,1,3,1,1)
    #but.connect('clicked',self.row_changed)

    #Vertical Grid Lines
    lbl = Gtk.Label('Vertical Grid Lines')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    self.grid.attach(lbl,0,4,1,1) 
    but = Gtk.Button(width_request = 20)
    self.vert_grid = Gtk.Label()
    self.vert_grid.set_label(str(self.v_grids))
    self.add_style(self.vert_grid,['borderless-num-display','font-14','text-black-color'])
    but.add(self.vert_grid)
    sc = but.get_style_context()
    sc.add_class('ctrl-button')
    but.connect('clicked',self.open_numpad,self.vert_grid,{'min':0,'max':8,'type':int,'polarity':False})
    self.grid.attach(but,1,4,1,1)
    #but.connect('clicked',self.row_changed)

    #grid color
    lbl = Gtk.Label('Grid Line Color')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    self.grid.attach(lbl,0,5,1,1) 
    rgbcolor = Gdk.RGBA()
    rgbcolor.red = float(self.grid_color[0])
    rgbcolor.green = float(self.grid_color[1])
    rgbcolor.blue = float(self.grid_color[2])
    rgbcolor.alpha = float(self.grid_color[3])
    bx = Gtk.Box()
    self.grid_color_button = Gtk.ColorButton(width_request = 50)
    self.grid_color_button.set_rgba (rgbcolor)
    sc = self.grid_color_button.get_style_context()
    sc.add_class('ctrl-button')
    bx.set_center_widget(self.grid_color_button)
    self.grid.attach(bx,1,5,1,1)

    #Marker 1
    lbl = Gtk.Label('Chart Marker 1 (Width/Color)')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    self.grid.attach(lbl,0,6,1,1) 
    but = Gtk.Button(width_request = 20)
    self.marker1_width_button = Gtk.Label()
    self.marker1_width_button.set_label(str(self.marker1_width))
    self.add_style(self.marker1_width_button,['borderless-num-display','font-14','text-black-color'])
    but.add(self.marker1_width_button)
    sc = but.get_style_context()
    sc.add_class('ctrl-button')
    but.connect('clicked',self.open_numpad,self.marker1_width_button,{'min':0,'max':8,'type':int,'polarity':False})
    self.grid.attach(but,1,6,1,1)
    #but.connect('clicked',self.row_changed)

    rgbcolor = Gdk.RGBA()
    rgbcolor.red = float(self.marker1_color[0])
    rgbcolor.green = float(self.marker1_color[1])
    rgbcolor.blue = float(self.marker1_color[2])
    rgbcolor.alpha = float(self.marker1_color[3])
    bx = Gtk.Box()
    self.marker1_color_button = Gtk.ColorButton(width_request = 50)
    self.marker1_color_button.set_rgba (rgbcolor)
    sc = self.marker1_color_button.get_style_context()
    sc.add_class('ctrl-button')
    bx.set_center_widget(self.marker1_color_button)
    self.grid.attach(bx,2,6,1,1)

    #Marker 2
    lbl = Gtk.Label('Chart Marker 2 (Width/Color)')
    self.add_style(lbl,["Label","font-16",'font-bold'])
    self.grid.attach(lbl,0,7,1,1) 
    but = Gtk.Button(width_request = 20)
    self.marker2_width_button = Gtk.Label()
    self.marker2_width_button.set_label(str(self.marker2_width))
    self.add_style(self.marker2_width_button,['borderless-num-display','font-14','text-black-color'])
    but.add(self.marker2_width_button)
    sc = but.get_style_context()
    sc.add_class('ctrl-button')
    but.connect('clicked',self.open_numpad,self.marker2_width_button,{'min':0,'max':8,'type':int,'polarity':False})
    self.grid.attach(but,1,7,1,1)
    #but.connect('clicked',self.row_changed)

    rgbcolor = Gdk.RGBA()
    rgbcolor.red = float(self.marker2_color[0])
    rgbcolor.green = float(self.marker2_color[1])
    rgbcolor.blue = float(self.marker2_color[2])
    rgbcolor.alpha = float(self.marker2_color[3])
    bx = Gtk.Box()
    self.marker2_color_button = Gtk.ColorButton(width_request = 50)
    self.marker2_color_button.set_rgba (rgbcolor)
    sc = self.marker2_color_button.get_style_context()
    sc.add_class('ctrl-button')
    bx.set_center_widget(self.marker2_color_button)
    self.grid.attach(bx,2,7,1,1)

    sep = Gtk.Label(height_request=3)
    self.dialog_window.pack_start(sep,1,1,1)

  def load_chart_settings(self,*args):
    settings = self.db_session.query(self.Tbl).filter(self.Tbl.id == int(self.c_id)).first()
    if settings:
      self.bg_color = json.loads(settings.bg_color) #rgb in json
      self.h_grids = settings.h_grids
      self.v_grids = settings.v_grids
      self.grid_color = json.loads(settings.grid_color) #rgb in json
      self.marker1_width = settings.marker1_width
      self.marker1_color = json.loads(settings.marker1_color) #rgb in json 
      self.marker2_width = settings.marker2_width
      self.marker2_color = json.loads(settings.marker2_color) #rgb in json 
    else:
      print("Chart Not Found")
      #using default values

  def confirm(self, button,pen_id,msg="Are you sure you want to delete this pen?", args=[]):
    popup = PopupConfirm(self, msg=msg)
    response = popup.run()
    popup.destroy()
    if response == Gtk.ResponseType.YES:
      self.delete_row(pen_id)
      return True
    else:
      return False

  def new_chart_selected(self, but,*args):
    val = self.chart_select.get_active_text()
    self.c_id = int(val)
    self.load_chart_settings()
    self.vert_grid.set_label(str(self.v_grids))
    self.hor_grid.set_label(str(self.h_grids))
    bg_rgbcolor = Gdk.RGBA()
    bg_rgbcolor.red = float(self.bg_color[0])
    bg_rgbcolor.green = float(self.bg_color[1])
    bg_rgbcolor.blue = float(self.bg_color[2])
    bg_rgbcolor.alpha = float(self.bg_color[3])
    self.color_button.set_rgba (bg_rgbcolor)
    grid_rgbcolor = Gdk.RGBA()
    grid_rgbcolor.red = float(self.grid_color[0])
    grid_rgbcolor.green = float(self.grid_color[1])
    grid_rgbcolor.blue = float(self.grid_color[2])
    grid_rgbcolor.alpha = float(self.grid_color[3])
    self.grid_color_button.set_rgba (grid_rgbcolor)
    marker1_rgbcolor = Gdk.RGBA()
    marker1_rgbcolor.red = float(self.marker1_color[0])
    marker1_rgbcolor.green = float(self.marker1_color[1])
    marker1_rgbcolor.blue = float(self.marker1_color[2])
    marker1_rgbcolor.alpha = float(self.marker1_color[3])
    self.marker1_color_button.set_rgba (marker1_rgbcolor)
    marker2_rgbcolor = Gdk.RGBA()
    marker2_rgbcolor.red = float(self.marker2_color[0])
    marker2_rgbcolor.green = float(self.marker2_color[1])
    marker2_rgbcolor.blue = float(self.marker2_color[2])
    marker2_rgbcolor.alpha = float(self.marker2_color[3])
    self.marker2_color_button.set_rgba (marker2_rgbcolor)
  
  def save_settings(self,but,*args):
    self.c_id = int(self.chart_select.get_active_text())
    bg_color = self.color_button.get_rgba()
    bg_color_list = []
    for c in bg_color:
      bg_color_list.append(c)

    grid_color = self.grid_color_button.get_rgba()
    grid_color_list = []
    for c in grid_color:
      grid_color_list.append(c)

    marker1_color = self.marker1_color_button.get_rgba()
    marker1_color_list = []
    for c in marker1_color:
      marker1_color_list.append(c)

    marker2_color = self.marker2_color_button.get_rgba()
    marker2_color_list = []
    for c in marker2_color:
      marker2_color_list.append(c)

    settings = self.db_session.query(self.Tbl).filter(self.Tbl.id == int(self.c_id)).first()
    if settings:
      settings.bg_color =  json.dumps(bg_color_list)
      settings.h_grids =  int(self.hor_grid.get_label())
      settings.v_grids = int(self.vert_grid.get_label())
      settings.grid_color =  json.dumps(grid_color_list)
      settings.marker1_width = int(self.marker1_width_button.get_label())
      settings.marker1_color =  json.dumps(marker1_color_list)
      settings.marker2_width = int(self.marker2_width_button.get_label())
      settings.marker2_color =  json.dumps(marker2_color_list)
      self.db_session.commit()
    self.app.charts[self.c_id].reload_chart()

  def remove_widgets(self,*args):
    grid = self.grid.get_children()
    for widgets in grid:
      self.grid.remove(widgets)

  def add_style(self, item,style):
    sc = item.get_style_context()
    for sty in style:
      sc.add_class(sty)

  def open_numpad(self,button,widget_obj,params,*args):
    numpad = ValueEnter(self,widget_obj,params)
    response = numpad.run()
    if response == Gtk.ResponseType.NO:
      pass
    else:
      pass
      #callback(args)
    numpad.destroy()

  def close_popup(self, *args):
    self.destroy()