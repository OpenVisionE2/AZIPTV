#!/usr/bin/python
# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor

def PVIPTV(*args, **kwargs):
    import IPTV
    return IPTV.IPTV(False, *args, **kwargs)


def PVIPTVAutostart(*args, **kwargs):
    import IPTV
    return IPTV.IPTV(True, *args, **kwargs)


def main(session, **kwargs):
    session.open(PVIPTV)


def menu(menuid, **kwargs):
    if menuid == 'mainmenu':
        return [(_('AzIPTV'),
          main,
          'AzIPTV',
          44)]
    return []


def Plugins(**kwargs):
    list = []
    list.append(PluginDescriptor(name='AzIPTV', description='IPTV Plugin for your Azbox', where=PluginDescriptor.WHERE_MENU, fnc=menu))
    list.append(PluginDescriptor(name='AzIPTV', description='IPTV Plugin for your Azbox', where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main))
    return list
