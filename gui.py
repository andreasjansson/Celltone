import wx
import threading

def remove_arg(f):
    return lambda x: f()

def compose(*args):
    return lambda: [arg() for arg in args]

class Gui:

    def __init__(self):
        self.on_play = None
        self.on_pause = None
        self.on_stop = None
        self.on_compile = None
        self.thread = GuiThread(self)
        
    def set_parts(self, parts):
        pass

    def show_parse_error(self, error):
        pass

    def show_log(self, items):
        pass

    def destroy(self):
        self.thread.frame.Destroy()
        wx.PostEvent(self.thread.frame.GetEventHandler(), wx.PaintEvent())

class GuiThread(threading.Thread):

    def __init__(self, gui):
        threading.Thread.__init__(self)
        self.gui = gui
        self.frame = None
        self.start()

    def run(self):
        app = wx.App(False)
        self.frame = wx.Frame(None, wx.ID_ANY, 'Hello World',
                              size = (200, 100))

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.play_button = wx.Button(self.frame, -1, "Play")
        self.pause_button = wx.Button(self.frame, -1, "Pause")
        button_sizer.Add(self.play_button)
        button_sizer.Add(self.pause_button)
        self.toggle_pause()

        self.frame.Bind(wx.EVT_BUTTON, remove_arg(
                compose(self.toggle_play, self.gui.on_play)), self.play_button)
        self.frame.Bind(wx.EVT_BUTTON, remove_arg(
                compose(self.toggle_pause, self.gui.on_pause)), self.pause_button)
        self.frame.Bind(wx.EVT_CLOSE, remove_arg(self.gui.on_close), self.frame)

        self.frame.SetSizerAndFit(button_sizer)
        self.frame.Show(True)

        app.MainLoop()

    def toggle_play(self):
        self.pause_button.Show()
        self.play_button.Hide()

    def toggle_pause(self):
        self.pause_button.Hide()
        self.play_button.Show()

