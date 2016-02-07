try:
    from functools import singledispatch
except ImportError:
    from singledispatch import singledispatch


# monoid
@singledispatch
def mempty(monoid):
    return monoid.mempty()


@singledispatch
def mappend(monoid, other):
    return monoid.mappend(other)


mempty.register(str)(lambda string: '')
mappend.register(str)(lambda string, other: string + other)

mempty.register(list)(lambda lst: [])
mappend.register(list)(lambda lst, other: lst + other)

mempty.register(tuple)(lambda lst: ())
mappend.register(tuple)(lambda tup, other: tup + other)


# functor
@singledispatch
def fmap(functor, func):
    '''Applies a function to the data 'inside' a functor.

    Uses functools.singledispatch so you can write your own functors
    for use with the library.'''
    return functor.fmap(func)


@fmap.register(list)
def _(lst, func):
    return [func(a) for a in lst]


@fmap.register(tuple)
def _(tup, func):
    return tuple(func(a) for a in tup)


# applicative functor
@singledispatch
def pure(applicative, item):
    return applicative.pure(item)


@singledispatch
def ap(applicative, func):
    return applicative.ap(func)


@pure.register(list)
def _(lst, item):
    return [item]


@ap.register(list)
def _(lst, funcs):
    return [f(i) for i in lst for f in funcs]


@pure.register(tuple)
def _(tup, item):
    return (item,)


@ap.register(tuple)
def _(tup, funcs):
    return tuple(f(i) for i in tup for f in funcs)


# traversable
@singledispatch
def traverse(traversable, func):
    return traversable.traverse(func)


@traverse.register(list)
def _(lst, func):
    head, rest = lst[0], lst[1:]

    cons = lambda a: lambda b: [a] + b
    if rest:
        return ap(traverse(rest, func), fmap(func(head), cons))
    else:
        return fmap(func(head), lambda a: [a])
