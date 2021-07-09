from enum import Enum

from werkzeug.datastructures import MultiDict


# check if model key is a public
def is_public(k): return k[0] != '_'


class MultiDictMixin(object):
    """
    Mixin to generate a MultiDict
    """

    @staticmethod
    def __dict_value__(value):
        """
        Get the value for a dict
        :param value:   Raw value
        :return:
        """
        return value.get_dict() if isinstance(value, MultiDictMixin) else value

    @staticmethod
    def __multidict_value__(value, attrib):
        """
        Get the value for a dict/MultiDict
        :param value:   Raw value
        :param attrib:  Attribute of raw value to return instead of raw value
        :return:
        """
        if attrib is None:
            if isinstance(value, list):
                result = list(MultiDictMixin.__dict_value__(g) for g in value)
            elif isinstance(value, tuple):
                result = tuple(MultiDictMixin.__dict_value__(g) for g in value)
            else:
                result = value
        else:
            if isinstance(value, list):
                result = list(MultiDictMixin.__dict_value__(vars(g)[attrib])
                              for g in value)
            elif isinstance(value, tuple):
                result = tuple(MultiDictMixin.__dict_value__(vars(g)[attrib])
                               for g in value)
            else:
                result = MultiDictMixin.__dict_value__(vars(value)[attrib])
        return result

    def get_multidict(self, ignore=None, **kwargs):
        """
        Generate a MultiDict
        :param ignore: fields to ignore
        :param kwargs: keyword args where 'key' is the object property and
                       'value' is the required attribute of the property.
                       e.g. with Parent.Child, children='name' will return
                       Child.name as the value for Parent.Child
        """
        return MultiDict(self.get_dict(ignore=ignore, **kwargs))

    def get_dict(self, ignore=None, **kwargs):
        """
        Generate a dict
        :param ignore: fields to ignore
        :param kwargs: keyword args where 'key' is the object property and
                       'value' is the required attribute of the property.
                       e.g. with Parent.Child, children='name' will return
                       Child.name as the value for Parent.Child
        """
        if ignore is None:
            ignore = []
        # TODO Method of passing ignores for sub elements.
        return {k: self.__multidict_value__(v, kwargs[k]
                if k in kwargs else None)
                for k, v in vars(self).items()
                # copy just the public data values
                if is_public(k) and k not in ignore}

    def equal(self, o: object, ignore=None) -> bool:
        """
        Check if the specified object equals this
        :param o:      object to check
        :param ignore: fields to ignore
        """
        if ignore is None:
            ignore = []
        eq = isinstance(o, MultiDictMixin)
        if eq:
            for k, v in vars(self).items():
                if is_public(k) and k not in ignore:
                    eq = (v == vars(o)[k])
                    if not eq:
                        break
        return eq


class ResultType(Enum):
    DICT = 1    # Return type dictionary.
    MODEL = 2   # Return type SQLAlchemy model.
