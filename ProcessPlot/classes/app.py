import logging, os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Gio
from classes.logger import *
from classes.chart import ChartArea
from classes.database import SettingsDb, DataDb
from classes.exceptions import *
from classes.chart import *
from classes.popup import LegendPopup

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),  'Public')

class App(Gtk.Window):
  __log = logging.getLogger('main.App')
  def __init__(self):
    self.data_db = DataDb()
    self.settings_db = SettingsDb()
    title = 'Process Plot'
    Gtk.Window.__init__(self, title=title)
    self.set_size_request(100, 100)
    self.set_default_size(1950, 1050)
    self.set_border_width(10)
    self.set_decorated(False)
    self.maximize()
    self.numCharts = 2
    cssProvider = Gtk.CssProvider()
    cssProvider.load_from_path(os.path.join(PUBLIC_DIR, 'css/style.css'))
    screen = Gdk.Screen.get_default()
    styleContext = Gtk.StyleContext()
    styleContext.add_provider_for_screen(screen, cssProvider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)
    self.window = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.big_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    self.titlebar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,height_request = 20)
    self.add(self.window)
    self.window.pack_start(self.titlebar,0,0,1)
    self.window.pack_start(self.big_box,1,1,1)
    #building trend window 
    self.trend_window = Gtk.EventBox()
    self.trend_window.set_above_child(True)
    sc = self.trend_window.get_style_context()
    sc.add_class('dialog-border')
    self.trend_window.connect("button_release_event",self.event_window_clicked)
    #adding widgets
    self.build_chart()
    self.build_titlebar()
    self.build_chart_ctrl()

  def build_titlebar(self,*args):

    sc = self.titlebar.get_style_context()
    sc.add_class('title-bar')

    self.pin_button = Gtk.Button(width_request = 20)
    self.pin_button.connect('clicked',self.open_legend_popup)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/legend.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.pin_button.add(image)
    self.titlebar.pack_start(self.pin_button,0,0,1)
    sc = self.pin_button.get_style_context()
    sc.add_class('ctrl-button')

    self.settings_button = Gtk.Button(width_request = 20)
    #self.settings_button.connect('clicked',self.open_legend_popup)
    p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR,'images/settings.png'), 20, -1, True)
    image = Gtk.Image(pixbuf=p_buf)
    self.settings_button.add(image)
    self.titlebar.pack_start(self.settings_button,0,0,1)
    sc = self.settings_button.get_style_context()
    sc.add_class('ctrl-button')


    selections = ["1","2","4","8","16"]
    self.number_of_charts = Gtk.ComboBoxText()
    self.number_of_charts.set_entry_text_column(0)
    self.number_of_charts.connect("changed", self.update_number_of_charts)
    found = 0
    for x in selections:
        self.number_of_charts.append_text(x)
    try:
      idx = selections.index(str(self.chart_panel.charts))
    except IndexError:
      idx = 0
    self.numCharts = int(selections[idx])  #error checking from stored value
    self.number_of_charts.set_active(idx)
    self.titlebar.pack_start(self.number_of_charts,0,0,1)

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

  def update_number_of_charts(self,*args):
    if self.numCharts != int(self.number_of_charts.get_active_text()):
      self.numCharts = int(self.number_of_charts.get_active_text())
      self.chart_panel.charts = self.numCharts
      self.chart_panel.build_charts()

  def build_chart(self,*args):
    self.chart_panel = ChartArea(self)
    self.trend_window.add(self.chart_panel)
    self.big_box.pack_start(self.trend_window,1,1,1)
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

  def open_legend_popup(self, button):
    popup = LegendPopup(self)
    response = popup.run()
    popup.destroy()

  def exit_app(self, *args):
    Gtk.main_quit()

  def event_window_clicked(self,*args):
    self.__log.info(f'Event window clicked')
