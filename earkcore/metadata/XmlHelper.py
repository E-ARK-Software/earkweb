from lxml import objectify

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'


def q(ns, v):
    return '{{{}}}{}'.format(ns, v)


def sequence_insert(node, child, successor_sections):
    insert_function = node.append
    for section in successor_sections:
        path = objectify.ObjectPath(node.tag + '.' + section)
        if path.hasattr(node):
            insert_function = node[section].addprevious
            break
    insert_function(child)