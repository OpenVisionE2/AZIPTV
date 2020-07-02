#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from enigma import *
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap, NumberActionMap
from Components.MenuList import MenuList
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Tools.Directories import fileExists
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from Components.Label import Label
from Components.Sources.List import List
import re
import os
import sys
from os import system, listdir, statvfs, popen, makedirs, stat, major, minor, path, access
from enigma import eTPM, eTimer, eServiceReference, iPlayableService
from Components.AVSwitch import AVSwitch
from Components.SystemInfo import SystemInfo
import urllib
from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry, ConfigText
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.HardwareInfo import HardwareInfo
from Components.NimManager import nimmanager, getConfigSatlist
from Components.Console import Console
from Components.ProgressBar import ProgressBar
import time
from Tools.HardwareInfo import HardwareInfo
from Components.VolumeControl import VolumeControl
config.AZIPTV = ConfigSubsection()
config.AZIPTV.Scaling = ConfigSelection(default='Just Scale', choices=['Just Scale', 'Pan&Scan', 'Pillarbox'])

class IPTV(Screen):
    skin = '\n\t\t<screen position="center,center" size="725,460" title="AzIPTV v.1.0" flags="wfNoBorder" >\n\t\t<widget source="menu" render="Listbox" position="10,50" size="475,400" scrollbarMode="showOnDemand" >\n\t\t\t<convert type="TemplatedMultiContent">\n\t\t\t\t{"template": [\n\t\t\t\t\t\tMultiContentEntryText(pos = (70, 10), size = (400, 38), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel\n\t\t\t\t\t\tMultiContentEntryText(pos = (65, 29), size = (400, 17), font=1, flags = RT_HALIGN_LEFT, text = 2), # index 3 is the Description\n\t\t\t\t\t\tMultiContentEntryPixmapAlphaTest(pos = (1, 1), size = (48, 48), png = 3), # index 4 is the pixmap\n\t\t\t\t\t],\n\t\t\t\t"fonts": [gFont("Regular", 21),gFont("Regular", 14)],\n\t\t\t\t"itemHeight": 50\n\t\t\t\t}\n\t\t\t</convert>\n\t\t</widget>\n\t\t<widget name="menu1" position="505,50" size="200,250" scrollbarMode="showOnDemand" />\n\t\t<widget name="infoM0" position="10,10" zPosition="2" size="455,40" font="Regular;26" foregroundColor="#ffffff" transparent="0" halign="center" valign="center" />\n\t\t<widget name="infoM1" position="485,10" zPosition="2" size="220,40" font="Regular;26" foregroundColor="#ffffff" transparent="0" halign="center" valign="center" />\n\t\t<widget name="l001" position="80,95" zPosition="1" size="370,1" alphatest="on" />\n\t\t<widget name="l002" position="80,145" zPosition="1" size="370,1" alphatest="on" />\n\t\t<widget name="l003" position="80,195" zPosition="1" size="370,1" alphatest="on" />\n\t\t<widget name="l004" position="80,245" zPosition="1" size="370,1" alphatest="on" />\n\t\t<widget name="l005" position="80,295" zPosition="1" size="370,1" alphatest="on" />\n\t\t<widget name="l006" position="80,345" zPosition="1" size="370,1" alphatest="on" />\n\t\t<widget name="l007" position="80,395" zPosition="1" size="370,1" alphatest="on" />\n\t\t<widget name="l008" position="80,445" zPosition="1" size="370,1" alphatest="on" />\n\t\t<widget name="picon" position="545,340" zPosition="1" size="100,60" alphatest="on" />\n\t\t<widget name="infoM2" position="485,410" zPosition="2" size="220,50" font="Regular;24" foregroundColor="#ffffff" transparent="0" halign="center" valign="center" />\n\t\t<widget name="text2"\t\tposition="0,0"\tfont="Regular;24" size="710,25"\t halign="center" />\n\t\t<widget name="start_progress" position="45,27" size="620,15" zPosition="2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/Ico/progress_big3.png" backgroundColor="#333333" />\n\t\t</screen>'

    def __init__(self, isAutostart, session, args = 0):
        Screen.__init__(self, session)
        self.session = session
        self.Console = Console()
        self.current_service = self.session.nav.getCurrentlyPlayingServiceReference()
        selectable_nims = []
        for nim in nimmanager.nim_slots:
            if nim.config_mode == 'nothing':
                continue
            if nim.config_mode == 'advanced' and len(nimmanager.getSatListForNim(nim.slot)) < 1:
                continue
            if nim.config_mode in ('loopthrough', 'satposdepends'):
                root_id = nimmanager.sec.getRoot(nim.slot_id, int(nim.config.connectedTo.value))
                if nim.type == nimmanager.nim_slots[root_id].type:
                    continue
            if nim.isCompatible('DVB-S'):
                selectable_nims.append((str(nim.slot), nim.friendly_full_description))

        self.select_nim = ConfigSelection(choices=selectable_nims)
        self.feid = 0
        if self.select_nim.value != '':
            self.feid = int(self.select_nim.value)
        self.frontend = self.OpenFrontend()
        if self.frontend is None:
            self.oldref = self.session.nav.getCurrentlyPlayingServiceReference()
            self.session.nav.stopService()
            if not self.frontend:
                if session.pipshown:
                    session.pipshown = False
                    del session.pip
                    if not self.openFrontend():
                        self.frontend = None
        self.session.nav.playService(None)
        self.switchmode = 0
        self.showhide = 0
        self['menu'] = List([])
        self['actions'] = NumberActionMap(['MediaPlayerActions', 'SetupActions', 'DirectionActions'], {'menu': self.Konfig,
         'ok': self.ok,
         'cancel': self.sakri,
         'up': self.keyUp,
         'down': self.keyDown,
         'left': self.keyLeft,
         'right': self.keyRight,
         'nextBouquet': self.ZapUp,
         'prevBouquet': self.ZapDown,
         '1': self.keyNumberGlobal,
         '2': self.keyNumberGlobal,
         '3': self.keyNumberGlobal,
         '4': self.keyNumberGlobal,
         '5': self.keyNumberGlobal,
         '6': self.keyNumberGlobal,
         '7': self.keyNumberGlobal,
         '8': self.keyNumberGlobal,
         '9': self.keyNumberGlobal,
         '0': self.keyNumberGlobal}, -2)
        self['text2'] = Label(_('Loading...Please Wait'))
        self['start_progress'] = ProgressBar()
        self['infoM0'] = Label()
        self['infoM1'] = Label()
        self['infoM2'] = Label()
        self['l001'] = Pixmap()
        self['l002'] = Pixmap()
        self['l003'] = Pixmap()
        self['l004'] = Pixmap()
        self['l005'] = Pixmap()
        self['l006'] = Pixmap()
        self['l007'] = Pixmap()
        self['l008'] = Pixmap()
        self['picon'] = Pixmap()
        self.TestCounter = 0
        self.playstarted = False
        self.DVBCATimer = eTimer()
        self.DVBCATimer.callback.append(self.Prepare)
        buffersize = 512
        try:
            myfile = open('/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/config')
            for line in myfile.readlines():
                if line[0:1] != '#':
                    ipos = ipos1 = 0
                    ipos = line.find('<buffersize>')
                    ipos1 = line.find('</buffersize>')
                    if ipos != '' and ipos1 != '' and ipos1 > ipos:
                        buffersize = int(line[ipos + 12:ipos1])

        except:
            print('Error reading cfg file.')

        if buffersize < 128:
            buffersize = 128
        hw_type = HardwareInfo().get_device_name()
        if hw_type == 'minime' or hw_type == 'me':
            self.cmd0 = 'rmfp_player -dram 0 -ve 0 -vd 0 -ae 0 -no_disp -prebuf '
        if hw_type == 'elite' or hw_type == 'premium' or hw_type == 'premium+' or hw_type == 'ultra':
            self.cmd0 = 'rmfp_player -dram 1 -ve 1 -vd 0 -ae 0 -no_disp -prebuf '
        self.cmd0 = self.cmd0 + str(buffersize) + ' -detect_limit 100 -resetvcxo -no_close -oscaler spu -nosubs '
        self.showhide = 0
        self['menu1'] = MenuList([])
        self['menu'] = List([])
        self.onLayoutFinish.append(self.startup)

    def startup(self):
        dat = '/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/Lists/bouquets'
        n = 0
        self.list2 = []
        try:
            f = open(dat, 'r')
            lines = f.readlines()
            for line in lines:
                nn = str(n) + '. '
                self.list2.append(nn + str(line))
                n += 1

        except Exception:
            print('Error reading bouquets file.')

        self['menu1'].setList(self.list2)
        self['infoM0'].setText('ALL Channels')
        self['infoM1'].setText('Bouquets :')
        picture = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/Ico/line1.png')
        self['l001'].instance.setPixmap(picture)
        self['l002'].instance.setPixmap(picture)
        self['l003'].instance.setPixmap(picture)
        self['l004'].instance.setPixmap(picture)
        self['l005'].instance.setPixmap(picture)
        self['l006'].instance.setPixmap(picture)
        self['l007'].instance.setPixmap(picture)
        self['l008'].instance.setPixmap(picture)
        self.PostaviLista(0)
        self['menu1'].selectionEnabled(0)
        azplay_vctrl = VolumeControl.instance
        self.azplay_currebtvol = azplay_vctrl.volctrl.getVolume()
        self.azplay_ismute = azplay_vctrl.volctrl.isMuted()
        self.Prepare()

    def Prepare(self):
        self['infoM0'].hide()
        self['infoM1'].hide()
        self.TestCounter += 1
        self['start_progress'].setValue(self.TestCounter * 4)
        try:
            tmpfile = open('/proc/player', 'rb')
            line = tmpfile.readline()
            tmpfile.close()
        except IOError:
            print('Error updateMsg')

        if int(line[:-1]) == 1:
            print('StopService - DONE ! (', self.TestCounter, ')')
            self['start_progress'].setValue(100)
            self.DVBCATimer1 = eTimer()
            self.DVBCATimer1.callback.append(self.Prepare1)
            self.DVBCATimer1.start(100, True)
        elif self.TestCounter < 49:
            self.DVBCATimer.start(100, True)
        elif int(line[:-1]) != 1:
            self.close()

    def Prepare1(self):
        self.switchmode = 1
        self['infoM0'].show()
        self['infoM1'].show()
        self['text2'].hide()
        self['start_progress'].hide()
        open('/proc/player', 'w').write('2')

    def keyNumberGlobal(self, number):
        try:
            self['infoM0'].setText(str(self.list2[number])[3:])
            self.PostaviLista(number)
        except Exception as e:
            print(str(e))
            return

    def PostaviLista(self, number):
        okpng = LoadPixmap(cached=True, path='/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/Ico/tv11.png')
        enc = 'iso-8859-1'
        dat = '/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/Lists/' + str(number) + '.m3u'
        self.list = []
        self.list1 = []
        self.listp = []
        n = 0
        try:
            f = open(dat, 'r')
            lines = f.readlines()
            for line in lines:
                try:
                    data = line.decode(enc)
                    line = data.encode('utf-8')
                except Exception:
                    print('Error enciding utf-8 filename.')

                if str(line)[:7] == '#EXTM3U':
                    continue
                if str(line)[:7] == '#EXTINF':
                    n += 1
                    nn = '000' + str(n)
                    nn = nn[len(nn) - 3:] + '. '
                    self.list.append((_(nn + str(line)[10:]),
                     n,
                     _(' '),
                     okpng))
                    newstr = str(line)[10:] + '.png'
                    newstr = newstr.replace('\n', '')
                    if str(newstr)[:1] == ' ':
                        newstr = newstr[1:]
                    if str(newstr)[:1] == ' ':
                        newstr = newstr[1:]
                    if str(newstr)[:1] == ' ':
                        newstr = newstr[1:]
                    self.listp.append(newstr)
                if str(line)[:1] != '#':
                    self.list1.append(str(line))

        except Exception:
            print('Error reading chlist file.')

        self['menu'].setList(self.list)
        self.ListCount = n
        self.ShowPicon(0)

    def ok(self):
        if self.switchmode == 0:
            return
        azplay_vctrl = VolumeControl.instance
        if self.azplay_ismute == False:
            value = self.azplay_currebtvol
            azplay_vctrl.volctrl.setVolume(value, value)
            azplay_vctrl.volSave()
            azplay_vctrl.volumeDialog.setValue(value)
        time.sleep(0.1)
        if os.path.exists('/tmp/rmfp.cmd2'):
            os.remove('/tmp/rmfp.cmd2')
        for n in range(0, 8):
            try:
                f = open('/tmp/rmfp.cmd2', 'wb')
                try:
                    f.write('100\n')
                finally:
                    f.close()

            except Exception as e:
                print(str(e))

            if os.path.exists('/tmp/rmfp.cmd2'):
                break
            time.sleep(0.05)

        hdparm = os.popen('killall rmfp_player')
        time.sleep(0.1)
        cur = self['menu'].getCurrent()
        if cur:
            link = self.list1[int(cur[1]) - 1]
            link = link[:len(link) - 1]
            cmd = self.cmd0 + "'" + link + "' &"
            os.popen(cmd)
            print('[IPTV cmd] ' + cmd)
            self.playstarted = True
            self.HDDTimer1 = eTimer()
            self.HDDTimer1.callback.append(self.sakri)
            self.HDDTimer1.start(2000, True)

    def sakri(self):
        if self.playstarted == True:
            if config.AZIPTV.Scaling.value == 'Just Scale':
                cmd = 223
            if config.AZIPTV.Scaling.value == 'Pan&Scan':
                cmd = 224
            if config.AZIPTV.Scaling.value == 'Pillarbox':
                cmd = 225
            if cmd > 0:
                self.SendCMD2(-1, cmd)
            time.sleep(0.11)
            self.session.openWithCallback(self.ClBack1, HideScr, 1)
        else:
            self.quit()

    def SendCMD2(self, k1, k2):
        if k1 >= 0:
            if os.path.exists('/tmp/rmfp.in2'):
                os.remove('/tmp/rmfp.in2')
            if os.path.exists('/tmp/rmfp.cmd2'):
                os.remove('/tmp/rmfp.cmd2')
            cmd = 'echo ' + str(k1) + ' > /tmp/rmfp.in2;echo ' + str(k2) + ' > /tmp/rmfp.cmd2'
            os.popen(cmd)
        else:
            if os.path.exists('/tmp/rmfp.cmd2'):
                os.remove('/tmp/rmfp.cmd2')
            os.popen('echo ' + str(k2) + ' > /tmp/rmfp.cmd2')

    def ClBack1(self, komanda):
        if komanda[:10] == '*DirectCh*':
            chno = komanda[10:]
            self.DirectCh(chno)
        if komanda == '*Exit*':
            self.quit()
        if komanda == 'Ch+':
            self.keyDown()
            self.ChZap()
        if komanda == 'Ch-':
            self.keyUp()
            self.ChZap()

    def DirectCh(self, chno):
        sel = int(chno)
        print('[Chanel No.:] ' + str(sel))
        if sel >= self.ListCount:
            sel = self.ListCount - 1
        self['menu'].setIndex(sel - 1)
        sel = self['menu'].getIndex()
        self.ShowPicon(sel)
        self.ChZap()

    def ChZap(self):
        hdparm = os.popen('killall rmfp_player')
        self.HDDTimer1 = eTimer()
        self.HDDTimer1.callback.append(self.ChZap1)
        self.HDDTimer1.start(100, True)

    def ChZap1(self):
        cur = self['menu'].getCurrent()
        if cur:
            link = self.list1[int(cur[1]) - 1]
            link = link[:len(link) - 1]
            cmd = 'rmfp_player -dram 0 -ve 0 -vd 3 -ae 0 -prebuf 512 ' + link + ' &'
            os.popen(cmd)
            self.HDDTimer1 = eTimer()
            self.HDDTimer1.callback.append(self.sakri)
            self.HDDTimer1.start(1000, True)

    def quit(self):
        if self.switchmode == 0:
            return
        time.sleep(0.1)
        if os.path.exists('/tmp/rmfp.cmd2'):
            os.remove('/tmp/rmfp.cmd2')
        for n in range(0, 8):
            try:
                f = open('/tmp/rmfp.cmd2', 'wb')
                try:
                    f.write('100\n')
                finally:
                    f.close()

            except Exception as e:
                print(str(e))

            if os.path.exists('/tmp/rmfp.cmd2'):
                break
            time.sleep(0.05)

        hdparm = os.popen('killall rmfp_player')
        time.sleep(0.1)
        open('/proc/player', 'w').write('1')
        time.sleep(0.1)
        self.frontend = None
        self.session.nav.playService(self.current_service)
        time.sleep(0.9)
        azplay_vctrl = VolumeControl.instance
        if self.azplay_ismute == False:
            value = self.azplay_currebtvol
            azplay_vctrl.volctrl.setVolume(value, value)
            azplay_vctrl.volSave()
            azplay_vctrl.volumeDialog.setValue(value)
        time.sleep(0.5)
        self.close()

    def quit0(self):
        hdparm = os.popen('killall rmfp_player')
        self.HDDTimer1 = eTimer()
        self.HDDTimer1.callback.append(self.quit1)
        self.HDDTimer1.start(100, True)

    def quit1(self):
        open('/proc/player', 'w').write('1')
        self.HDDTimer1 = eTimer()
        self.HDDTimer1.callback.append(self.quit2)
        self.HDDTimer1.start(100, True)

    def quit2(self):
        self.close()

    def keyUp(self):
        sel = self['menu'].getIndex()
        sel -= 1
        if sel < 0:
            sel = self.ListCount - 1
        self['menu'].setIndex(sel)
        sel = self['menu'].getIndex()
        self.ShowPicon(sel)

    def keyDown(self):
        sel = self['menu'].getIndex()
        sel += 1
        if sel >= self.ListCount:
            sel = 0
        self['menu'].setIndex(sel)
        sel = self['menu'].getIndex()
        self.ShowPicon(sel)

    def keyLeft(self):
        sel = self['menu'].getIndex()
        sel -= 8
        self['menu'].setIndex(sel)
        sel = self['menu'].getIndex()
        self.ShowPicon(sel)

    def keyRight(self):
        sel = self['menu'].getIndex()
        sel += 8
        if sel >= self.ListCount:
            sel = 0
        self['menu'].setIndex(sel)
        sel = self['menu'].getIndex()
        self.ShowPicon(sel)

    def ZapUp(self):
        self.keyDown()
        self.ok()

    def ZapDown(self):
        self.keyUp()
        self.ok()

    def ShowPicon(self, sel):
        picture0 = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/Ico/empty.png')
        try:
            file = '/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/Picons/picon_default.png'
            file1 = '/usr/lib/enigma2/python/Plugins/Extensions/AzIPTV/Picons/' + str(self.listp[sel])
            if os.path.exists(file1):
                file = file1
            picture = LoadPixmap(file)
            self['picon'].instance.setPixmap(picture)
        except Exception:
            self['picon'].instance.setPixmap(picture0)

        try:
            ime = self.list[sel][0][5:]
        except Exception:
            ime = 'Err.In List'

        self['infoM2'].setText(str(ime))

    def Konfig(self):
        self.session.openWithCallback(self.ClBackCfg, AZIPTVConfig)

    def ClBackCfg(self, komanda = None):
        print('-')
        if komanda == 'ok':
            print('Saved')

    def ClBack(self):
        print('++++++++++++++++++++++++')

    def OpenFrontend(self):
        frontend = None
        resource_manager = eDVBResourceManager.getInstance()
        if resource_manager is None:
            print('get resource manager instance failed')
        else:
            self.raw_channel = resource_manager.allocateRawChannel(self.feid)
            if self.raw_channel is None:
                print('allocateRawChannel failed')
            else:
                frontend = self.raw_channel.getFrontend()
                if frontend is None:
                    print('getFrontend failed')
        return frontend


class HideScr(Screen):
    skin = '\n\t\t<screen position="0,0" size="0,0" title="AzIPTV v.1.0" flags="wfNoBorder" >\n\t\t</screen>'

    def __init__(self, session, pateka):
        Screen.__init__(self, session)
        self.session = session
        self['actions'] = NumberActionMap(['MediaPlayerActions',
         'InputActions',
         'OkCancelActions',
         'ColorActions',
         'DirectionActions'], {'menu': self.Konfig,
         'ok': self.ok,
         'cancel': self.exit1,
         'up': self.exit,
         'down': self.exit,
         'left': self.ZapDown,
         'right': self.ZapUp,
         'nextBouquet': self.ZapUp,
         'prevBouquet': self.ZapDown,
         '1': self.keyNumberGlobal,
         '2': self.keyNumberGlobal,
         '3': self.keyNumberGlobal,
         '4': self.keyNumberGlobal,
         '5': self.keyNumberGlobal,
         '6': self.keyNumberGlobal,
         '7': self.keyNumberGlobal,
         '8': self.keyNumberGlobal,
         '9': self.keyNumberGlobal,
         '0': self.keyNumberGlobal}, -1)

    def updateMsg(self):
        self.close()

    def exit1(self):
        self.close('*Exit*')

    def exit(self):
        self.close('---')

    def ok(self):
        self.close('---')

    def ZapUp(self):
        self.close('Ch+')

    def ZapDown(self):
        self.close('Ch-')

    def keyNumberGlobal(self, number):
        self.session.openWithCallback(self.ClBack2, SetChNo, number)

    def ClBack2(self, komanda):
        self.close('*DirectCh*' + str(komanda))

    def Konfig(self):
        self.session.openWithCallback(self.ClBackCfg, AZIPTVConfig, '1')

    def ClBackCfg(self, komanda = None):
        print('-')
        if komanda == 'ok':
            if config.AZIPTV.Scaling.value == 'Just Scale':
                cmd = 223
            if config.AZIPTV.Scaling.value == 'Pan&Scan':
                cmd = 224
            if config.AZIPTV.Scaling.value == 'Pillarbox':
                cmd = 225
            if cmd > 0:
                self.SendCMD2(-1, cmd)
            time.sleep(0.11)

    def SendCMD2(self, k1, k2):
        if k1 >= 0:
            if os.path.exists('/tmp/rmfp.in2'):
                os.remove('/tmp/rmfp.in2')
            if os.path.exists('/tmp/rmfp.cmd2'):
                os.remove('/tmp/rmfp.cmd2')
            cmd = 'echo ' + str(k1) + ' > /tmp/rmfp.in2;echo ' + str(k2) + ' > /tmp/rmfp.cmd2'
            os.popen(cmd)
        else:
            if os.path.exists('/tmp/rmfp.cmd2'):
                os.remove('/tmp/rmfp.cmd2')
            os.popen('echo ' + str(k2) + ' > /tmp/rmfp.cmd2')


class SetChNo(Screen):
    skin = '\n\t\t<screen position="0,0" size="120,60" title="AzIPTV v.1.0" flags="wfNoBorder" >\n\t\t<widget name="infoM0" position="10,10" zPosition="2" size="50,40" font="Regular;40" foregroundColor="#ffffff" transparent="0" halign="center" valign="center" />\n\t\t<widget name="infoM1" position="60,10" zPosition="2" size="50,40" font="Regular;40" foregroundColor="#ffffff" transparent="0" halign="center" valign="center" />\n\t\t<widget name="infoM2" position="110,10" zPosition="2" size="50,40" font="Regular;40" foregroundColor="#ffffff" transparent="0" halign="center" valign="center" />\n\t\t</screen>'

    def __init__(self, session, number):
        Screen.__init__(self, session)
        self.session = session
        self.number1 = number
        self.number2 = -1
        self['actions'] = NumberActionMap(['MediaPlayerActions',
         'InputActions',
         'OkCancelActions',
         'ColorActions',
         'DirectionActions'], {'cancel': self.exit1,
         '1': self.keyNumberGlobal,
         '2': self.keyNumberGlobal,
         '3': self.keyNumberGlobal,
         '4': self.keyNumberGlobal,
         '5': self.keyNumberGlobal,
         '6': self.keyNumberGlobal,
         '7': self.keyNumberGlobal,
         '8': self.keyNumberGlobal,
         '9': self.keyNumberGlobal,
         '0': self.keyNumberGlobal}, -1)
        self['infoM0'] = Label()
        self['infoM1'] = Label()
        self['infoM2'] = Label()
        self['infoM0'].setText('-')
        self['infoM1'].setText(str(self.number1))
        self.ChSelTimer1 = eTimer()
        self.ChSelTimer1.callback.append(self.ok1)
        self.ChSelTimer1.start(3000, True)

    def ok1(self):
        if self.number2 == -1:
            chno = '0' + str(self.number1)
        else:
            chno = str(self.number1) + str(self.number2)
        self.close(chno)

    def keyNumberGlobal(self, number):
        self.number2 = number
        self['infoM0'].setText(str(self.number1))
        self['infoM1'].setText(str(self.number2))
        self.ChSelTimer1 = eTimer()
        self.ChSelTimer1.callback.append(self.ok1)
        self.ChSelTimer1.start(100, True)

    def exit1(self):
        self.close('*Exit*')

    def exit(self):
        self.close('---')


class AZIPTVConfig(ConfigListScreen, Screen):
    skin = '\n\t\t<screen position="center,center" size="710,275" title="AzIPTV - Setup" >\n\t\t<ePixmap pixmap="buttons/red.png" position="10,230" size="140,40" transparent="1" alphatest="on" />\n\t\t<ePixmap pixmap="buttons/green.png" position="560,230" size="140,40" transparent="1" alphatest="on" />\n\t\t<widget source="key_red" render="Label" position="10,230" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t<widget source="key_green" render="Label" position="560,230" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t<widget source="poraka" render="Label" position="150,230" zPosition="1" size="400,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t<widget name="config" position="10,10" size="690,210" scrollbarMode="showOnDemand" />\n\t\t</screen>'

    def __init__(self, session, args = None):
        Screen.__init__(self, session)
        self.session = session
        self.ActivePlay = args
        self.list = []
        self['actions'] = ActionMap(['ChannelSelectBaseActions',
         'WizardActions',
         'DirectionActions',
         'MenuActions',
         'NumberActions',
         'ColorActions'], {'save': self.SaveCfg,
         'back': self.Izlaz,
         'ok': self.SaveCfg,
         'green': self.SaveCfg,
         'red': self.Izlaz}, -2)
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('Save Conf'))
        self['poraka'] = StaticText(_('AzIPTV - Setup'))
        ConfigListScreen.__init__(self, self.list)
        self.Scaling_old = config.AZIPTV.Scaling.value
        self.Scaling_old1 = config.AZIPTV.Scaling.value
        self.createSetup()

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.createSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.createSetup()

    def createSetup(self):
        self.list = []
        self.list.append(getConfigListEntry(_('Scaling:'), config.AZIPTV.Scaling))
        self['config'].list = self.list
        self['config'].l.setList(self.list)
        if self.Scaling_old != config.AZIPTV.Scaling.value:
            cmd = 0
            if config.AZIPTV.Scaling.value == 'Just Scale':
                cmd = 223
            if config.AZIPTV.Scaling.value == 'Pan&Scan':
                cmd = 224
            if config.AZIPTV.Scaling.value == 'Pillarbox':
                cmd = 225
            if cmd > 0:
                self.SendCMD2(-1, cmd)
        self.Scaling_old = config.AZIPTV.Scaling.value

    def SendCMD2(self, k1, k2):
        if k1 >= 0:
            if os.path.exists('/tmp/rmfp.in2'):
                os.remove('/tmp/rmfp.in2')
            if os.path.exists('/tmp/rmfp.cmd2'):
                os.remove('/tmp/rmfp.cmd2')
            cmd = 'echo ' + str(k1) + ' > /tmp/rmfp.in2;echo ' + str(k2) + ' > /tmp/rmfp.cmd2'
            os.popen(cmd)
        else:
            if os.path.exists('/tmp/rmfp.cmd2'):
                os.remove('/tmp/rmfp.cmd2')
            os.popen('echo ' + str(k2) + ' > /tmp/rmfp.cmd2')

    def SaveCfg(self):
        config.AZIPTV.Scaling.save()
        self.close('ok')

    def Izlaz(self):
        config.AZIPTV.Scaling.value = self.Scaling_old1
        cmd = 0
        if config.AZIPTV.Scaling.value == 'Just Scale':
            cmd = 223
        if config.AZIPTV.Scaling.value == 'Pan&Scan':
            cmd = 224
        if config.AZIPTV.Scaling.value == 'Pillarbox':
            cmd = 225
        if cmd > 0:
            self.SendCMD2(-1, cmd)
        time.sleep(0.11)
        self.close()


def main(session, **kwargs):
    session.open(IPTV)


def Plugins(**kwargs):
    boxime = 'me'
    if boxime == 'elite' or boxime == 'premium' or boxime == 'premium+' or boxime == 'ultra' or boxime == 'me' or boxime == 'minime' or boxime == 'multimedia':
        return [PluginDescriptor(name=_('AzIPTV'), description=_('AzIPTV'), icon='IPTV.png', where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=main)]
    else:
        return []
