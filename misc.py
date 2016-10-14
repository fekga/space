import collections
import operator

class Change(object):
    def __init__(self, window, init_value):
        self.window = window
        self.init_value = self.value = init_value
        self.window.push_handlers(self)

    def _change_value(self, value, op, typecast=None):
        def no_cast(value):
            return value
        if typecast is None:
            typecast = no_cast
        if isinstance(self.init_value, collections.Iterable):
            self.value = tuple(map(lambda i: typecast(op(i, value)), self.init_value))
        else:
            self.value = typecast(op(self.init_value, value))

    def _multiply_value(self, multiplier, typecast=None):
        self._change_value(multiplier, operator.__mul__, typecast)

    def _add_value(self, addend, typecast=None):
        self._change_value(addend,operator.__add__, typecast)

    def __call__(self):
        return self.value

class ChangeWrapper(object):
    def __init__(self, wrapped_class, *args, **kwargs):
        self.init_settings = dict()
        for k,v in kwargs.items():
            if isinstance(v,Change):
                kwargs[k] = v()
                self.init_settings[k] = v
        self.wrapped_class = wrapped_class(*args,**kwargs)

    def __getattr__(self, item):
        if item in self.init_settings:
            return self.init_settings[item]()
        return self.wrapped_class.__getattribute__(item)

class ResizeHeightRatio(Change):
    def __init__(self, window, init_value):
        super().__init__(window,init_value)

    def on_resize(self, width, height):
        self._multiply_value(height/self.window.initial_height,int)

class ResizeWidth(Change):
    def __init__(self, window, init_value=1):
        super().__init__(window,init_value)

    def on_resize(self, width, height):
        self._multiply_value(width,int)

class ResizeHeight(Change):
    def __init__(self, window, init_value=1):
        super().__init__(window,init_value)

    def on_resize(self, width, height):
        self._multiply_value(height,int)