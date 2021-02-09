import lldb

from hilda.exceptions import SymbolAbsentError


class SymbolsJar(dict):
    def set_hilda_client(self, client):
        self._client = client

    def get_lazy(self, name):
        if hasattr(self, '_client'):
            if '{' in name:
                # remove module name from symbol
                name = name.split('{', 1)[0]
            for s in self._client.target.FindSymbols(name):
                s = self._client.add_lldb_symbol(s.symbol)
                if s:
                    return s
        return None

    def __getitem__(self, item):
        if item not in self:
            symbol = self.get_lazy(item)
            if symbol:
                return symbol
        return dict.__getitem__(self, item)

    def __getattr__(self, name):
        if name not in self:
            if hasattr(self, '_client'):
                for s in self._client.target.FindSymbols(name):
                    s = self._client.add_lldb_symbol(s.symbol)
                    if s:
                        return s
            raise SymbolAbsentError(f'no such symbol: {name}')

        return self.get(name)

    def __setattr__(self, key, value):
        return self.__setitem__(key, value)

    def __delattr__(self, item):
        return self.__delitem__(item)

    def __sub__(self, other):
        retval = SymbolsJar()
        for k1, v1 in self.items():
            if k1 not in other:
                retval[k1] = v1
        return retval

    def __add__(self, other):
        retval = SymbolsJar()
        for k, v in other.items():
            retval[k] = v
        for k, v in self.items():
            retval[k] = v
        return retval

    def bp(self, callback=None, **args):
        """
        Place a breakpoint on all symbols in current jar.
        Look for the bp command for more details.
        :param callback:  callback function to be executed upon an hit
        :param args: optional args for the bp command
        """
        for k, v in self.items():
            v.bp(callback, **args)

    def by_module(self):
        """
        Filter to only names containing their module names
        :return: reduced symbol jar
        """
        retval = SymbolsJar()
        for k, v in self.items():
            if '{' not in k or '}' not in k:
                continue
            retval[k] = v
        return retval

    def by_type(self, lldb_type):
        """
        Filter by LLDB symbol types (for example: lldb.eSymbolTypeCode,
        lldb.eSymbolTypeData, ...)
        :param lldb_type: symbol type from LLDB consts
        :return: symbols matching the type filter
        """
        retval = SymbolsJar()
        for k, v in self.items():
            if v.type_ == lldb_type:
                retval[k] = v
        return retval

    def code(self):
        """
        Filter only code symbols
        :return: symbols with type lldb.eSymbolTypeCode
        """
        return self.by_type(lldb.eSymbolTypeCode)

    def data(self):
        """
        Filter only data symbols
        :return: symbols with type lldb.eSymbolTypeCode
        """
        return self.by_type(lldb.eSymbolTypeData)

    def objc_class(self):
        """
        Filter only objc meta classes
        :return: symbols with type lldb.eSymbolTypeObjCMetaClass
        """
        return self.clean().by_type(lldb.eSymbolTypeObjCMetaClass)

    def clean(self):
        """
        Filter only symbols without module suffix
        :return: reduced symbol jar
        """
        retval = SymbolsJar()
        for k, v in self.items():
            if '{' in k:
                continue
            retval[k] = v
        return retval

    def monitor(self, **args):
        """
        Perform monitor for all symbols in current jar.
        See monitor command for more details.
        :param args: given arguments for monitor command
        """
        for k, v in self.items():
            v.monitor(**args)

    def startswith(self, exp, case_sensitive=True):
        """
        Filter only symbols with given prefix
        :param exp: prefix
        :param case_sensitive: is case sensitive
        :return: reduced symbol jar
        """
        if not case_sensitive:
            exp = exp.lower()

        retval = SymbolsJar()
        for k, v in self.items():
            orig_k = k
            if not case_sensitive:
                k = k.lower()
            if k.startswith(exp):
                retval[orig_k] = v
        return retval

    def find(self, exp, case_sensitive=True):
        """
        Filter symbols containing a given expression
        :param exp: given expression
        :param case_sensitive: is case sensitive
        :return: reduced symbol jar
        """
        if not case_sensitive:
            exp = exp.lower()

        retval = SymbolsJar()
        for k, v in self.items():
            orig_k = k
            if not case_sensitive:
                k = k.lower()
            if exp in k:
                retval[orig_k] = v
        return retval