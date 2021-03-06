#!/usr/bin/env python
from __future__ import print_function
import requests
from multiprocessing.pool import ThreadPool

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os

class memoized_property(object):
    """A read-only @property that is only evaluated once."""
    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result

class BaseClient:

    def __init__(self, host, user, api_key=None):
        self.host = host
        self.user = user
        self.ses = requests.session()
        if api_key:
            self.ses.headers["Authorization"] = "Token " + api_key

    @memoized_property
    def plugins(self):
        url = self.PLUGINS_TEMPLATE % {"host": self.host}
        r = self.ses.get(url)
        r.raise_for_status()
        return r.json()['plugins']

    #refactor?
    def get_info_text(self, plugin, q):
        url = self.INFO_TEMPLATE % { "host": self.host, "type": "txt", "plugin": plugin, "q": q}
        r = self.ses.get(url)
        r.raise_for_status()
        return r.text

    def get_info_json(self, plugin, q):
        url = self.INFO_TEMPLATE % { "host": self.host, "type": "json", "plugin": plugin, "q": q}
        r = self.ses.get(url)
        r.raise_for_status()
        return r.json()
    get_info = get_info_json


    def show_info(self, arg, plugins=None):
        if not plugins:
            plugins = [p['name'] for p in self.plugins]
        for p in plugins:
            try :
                res = self.get_info_text(p, arg)
            except Exception as e:
                res = "Error: %s" % e
            if res:
                print('*** %s ***' % p)
                print(res)

    def _run(self, tup):
        type, plugin, arg = tup
        func = getattr(self, 'get_info_' + type)
        try :
            return plugin, arg, func(plugin, arg)
        except Exception as e:
            return plugin, arg, e


    def make_requests(self, type, args, plugins=None):
        pool = ThreadPool(6)
        if not plugins:
            plugins = [p['name'] for p in self.plugins]
        reqs = [(type, p, arg) for p in plugins for arg in args]
        #not sure why returning this doesn't work
        for x in pool.imap(self._run, reqs):
            yield x

    def get_info_dict(self, arg, plugins=None):
        reqs = self.make_requests("json", [arg], plugins)
        result = {}
        for p, arg, r in reqs:
            result[p] = r
        return result

    def show_info_parrallel(self, arg, plugins=None):
        reqs = self.make_requests("text", [arg], plugins)
        for p, arg, res in reqs:
            if res:
                print('*** %s ***' % p)
                print(res)

    def show_info_parrallel_multiple(self, args, plugins=None):
        reqs = self.make_requests("text", args, plugins)
        for p, arg, res in reqs:
            if res:
                print('*** %s %s ***' % (p, arg))
                print(res)

    def get_info_dict_multiple(self, args, plugins=None):
        reqs = self.make_requests("json", args, plugins)
        result = {}
        for p, arg, r in reqs:
            if arg not in result:
                result[arg] = {}
            result[arg][p] = r
        return result
        
class NinfoWebClient(BaseClient):
    PLUGINS_TEMPLATE = "%(host)s/info/plugins"
    INFO_TEMPLATE = "%(host)s/info/%(type)s/%(plugin)s/%(q)s"

class DjangoNinfoClient(BaseClient):
    PLUGINS_TEMPLATE = "%(host)s/ninfo/api/plugins"
    INFO_TEMPLATE = "%(host)s/ninfo/api/plugins/%(plugin)s/%(type)s/%(q)s"

server_types = {
    "ninfo-web": NinfoWebClient,
    "django-ninfo": DjangoNinfoClient,
}

def Client(server_type, host, user=None, api_key=None):
    cls = server_types[server_type]

    return cls(host=host, user=user, api_key=api_key)

def ClientINI(ini_file=None):
    cp = configparser.ConfigParser()
    if ini_file:
        cp.read([ini_file])
    else:
        cp.read([os.path.expanduser("~/.config/ninfo.ini"), "ninfo.ini"])
    cfg = dict(cp.items("config"))

    server_type = cfg.pop("server-type")
    cls = server_types[server_type]

    return cls(**cfg)

def main():
    from optparse import OptionParser
    parser = OptionParser(usage = "usage: %prog [options] [addresses]")
    parser.add_option("-p", "--plugin", dest="plugins", action="append", default=None)
    parser.add_option("-l", "--list", dest="list", action="store_true", default=False)
    parser.add_option("-c", "--cfg", dest="config", action="store", default=None)
    (options, args) = parser.parse_args()
    
    p = ClientINI(options.config)
    if options.list:
        print("%-20s %-20s %s" %("Name", "Title", "Description"))
        for pl in p.plugins:
            print("%-20s %-20s %s" % (pl['name'], pl['title'], pl['description']))
        return

    plugins = options.plugins or None
    p.show_info_parrallel_multiple(args, plugins=plugins)

if __name__ == "__main__":
    main()
