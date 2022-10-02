import logging

class Tree(object):
    """Generic tree node."""
    def __init__(self, name, children=None, isroot=False):
        self.name = name
        if isroot:
            self.rootname = name
        else:
            self.rootname = ""
        self.children = []
        if children is not None:
            for child in children:
                self.add_child(child)

    def __repr__(self):
        return self.name

    def add_child(self, node):
        assert isinstance(node, Tree)
        node.rootname = self.rootname
        self.children.append(node)

    def count_children(self):
        return len(self.children)

    def print_tree(self, depth=0):
        tabbing = "\t" * depth
        logging.debug(f"{tabbing}{self.name}")
        for child in self.children:
            child.print_tree(depth + 1)

    def get_total_nodes(self):
        count = 0
        if len(self.children) == 0:
            count = 0
        else:
            for child in self.children:
                count += 1 + child.get_total_nodes()
        return count

    def get_list_of_leaves(self, top=True):
        if top and self.count_children() == 0:
            leaves = []
        else:
            if self.count_children() > 0:
                leaves = []
                for child in self.children:
                    leaves = leaves + child.get_list_of_leaves(False)
            else:
                leaves = [self.name]
        return leaves
