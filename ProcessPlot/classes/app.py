import logging, os, time
from classes.data_manager import DataManager
from classes.ui import MainWindow
from classes.database import DataDb, SettingsDb
from classes.ui import MainWindow

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),  'Public')

class App(object):
  __log = logging.getLogger('ProcessPlot.classes.app')
  def __init__(self):
    self.data_db = DataDb()
    self.data_manager = DataManager(self)
    self.settings_db = SettingsDb()
    has_ui = True
    if has_ui:
      # build the UI and run the Gtk main loop
      self.main_window = MainWindow(self)
    else:
      self.__log.info("No UI, running headless")
      self.run_headless()

  def run_headless(self):
    print("Here is where you run command line version only")
    # simulate some main loop
    for x in range(5):
      print(f"No code written yet, closing in {5-x} second(s)")
      time.sleep(1)

