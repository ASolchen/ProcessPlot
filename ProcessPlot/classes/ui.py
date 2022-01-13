import logging, os
from typing import Set
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Gio

from classes.logger import *
from classes.chart import ChartArea
from classes.exceptions import *
from classes.chart import *
from classes.popup import PenSettingsPopup, ConnectionSettingsPopup, PointSettingsPopup
from Public.widgets.checkbox import CheckBoxWidget

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),  'Public')

class MainWindow(Gtk.Window):
  __log = logging.getLogger('ProcessPlot.classes.ui')
  def __init__(self, app):
    self.app  = app
    self.db_session = app.settings_db.session
    self.db_model = app.settings_db.models['ui']
    #settings
    self.numCharts = 1
    self.dark_mode = False
    self.headless_mode = False
    self.screen_width = 1950
    self.screen_height = 1050
    #settings
    self.application_settings = Gtk.Settings.get_default()
    self.application_settings.set_property("gtk-application-prefer-dark-theme", self.dark_mode)
    title = 'Process Plot'
    Gtk.Window.__init__(self, title=title)
    self.connect("delete-event", self.exit_app)
    self.set_size_request(100, 100)
    self.set_default_size(1950, 1050)
    self.set_border_width(10)
    self.set_decorated(False)
    self.maximize()
    cssProvider = Gtk.CssProvider()
    cssProvider.load_from_path(os.path.join(PUBLIC_DIR, 'css/style.css'))
    screen = Gdk.Screen.get_default()
    styleContext = Gtk.StyleContext()
    styleContext.add_provider_for_screen(screen, cssProvider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)
    self.window = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.settings_popout= Gtk.Box(orientation=Gtk.Orientation.VERTICAL, width_request = 0)
    self.big_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    self.titlebar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request = 20)
    self.add(self.window)
    self.window.pack_start(self.titlebar,0,0,1)
    self.window.pack_start(self.big_box,1,1,1)
    self.big_box.pack_start(self.settings_popout,0,0,1)
    #building trend window 
    #adding widgets
    self.build_chart()
    self.build_titlebar()
    self.build_chart_ctrl()
    self.show_all()
    self.load_settings()
    self.update_settings()
    Gtk.main()


  def load_settings(self):
    Tbl = self.db_model
    settings = self.db_session.query(Tbl).order_by(Tbl.id.asc()).first() # load the last saved settings
    if settings:
      self.dark_mode = settings.dark_mode
      self.numCharts = settings.charts
      self.headless_mode = settings.headless
      self.screen_width = settings.screen_width
      self.screen_height = settings.screen_height

  def update_settings(self):
    #this method is for updating settings after app has built
    self.update_number_of_charts(self.numCharts)
    self.application_settings.set_property("gtk-application-prefer-dark-theme", self.dark_mode)


  def save_settings(self):
    Tbl = self.db_model
    settings = self.db_session.query(Tbl).order_by(Tbl.id.asc()).first() # save the current settings
    if settings:
      settings.dark_mode = self.dark_mode
      settings.charts = self.numCharts
      settings.headless = self.headless_mode
      settings.screen_width = self.screen_width
      settings.screen_height = self.screen_height
    else:
      self.db_session.add(Tbl(dark_mode=self.dark_mode, charts=self.numCharts, headless = self.headless_mode,screen_height = self.screen_height, screen_width = self.screen_width  ))
    self.db_session.commit()

  
  def build_titlebar(self,*args):

    sc = self.titlebar.get_style_context()
    sc.add_class('title-bar')

    self.pin_button = Gtk.Button(width_request = 20)
    self.pin_button.connect('clicked',self.build_settings_popout)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/settings.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.pin_button.add(image)
    self.titlebar.pack_start(self.pin_button,0,0,1)
    sc = self.pin_button.get_style_context()
    sc.add_class('ctrl-button')

    title = Gtk.Label(label = 'ProcessPlot')
    sc = title.get_style_context()
    sc.add_class('text-black-color')
    sc.add_class('font-18')
    sc.add_class('font-bold')
    self.titlebar.pack_start(title,1,1,1)

    self.exit_button = Gtk.Button(width_request = 15)
    self.exit_button.connect('clicked',self.exit_app)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Close.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.exit_button.add(image)
    self.titlebar.pack_start(self.exit_button,0,0,1)
    sc = self.exit_button.get_style_context()
    sc.add_class('exit-button')

  def get_number_of_charts(self,chart_select):
    self.numCharts = int(chart_select.get_active_text())
    self.update_number_of_charts(self.numCharts)

  def get_dark_toggle(self,t_button):
    self.dark_mode = bool(t_button.get_active())
    self.save_settings()
    self.update_settings()

  def update_number_of_charts(self,val):
    self.app.charts_number = 0
    self.chart_panel.charts = val
    self.chart_panel.build_charts()
    self.save_settings()

  def build_settings_popout(self,*args):

    settings_popout_width = 300
    self.settings_window = Gtk.Box(width_request=settings_popout_width,orientation=Gtk.Orientation.VERTICAL)
    self.settings_title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=20,width_request=settings_popout_width)

    self.popups = {
      "pen": PenSettingsPopup,
      "point": PointSettingsPopup,
      "connection": ConnectionSettingsPopup,
    }

    #header
    title = Gtk.Label(label = 'Settings')
    sc = title.get_style_context()
    sc.add_class('text-black-color')
    sc.add_class('font-18')
    sc.add_class('font-bold')
    self.settings_title_bar.pack_start(title,1,1,1)
    self.pin_button = Gtk.Button(width_request = 20)
    self.pin_button.connect('clicked',self.remove_settings_popout)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale('./ProcessPlot/Public/images/pin.png', 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.pin_button.add(image)
    self.settings_title_bar.pack_start(self.pin_button,0,0,1)
    sc = self.pin_button.get_style_context()
    sc.add_class('ctrl-button')
    self.settings_window.pack_start(self.settings_title_bar,0,0,1)

    self.ctrl_button_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request=30,width_request=300)

    self.conn_button = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Connection.png'), 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.conn_button.add(image)
    self.ctrl_button_bar.add(self.conn_button)
    sc = self.conn_button.get_style_context()
    sc.add_class('ctrl-button')
    self.conn_button.connect('clicked',self.open_popup,"connection",self.app)

    self.point_button = Gtk.Button(width_request = 30)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Tag.png'), 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.point_button.add(image)
    self.ctrl_button_bar.add(self.point_button)
    sc = self.point_button.get_style_context()
    sc.add_class('ctrl-button')
    self.point_button.connect('clicked',self.open_popup,"point",self.app)
 
    self.pen_settings_button = Gtk.Button(width_request = 30)

    self.pen_settings_button.connect('clicked',self.open_popup,"pen",self.app)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Create.png'), 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.pen_settings_button.add(image)
    self.ctrl_button_bar.add(self.pen_settings_button)
    sc = self.pen_settings_button.get_style_context()
    sc.add_class('ctrl-button')

    self.settings_window.pack_start(self.ctrl_button_bar,0,0,1)

    divider = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sc = divider.get_style_context()
    sc.add_class('Hdivider')
    self.settings_window.pack_start(divider,0,0,1)
    #Settings Data

    self.settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,width_request=settings_popout_width,height_request = 800)
    scroll = Gtk.ScrolledWindow(height_request = 800)
    lbl = Gtk.Label(label = 'App Settings')
    sc = lbl.get_style_context()
    sc.add_class('settings-description')
    self.settings_data = Gtk.Box(width_request=settings_popout_width,orientation=Gtk.Orientation.VERTICAL,height_request = 800, spacing = 10)
    self.settings_data.pack_start(lbl,0,0,1)
    scroll.add(self.settings_data)
    self.settings_box.add(scroll)
    self.settings_window.pack_start(self.settings_box,1,1,1)
    
    settings1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,width_request=settings_popout_width)
    lbl = Gtk.Label('Number of Charts')
    sc = lbl.get_style_context()
    sc.add_class('settings-description')
    settings1.pack_start(lbl,1,1,1)
    selections = ["1","2","4","8","16"]
    self.number_of_charts = Gtk.ComboBoxText()
    self.number_of_charts.set_entry_text_column(0)
    self.number_of_charts.connect("changed", self.get_number_of_charts)
    for x in selections:
        self.number_of_charts.append_text(x)
    try:
      idx = selections.index(str(self.numCharts))
    except IndexError:
      idx = 0
    self.number_of_charts.set_active(idx)
    settings1.pack_start(self.number_of_charts,0,0,1)
    self.settings_data.pack_start(settings1,0,0,1)

    settings2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,width_request=settings_popout_width)
    lbl = Gtk.Label('App Theme Dark')
    sc = lbl.get_style_context()
    sc.add_class('settings-description')
    settings2.pack_start(lbl,1,1,1)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    wid =CheckBoxWidget(30,30,image,self.dark_mode)
    t_button = wid.return_self()
    t_button.connect("toggled", self.get_dark_toggle)
    settings2.pack_start(t_button,0,0,1)
    self.settings_data.pack_start(settings2,0,0,1)

    settings3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,width_request=settings_popout_width)
    lbl = Gtk.Label('Run App Headless')
    sc = lbl.get_style_context()
    sc.add_class('settings-description')
    settings3.pack_start(lbl,1,1,1)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    wid =CheckBoxWidget(30,30,image,self.headless_mode)
    t_button = wid.return_self()
    #t_button.connect("toggled", self.get_dark_toggle)
    settings3.pack_start(t_button,0,0,1)
    self.settings_data.pack_start(settings3,0,0,1)
    
    self.settings_popout.pack_start(self.settings_window,1,1,1)
    self.big_box.show_all()
  
  def remove_settings_popout(self,*args):
    wid = self.settings_popout.get_children()
    for item in wid:
      self.settings_popout.remove(item)
    self.big_box.show_all()
  
  def build_chart(self,*args):
    self.chart_panel = ChartArea(self.app)
    self.big_box.pack_start(self.chart_panel,1,1,1)
    self.big_box.show_all()

  def build_chart_ctrl(self):
    trend_control_panel = Gtk.Box(width_request=40,height_request=400,orientation=Gtk.Orientation.VERTICAL)
    self.pan_button = Gtk.Button(width_request = 30)
    self.pan_button.connect('clicked',self.exit_app,None)
    #self.pan_button.connect('clicked',self.setup_tags,None)
    #self.pan_button.set_sensitive(False)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/pan.png'), 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.pan_button.add(image)
    trend_control_panel.add(self.pan_button)
    sc = self.pan_button.get_style_context()
    sc.add_class('ctrl-button')

    self.chart_marker_button = Gtk.Button(width_request = 30)
    #self.chart_marker_button.connect('clicked',self.setup_tags,None)
    #self.chart_marker_button.set_sensitive(False)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/ChartMarkers.png'), 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.chart_marker_button.add(image)
    trend_control_panel.add(self.chart_marker_button)
    sc = self.chart_marker_button.get_style_context()
    sc.add_class('ctrl-button')

    self.play_button = Gtk.Button(width_request = 30)
    #self.play_button.connect('clicked',self.setup_tags,None)
    #self.play_button.set_sensitive(False)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/play.png'), 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.play_button.add(image)
    trend_control_panel.add(self.play_button)
    sc = self.play_button.get_style_context()
    sc.add_class('ctrl-button')

    self.stop_button = Gtk.Button(width_request = 30)
    #self.stop_button.connect('clicked',self.setup_tags,None)
    #self.stop_button.set_sensitive(False)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/stop.png'), 30, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.stop_button.add(image)
    trend_control_panel.add(self.stop_button)
    sc = self.stop_button.get_style_context()
    sc.add_class('ctrl-button')
    
    self.big_box.pack_start(trend_control_panel,0,0,1)
 
  def open_popup(self, button,popup_key,app):
    popup = self.popups[popup_key](self,app)
    response = popup.run()
    popup.destroy()

  def exit_app(self, *args):
    Gtk.main_quit()
