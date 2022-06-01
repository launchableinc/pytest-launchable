# cache the result of function call
# note that arguments are passed as is.

# The new version python seems to have similar features, we will support the old python as well.

def memorizer(f):
    func_to_value = {}

    def w(*args):
        if f in func_to_value:  # cache hit
            return func_to_value[f]
        else:
            v = f(*args)
            func_to_value[f] = v
            return v
    return w
