import operator

from .identity import Identity
from .const import Const
from .typeclass import fmap, ap, traverse
from .setter import magic_set, multi_magic_set


def make_lens(getter, setter):
    '''turns a pair of getter and setter functions into a van Laarhoven
    lens. A getter function is one that takes a state and returns a
    value derived from that state. A setter function takes a new value and
    an old state and injects the new value into the old state, returning
    a new state.

    make_lens :: getter_func, setter_func -> Lens
    getter_func :: state -> value
    setter_func :: new_value, old_state -> new_state
    '''

    def new_func(func, state):
        old_value = getter(state)
        fa = func(old_value)
        return fmap(fa, lambda a: setter(a, state))

    return Lens(new_func)


class Lens:
    '''A Lens. Serves as the backbone of the lenses library. Acts as an
    object-oriented wrapper around a function that does all the hard
    work. This function is a van Laarhoven lens and has the following
    type (in ML-style notation):

    func :: (value -> functor value), state -> functor state
    '''
    __slots__ = ['func']

    def __init__(self, func):
        self.func = func

    def get(self, state):
        'Returns the value this lens is magnified on.'
        return self.func(lambda a: Const(a), state).item

    def get_all(self, state):
        'Returns all values this lens traverses over.'
        return self.func(lambda a: Const((a, )), state).item

    def modify(self, state, fn):
        'Applies a function to the magnified value.'
        return self.func(lambda a: Identity(fn(a)), state).item

    def set(self, state, newitem):
        'Sets the magnified value in the passed state.'
        return self.func(lambda a: Identity(newitem), state).item

    def compose(self, other):
        '''Composes another lens with this one.

        The `other` lens is used to refine the `self` lens. The
        following two pieces of code should be equivalent:

        ```
        self.compose(other).get(state)

        other.get(self.get(state))
        ```
        '''

        def new_func(fn, state):
            return self.func((lambda state2: other.func(fn, state2)), state)

        return Lens(new_func)


def _magic_set_lens(name, method, getter):
    @Lens
    def new_lens(fn, state):
        return fmap(
            fn(getter(state, name)),
            lambda newvalue: magic_set(state, method, name, newvalue))

    return new_lens


def getattr_l(name):
    return _magic_set_lens(name, 'setattr', getattr)


def getitem(key):
    return _magic_set_lens(key, 'setitem', operator.getitem)


@Lens
def trivial(func, state):
    'A trivial lens that magnifies to the whole state.'
    return fmap(func(state), lambda newvalue: newvalue)


@Lens
def both(func, state):
    'A traversal that magnifies both items [0] and [1].'
    mms = multi_magic_set(state, [('setitem', 0), ('setitem', 1)])
    return ap(func(state[1]), fmap(func(state[0]), mms))


def item(old_key):
    @Lens
    def new_lens(fn, state):
        return fmap(
            fn((old_key, state[old_key])),
            lambda new_value: dict([new_value] + [
                (k, v) for k, v in state.items() if k is not old_key
            ])
        )  # yapf: disable

    return new_lens


def item_by_value(old_value):
    def getter(state):
        for dkey, dvalue in state.items():
            if dvalue is old_value:
                return dkey, dvalue
        raise LookupError('{} not in dict'.format(old_value))

    @Lens
    def new_lens(fn, state):
        return fmap(
            fn(getter(state)),
            lambda new_value: dict([new_value] + [
                (k, v) for k, v in state.items() if v is not old_value
            ])
        )  # yapf: disable

    return new_lens


def tuple_l(*some_lenses):
    def getter(state):
        return tuple(a_lens.get(state) for a_lens in some_lenses)

    def setter(new_values, state):
        for a_lens, new_value in zip(some_lenses, new_values):
            state = a_lens.set(state, new_value)
        return state

    return make_lens(getter, setter)


@Lens
def traverse_l(fn, state):
    return traverse(state, fn)
