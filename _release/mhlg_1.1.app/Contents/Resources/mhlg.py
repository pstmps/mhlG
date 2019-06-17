import xxhash
import os
import glob
import datetime

import xml.etree.cElementTree as mhl
from xml.dom import minidom

import getpass
import socket

from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

import wx
import wx.adv

directory_name = ""


global pcount
global threadCOUNT

pcount = 0

class mhlGEN(wx.Frame):
    global threadCOUNT

    #----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "MHL GENERATOR")
        self.SetSize(wx.Size(400, 280))
        self.createMenu()

        panel = wx.Panel(self, wx.ID_ANY)

        button = wx.Button(panel, wx.ID_ANY, '...', (100, 100))
        self.start = wx.Button(panel, wx.ID_ANY, 'START', (100, 130))
        png = wx.Image('ufo.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        ufo = wx.StaticBitmap(panel, 1, png, (0,0), (4,4))

        #self.Pgauge = wx.Gauge(panel, range=20, size=(120, 25), style=wx.GA_HORIZONTAL)
        self.threadSEL = wx.Slider(panel,name='# of Threads', value= 64, minValue= 1, maxValue= 1024, style = wx.SL_HORIZONTAL| wx.SL_AUTOTICKS |wx.SL_LABELS)

        #self.threadSEL.Bind(wx.EVT_SLIDER, self.OnSliderScroll)

        button.Bind(wx.EVT_BUTTON, onButton)
        self.start.Bind(wx.EVT_BUTTON, self.start_conversion)

        sizer = wx.GridSizer(2,2,0,0)

        topSizer = wx.BoxSizer(wx.VERTICAL)
        titleSizer = wx.BoxSizer(wx.HORIZONTAL)

        inputTwoSizer   = wx.BoxSizer(wx.HORIZONTAL)
        inputThreeSizer   = wx.BoxSizer(wx.HORIZONTAL)
        inputThreadSizer = wx.BoxSizer(wx.HORIZONTAL)

        labelTwo = wx.StaticText(panel, wx.ID_ANY, 'Choose directory')
        labelThree = wx.StaticText(panel, wx.ID_ANY, 'Start generating mhl')
        labelThreads = wx.StaticText(panel, wx.ID_ANY, 'Number of Threads')

        titleSizer.Add(ufo, 0, wx.ALL, 5)

        inputTwoSizer.Add((20,20), 1, wx.EXPAND) # this is a spacer

        inputTwoSizer.Add(labelTwo, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

        inputThreeSizer.Add((20,20), 1, wx.EXPAND) # this is a spacer

        inputThreeSizer.Add(labelThree, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

        inputThreadSizer.Add((20, 20), 1, wx.EXPAND)  # this is a spacer

        inputThreadSizer.Add(labelThreads, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        sizer.AddMany( [
            (inputTwoSizer, 0, wx.ALIGN_RIGHT),
            (button, 0, wx.ALIGN_LEFT),
            #(inputThreadSizer, 0, wx.ALIGN_RIGHT),
            #(self.threadSEL, 10, wx.ALIGN_LEFT),
            #(self.Pgauge, 0, wx.ALIGN_LEFT),
            #((20, 20), 1, wx.EXPAND),
            (inputThreeSizer, 0, wx.ALIGN_RIGHT),
            (self.start, 0, wx.ALIGN_LEFT)
        ])

        #topSizer.Add((1,1), -1, wx.ALL)
        topSizer.Add(titleSizer, 0, wx.CENTER)
        topSizer.Add(wx.StaticLine(panel), 0, wx.ALL | wx.EXPAND, 5)
        topSizer.Add(labelThreads, 0, wx.CENTER)
        topSizer.Add(self.threadSEL, 0, wx.CENTER)
        topSizer.Add(wx.StaticLine(panel), 0, wx.ALL|wx.EXPAND, 5)
        topSizer.Add(sizer, 0, wx.ALL|wx.EXPAND, 5)
        topSizer.Add(wx.StaticLine(panel), 0, wx.ALL|wx.EXPAND, 5)

        self.SetSizeHints(400,150,500,400)
        panel.SetSizer(topSizer)


    def start_conversion(self, event):
        global threadCOUNT
        threadCOUNT = self.threadSEL.GetValue()
        print (threadCOUNT)

        #self.Pgauge.SetValue(0)
        filelist = []

        pool = ThreadPool(threadCOUNT)

        pcount = 0

        for filename in glob.iglob(directory_name + '**/**', recursive=True):
            if os.path.isfile(filename):
                filelist.append(filename)



        results = pool.map(self.hashIT, filelist)




        hashlist = mhl.Element("hashlist", version="1.0")
        creatorinfo = mhl.SubElement(hashlist, "creatorinfo")
        mhl.SubElement(creatorinfo, "name").text = ('mhlg v1.0')
        mhl.SubElement(creatorinfo, "username").text = (getpass.getuser())
        mhl.SubElement(creatorinfo, "hostname").text = (socket.gethostname())
        mhl.SubElement(creatorinfo, "startdate").text = (datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

        for result in results:
            hash = mhl.SubElement(hashlist, "hash")
            mhl.SubElement(hash, "file").text = (str(result[0]))
            mhl.SubElement(hash, "size").text = (str(result[1]))
            mhl.SubElement(hash, "lastmodificationdate").text = (str(result[2]))
            mhl.SubElement(hash, "xxhash64be").text = (str(result[3]))
            mhl.SubElement(hash, "hashdate").text = (str(result[4]))

        mhl.SubElement(creatorinfo, "finishdate").text = (datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

        xmlstr = minidom.parseString(mhl.tostring(hashlist)).toprettyxml(indent="    ")

        #print(xmlstr)
        print (os.path.basename(os.path.normpath(directory_name)))
        with open(directory_name + '/' + os.path.basename(os.path.normpath(directory_name)) +'_'+ datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S') + '.mhl' , "w") as f:
            f.write(xmlstr)

    def hashIT(self, hashpath):
        global pcount
        BLOCKSIZE = 65536
        x = xxhash.xxh64()
        with open(hashpath, 'rb') as infile:
            buf = infile.read(BLOCKSIZE)
            while len(buf) > 0:
                x.update(buf)

                #pcount += 1
                #self.Pgauge.SetValue(pcount)
                #if pcount % 10 == 0:
                #    wx.Yield()
                buf = infile.read(BLOCKSIZE)

        digest = x.hexdigest()
        #digest = 'a'
        fsize = os.path.getsize(hashpath)
        # ftime = time.gmtime(os.path.getmtime(hashpath))
        ftime = datetime.datetime.fromtimestamp(os.path.getmtime(hashpath)).strftime('%Y-%m-%dT%H:%M:%S')
        htime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        hashpath = hashpath.replace(directory_name + '/', '')

        # print (hashpath + ' ' + digest)
        return hashpath, fsize, ftime, digest, htime

    def createMenu(self):
        """ Create the application's menu """
        menubar = wx.MenuBar()
        helpMenu = wx.Menu()
        about_menu_item = helpMenu.Append(wx.NewId(), "About","Opens the About Box")
        self.Bind(wx.EVT_MENU, self.onAboutDlg, about_menu_item)
        menubar.Append(helpMenu, "About")
        self.SetMenuBar(menubar)


    def onAboutDlg(self, event):
        abICO = wx.Icon('ufo.ico', desiredWidth=200, desiredHeight=200)
        info = wx.adv.AboutDialogInfo()
        info.SetIcon(abICO)
        info.Name = "MHL GENERATOR"
        info.Version = "1.1.0 20190617"
        info.Copyright = "(C) 2019"
        info.Developers = ["Michael-Philipp Stiebing","m.stiebing@gmail.com","Icons by Chanut-is-Industries"]
        info.SetWebSite('https://paypal.me/mhlg?locale.x=de_DE','Support program development')

        wx.adv.AboutBox(info)

    def onClose(self, event):
        self.Close()


def onButton(event):
    dialog = wx.DirDialog(None, "Choose a directory:",style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
    if dialog.ShowModal() == wx.ID_OK:
        #print (dialog.GetPath())
        global directory_name
        directory_name = dialog.GetPath()

    dialog.Destroy()
    #print ("test")





# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frame = mhlGEN()

    frame.Show()
    app.MainLoop()





