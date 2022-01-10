
import gi, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf
import re
import time

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),  'Public')

class CheckBoxWidget(object):
  def __init__(self, width,height,image,initial_val):
    self.height = height
    self.width = width
    self.img_checked = image
    self.initial_val = initial_val
    self.widget =Gtk.ToggleButton(width_request=self.width, height_request=self.height)
    self.build()

  def build(self):

    self.widget.connect("toggled", self.on_change)
    #p_buf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(PUBLIC_DIR, 'images/Check.png'), 30, -1, True)
    #self.img_checked = Gtk.Image(pixbuf=p_buf)
    self.set_initial_val(self.initial_val)

  def set_initial_val(self,i_val,*args):
    if i_val:
      self.widget.add(self.img_checked)
  
  def update_img(self,*args):
    temp = self.widget.get_children()
    for i in temp:
      self.widget.remove(i)
    if self.widget.get_active():
      self.widget.add(self.img_checked)
      self.widget.show_all()

  def on_change(self,*args):
    self.update_img()

  def return_status(self,*args):
    return self.widget.get_active()
  
  def return_self(self):
    return self.widget
