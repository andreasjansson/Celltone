import wx
import threading

gui_lock = threading.Lock()

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
        
    def set_parts(self, parts, time = 0):
        self.thread.debug_panel.parts_update = (parts, time)

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
        gui_lock.acquire()
        self.gui = gui
        self.frame = None
        self.start()

    def run(self):
        app = wx.App(False)
        self.frame = wx.Frame(None, wx.ID_ANY, 'Hello World',
                              size = (200, 100))

        frame_sizer = wx.BoxSizer(wx.VERTICAL)

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

        notebook = wx.Notebook(self.frame)
        self.debug_panel = DebugPanel(notebook)
        notebook.AddPage(self.debug_panel, 'Debugging')
        frame_sizer.Add(notebook)

        self.frame.SetSizerAndFit(frame_sizer)
        self.frame.Show(True)

        gui_lock.release()
        app.MainLoop()

    def toggle_play(self):
        self.pause_button.Show()
        self.play_button.Hide()

    def toggle_pause(self):
        self.pause_button.Hide()
        self.play_button.Show()


class DebugPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.parts_panels = {}

        self.parts_container = wx.Panel(self)
        self.parts_sizer = wx.BoxSizer(wx.VERTICAL)
        self.parts_container.SetSizer(self.parts_sizer)

        self.rules_container = wx.Panel(self)
        self.rules_sizer = wx.BoxSizer(wx.VERTICAL)
        self.rules_container.SetSizer(self.rules_sizer)

        timer_id = 101
        self.timer = wx.Timer(self, timer_id)
        self.timer.Start(100)
        wx.EVT_TIMER(self, timer_id, remove_arg(self.set_parts))

        self.parts_update = None

    def set_parts(self):

        if self.parts_update is None:
            return

        parts, time = self.parts_update
        self.parts_update = None

        to_be_updated = dict([(k, 1) for k in self.parts_panels.keys()])
        for name, panel in self.parts_panels.iteritems():
            del to_be_updated[name]
            if name not in to_be_updated:
                panel = PartsPanel(self, part)
                self.parts_panels[name] = panel
                self.parts_sizer.Add(panel)
            self.parts_panels[name].update(time)

        for name in to_be_updated.keys():
            self.parts_panels[name].update(time)
            panel.Destroy()
            del self.parts_panels[name]

class PartsPanel(wx.Panel):

    def __init__(self, parent, part):
        wx.Panel.__init__(self, parent)
        self.part = part

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)
        sizer.Add(wx.StaticText(self, -1, '%s = [' % self.part.name))
        self.numbers = []
        for note in self.part.notes:
            number = wx.StaticText(self, -1, note)
            sizer.Add(number)
            self.numbers.append(number)
            if note != self.parts.notes[-1]:
                sizer.Add(wx.StaticText(self, -1, ', '))
        sizer.Add(wx.StaticText(self, -1, ']'))

    def update(self, time):
        pass
