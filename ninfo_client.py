#!/usr/bin/env python
import requests
from multiprocessing.pool import ThreadPool

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

class Client:
    def __init__(self, host, user, api_key):
        self.host = host
        self.user = user
        self.api_key = api_key
        self.ses = requests.session()
        self.ses.verify = False

    @memoized_property
    def plugins(self):
        r = self.ses.get("%s/info/plugins" % self.host)
        r.raise_for_status()
        return r.json()['plugins']

    #refactor?
    def get_info_text(self, plugin, q):
        r = self.ses.get("%s/info/text/%s/%s" % (self.host, plugin, q))
        r.raise_for_status()
        return r.text

    def get_info_json(self, plugin, q):
        r = self.ses.get("%s/info/json/%s/%s" % (self.host, plugin, q))
        r.raise_for_status()
        return r.json()
    get_info = get_info_json


    def show_info(self, arg, plugins=None):
        if not plugins:
            plugins = [p['name'] for p in self.plugins]
        for p in plugins:
            try :
                res = self.get_info_text(p, arg)
            except Exception, e:
                res = "Error: %s" % e
            if res:
                print '*** %s ***' % p
                print res

    def _run(self, tup):
        type, plugin, arg = tup
        func = getattr(self, 'get_info_' + type)
        try :
            return plugin, arg, func(plugin, arg)
        except Exception, e:
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
                print  '*** %s ***' % p
                print res

    def show_info_parrallel_multiple(self, args, plugins=None):
        reqs = self.make_requests("text", args, plugins)
        for p, arg, res in reqs:
            if res:
                print  '*** %s %s ***' % (p, arg)
                print res

    def get_info_dict_multiple(self, args, plugins=None):
        reqs = self.make_requests("json", args, plugins)
        result = {}
        for p, arg, r in reqs:
            if arg not in result:
                result[arg] = {}
            result[arg][p] = r
        return result
        

import ConfigParser
import os
def ClientINI(ini_file=None):
    cp = ConfigParser.ConfigParser()
    if ini_file:
        cp.read([ini_file])
    else:
        cp.read([os.path.expanduser("~/.config/ninfo.ini"), "ninfo.ini"])
    cfg = dict(cp.items("config"))

    return Client(**cfg)

def main():
    from optparse import OptionParser
    parser = OptionParser(usage = "usage: %prog [options] [addresses]")
    parser.add_option("-p", "--plugin", dest="plugins", action="append", default=None)
    parser.add_option("-l", "--list", dest="list", action="store_true", default=False)
    (options, args) = parser.parse_args()
    
    p = ClientINI()
    if options.list:
        print "Name"
        for pl in p.plugins:
            print pl

    plugins = options.plugins or None
    p.show_info_parrallel_multiple(args, plugins=plugins)

if __name__ == "__main__":
    main()
