from enum import EnumMeta
from typing import Union, Iterable


class KeyScopeDict(dict):
    """
    这是一个添加了 key 值限定范围的dict
    """

    def __init__(self, scope: Union[Iterable, EnumMeta], auto_value=True, *keys, **kwargs):
        """

        :param scope: 限定范围, 可以是一个 Enum, 也可以是一个 Iterable
        :param auto_value: 是否自动对 Enum 进行自动取值
        """
        if not (isinstance(scope, Iterable) or isinstance(scope, EnumMeta)):
            raise Exception("scope type use Iterable or Enum(EnumMeta)")
        self.scope = scope
        self.auto_value = auto_value
        super(KeyScopeDict, self).__init__(*keys, **kwargs)

    def __setitem__(self, key, value):
        print(key, value)
        if self.in_scope(key):
            # 如果传入的 key 是 Enum 本身而不是值
            if isinstance(key, self.scope):
                if self.auto_value:
                    key = key.value
                else:
                    raise Exception("key expected type 'Enum.value', got 'Enum' instead")
            super(KeyScopeDict, self).__setitem__(key, value)
        else:
            raise Exception("key is illegal")

    def in_scope(self, key) -> bool:
        """
        查看 key 是否在规定的范围之内
        :param key: dict key
        :return: 是否满足
        """
        if isinstance(self.scope, EnumMeta):
            # AuthorizerCategory.value2member_map_
            return key in self.scope.value2member_map_
        elif isinstance(self.scope, Iterable):
            return key in self.scope
        else:
            return False
