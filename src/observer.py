from abc import ABCMeta, abstractmethod
# ABC - Abstract Base Class
 
class Observer(object):
    __metaclass__ = ABCMeta
 
    @abstractmethod
    def update(self, *args, **kwargs):
        pass
