import wx
import wx.lib.dialogs
from collections import namedtuple
import os
from PIL import Image
import numpy as np
import threading
import time
from Transfer import *


_ = wx.GetTranslation


imgformat = "jpg (*.jpg)|*.jpg|" \
            "png (*.png)|*.png|" \
            "jpeg (*.jpeg)|*.jpeg|" \
            "bmp (*.bmp)|*.bmp|" \
            "All files (*.*)|*.*"

pthformat = "pth (*.pth)|*.pth|"\
            "All files (*.*)|*.*"


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(600, -1))
        self.lang_config = wx.Config()
        self.__lang_init()

        self.img_cont = None
        self.img_style = None
        self.model = None
        self.img_out = None

        self.timer = wx.Timer(self)

        filemenu = wx.Menu()
        self.menuExit = filemenu.Append(wx.ID_EXIT, item=_("E&xit \tCtrl+Q"), helpString=_("退出程序"))


        helpmenu = wx.Menu()
        self.menuhelpdoc = helpmenu.Append(wx.ID_HELP, item=_("Help \tF1"), helpString=_("Help"))

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, title=_("&File"))
        menuBar.Append(helpmenu, title=_("&Help"))
        self.SetMenuBar(menuBar)

        self.__DoLayout()
        self.__Binds()

    def __DoLayout(self):
        """界面布局;"""
        static_font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
        Size = namedtuple("Size", ['x', 'y'])
        s = Size(100, 50)

        self.SetBackgroundColour(wx.Colour(100, 100, 100, alpha=wx.ALPHA_OPAQUE))  # 设置主体的背景颜色

        self.btn_cont = wx.Button(self, -1, label=_("点击导入要转换风格的图片"), size=(1.5 * s.x, s.y))
        self.btn_cont.SetFont(static_font)
        self.btn_cont.SetToolTip(_("choose content image"))
        self.btn_cont.SetBackgroundColour(wx.Colour(200, 200, 200))
        self.btn_cont.SetForegroundColour(wx.Colour(0, 0, 255))

        self.btn_style = wx.Button(self, -1, label=_("点击导入图片风格"), size=(1.5 * s.x, s.y))
        self.btn_style.SetFont(static_font)
        self.btn_style.SetToolTip(_("choose sytle image"))
        self.btn_style.SetBackgroundColour(wx.Colour(200, 200, 200))
        self.btn_style.SetForegroundColour(wx.Colour(0, 0, 255))

        self.btn_run = wx.Button(self, -1, label=_("开始转换"), size=(1.5 * s.x, s.y))
        self.btn_run.SetFont(static_font)
        self.btn_run.SetToolTip(_("run program"))
        self.btn_run.SetBackgroundColour(wx.Colour(200, 200, 200))
        self.btn_run.SetForegroundColour(wx.Colour(0, 0, 255))

        self.img_cont_win = wx.StaticBitmap(self, -1, size=(256, 256))
        self.img_cont_win.SetToolTip(_("content image display"))

        self.img_style_win = wx.StaticBitmap(self, -1, size=(256, 256))
        self.img_style_win.SetToolTip(_("sytle image display"))

        self.img_out_win = wx.StaticBitmap(self, -1, size=(512, 512))
        self.img_out_win.SetToolTip(_("output image display"))

        self.out_log = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_RICH, size=(8 * s.x, 3 * s.y))
        self.out_log.SetToolTip(_("Log"))

        self.sizer0 = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer1.Add(self.btn_cont, 1, wx.EXPAND | wx.ALL)
        self.sizer1.Add(self.btn_style, 1, wx.EXPAND | wx.ALL)
        self.sizer1.Add(self.btn_run, 1, wx.EXPAND | wx.ALL)

        self.sizer2.Add(self.img_cont_win, 0)
        self.sizer2.Add(self.img_style_win, 1)

        self.sizer3.Add(self.sizer2, 0)
        self.sizer3.Add(self.img_out_win, 0)

        self.sizer0.Add(self.sizer1, 0, wx.EXPAND)
        self.sizer0.Add(self.sizer3)
        self.sizer0.Add(self.out_log)

        self.SetSizer(self.sizer0)
        self.SetAutoLayout(1)
        self.sizer0.Fit(self)

        self.StatusBar = ProgressStatusBar(self)
        self.Show()

    def __Binds(self):
        """绑定函数;"""
        self.Bind(wx.EVT_TIMER, self.NextFrame, self.timer)
        self.img_out_win.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        self.Bind(wx.EVT_MENU, self.OnExit, self.menuExit)
        self.Bind(wx.EVT_MENU, self.set_hyper, self.menuhyper)

        self.btn_cont.Bind(wx.EVT_BUTTON, self.choose_cont)
        self.btn_style.Bind(wx.EVT_BUTTON, self.choose_style)
        self.btn_run.Bind(wx.EVT_BUTTON, self.run)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.btn_run.Bind(wx.EVT_BUTTON, self.run)

    def __lang_init(self):
        """语言设置初始化;"""
        language = self.lang_config.Read('lang', 'LANGUAGE_DEFAULT')

        self.locale = wx.Locale(getattr(wx, language))

        path = os.path.abspath("./locale") + os.path.sep
        self.locale.AddCatalogLookupPathPrefix(path)
        self.locale.AddCatalog("Detector")

    def OnCloseWindow(self, evt):
        """关闭GUI窗口;"""
        self.Destroy()

    def choose_cont(self, evt):
        """选择内容图片;"""
        self.img_cont = self.choose_file(imgformat)
        if self.img_cont is not None:
            bmp = self.load_img(self.img_cont)
            self.img_cont_win.SetBitmap(bmp)
            self.Refresh()  # 刷新窗口 显示图片

    def choose_style(self, evt):
        """选择风格图片;"""
        self.img_style = self.choose_file(pthformat)


    def load_img(self, fn):
        """加载图片;"""
        if isinstance(fn, str):
            img = Image.open(fn)
            img = img.resize((256, 256))
        elif isinstance(fn, Image.Image):
            img = fn
        width, height = img.size
        img = img.tobytes()
        arr = np.array(img)

        bmp = wx.ImageFromBuffer(width, height, arr).ConvertToBitmap()
        return bmp

    def display_out(self, img):
        """在图片输出框上显示结果图片;"""
        bmp = self.load_img(img)
        self.img_out_win.SetBitmap(bmp)
        self.Refresh()

    def run(self, evt):
        t0 = time.time()
        print(self.num_steps, self.style_weight, self.content_weight, type(self.num_steps))

        if not self.StatusBar.busy:
            self.status2busy()
            Transfer(self.img_style, self.img_cont, "./data")
            self.timer.Start(1000)


    def status2busy(self):
        """使状态栏进度条工作,其他按钮锁定;"""
        self.btn_cont.Disable()
        self.btn_style.Disable()
        self.StatusBar.PushStatusText(_("Busy"))
        self.btn_run.SetLabel(_("Stop"))
        self.StatusBar.busy = True
        self.StatusBar.work()

    def status2idle(self):
        """使状态栏进度条停止工作,解锁其他按钮;"""
        self.btn_cont.Enable()
        self.btn_style.Enable()
        self.StatusBar.PushStatusText(_("Idle"))
        self.btn_run.SetLabel(_("点击开始转换"))
        self.StatusBar.busy = False
        self.StatusBar.work()

    def NextFrame(self, evt):
        """刷新画面;"""
        if self.img_out == None:
            return
        else:
            self.display_out(self.img_out)

    def OnEraseBackground(self, event):
        """ Background will never be erased, this avoids flickering """
        return


    def LogMsg(self, msg):
        """在日志框中输出信息;"""
        self.out_log.AppendText(msg + "\n")

    def OnExit(self, evt):
        """退出程序;"""
        wx.Abort()

    def choose_file(self, wildcard):
        """选择文件;"""
        dlg = wx.FileDialog(
            self, message="选择文件",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE |  # wx4.0
                  wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST |
                  wx.FD_PREVIEW
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            dlg.Destroy()
            return paths[0]
        else:
            return None

if __name__ == '__main__':
    app = wx.App(False)
    app.SetAppName("Style")
    frame = MainWindow(None, '快速图像风格迁移')
    app.MainLoop()
