import xmltodict, copy, os


class BNGGdiff:
    """
    Add documentation here
    """

    def __init__(self, inp1, inp2, out, mode="matrix") -> None:
        self.input = inp1
        self.input2 = inp2
        self.output = out
        self.colors = {
            "g1": ["#dadbfd", "#e6e7fe", "#f3f3ff"],
            "g2": ["#ff9e81", "#ffbfaa", "#ffdfd4"],
            "intersect": ["#c4ed9e", "#d9f4be", "#ecf9df"],
        }
        self.available_modes = ["matrix", "union"]
        if mode not in self.available_modes:
            raise RuntimeError(
                f"Mode {mode} is not a valid mode, please choose from {self.available_modes}"
            )
        self.mode = mode

        with open(self.input, "r") as f:
            self.gdict_1 = xmltodict.parse(f.read())
        with open(self.input2, "r") as f:
            self.gdict_2 = xmltodict.parse(f.read())

    def diff_graphs(
        self,
        g1,
        g2,
        colors={
            "g1": ["#dadbfd", "#e6e7fe", "#f3f3ff"],
            "g2": ["#c4ed9e", "#d9f4be", "#ecf9df"],
            "intersect": ["#c4ed9e", "#d9f4be", "#ecf9df"],
        },
    ):
        """
        Given two XML dictionaries (using xmltodict) of two graphml
        graphs, do the diff and return the difference graphml xml in
        dictionary format

        The result is g1-g2. By default g1 only stuff are colored green
        g2 only nodes are colored red and common elements are colored blue.
        These can be changed by the colors kwarg which is a dictionary with
        keys g1, g2 and intersect and colors are given as hexcode strings.

        input
            g1: dict
            g2: dict
            colors (opt): dict

        output
            diff_g1_g2: dict
        """
        # first do a deepcopy so we don't have to
        # manually do add boilerpate
        if self.mode == "matrix":
            diff_gml = copy.deepcopy(g1)
            self._find_diff(g1, g2, diff_gml, colors)
            # now write gml as graphml
            with open(self.output, "w") as f:
                f.write(xmltodict.unparse(diff_gml))
            # write recolored g1
            g1_recolor_name = os.path.basename(self.input).replace(
                ".graphml", "_recolored.graphml"
            )
            with open(g1_recolor_name, "w") as f:
                f.write(xmltodict.unparse(self.gdict_1_recolor))
            # write recolored g2
            g2_recolor_name = os.path.basename(self.input2).replace(
                ".graphml", "_recolored.graphml"
            )
            with open(g2_recolor_name, "w") as f:
                f.write(xmltodict.unparse(self.gdict_2_recolor))
            # let's do the reverse
            diff_gml = copy.deepcopy(g2)
            self._find_diff(
                g2,
                g1,
                diff_gml,
                colors={
                    "g1": colors["g2"],
                    "g2": colors["g1"],
                    "intersect": colors["intersect"],
                },
            )
            rev_diff_name = os.path.basename(self.output).replace(
                ".graphml", "_rev.graphml"
            )
            with open(rev_diff_name, "w") as f:
                f.write(xmltodict.unparse(diff_gml))
        # elif self.mode == "union":
        #     self._find_diff_union(g1, g2, diff_gml, colors)
        else:
            raise RuntimeError(
                f"Mode {self.mode} is not a valid mode, please choose from {self.available_modes}"
            )
        return diff_gml

    # def _find_diff_union(self, g1, g2, dg, colors):
    #     # FIXME: Global IDs are not fixed, we need to adjust
    #     # IDs and similarly fix edges accordingly

    #     # we first want to do the regular diff
    #     self._find_diff(g1, g2, dg, colors)
    #     # now we loop over g2 nodes and add them to dg with the right
    #     # colors to get the union version
    #     node_stack = [(["graphml"], [], g2["graphml"])]
    #     while len(node_stack) > 0:
    #         curr_node = None
    #         curr_keys, curr_names, curr_node = node_stack.pop(-1)
    #         # let's take a look at the difference
    #         dnode = self._get_node_from_names(dg, curr_names)
    #         if dnode is None and len(curr_names) > 0:
    #             # this means we don't have this node in diff graph
    #             # we need to add it in
    #             curr_dnode = self._add_node_to_graph(curr_node, dg, curr_names)
    #             self._color_node(
    #                 curr_dnode, colors["g2"][self._get_color_id(curr_dnode)]
    #             )
    #         # if we have graphs in there, add the nodes to the stack
    #         if "graph" in curr_node.keys():
    #             # there is a graph in the node, add the nodes to stack
    #             if isinstance(curr_node["graph"]["node"], list):
    #                 for inode, node in enumerate(curr_node["graph"]["node"]):
    #                     ckey = curr_keys + [node["@id"]]
    #                     node_stack.append(
    #                         (ckey, curr_names + [self._get_node_name(node)], node)
    #                     )
    #             else:
    #                 ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
    #                 node_stack.append(
    #                     (
    #                         ckey,
    #                         curr_names
    #                         + [self._get_node_name(curr_node["graph"]["node"])],
    #                         curr_node["graph"]["node"],
    #                     )
    #                 )

    def _add_node_to_graph(self, node, dg, names):
        node_to_add_to = self._get_node_from_names(dg, names[:-1])
        copied_node = copy.deepcopy(node)
        if "graph" in node_to_add_to.keys():
            if isinstance(node_to_add_to["graph"]["node"], list):
                node_to_add_to["graph"]["node"].append(copied_node)
            else:
                # it's a single node and we need to turn
                # it into a list instead
                copied_original_node = copy.deepcopy(node_to_add_to["graph"]["node"])
                nodes_to_add = [copied_original_node, copied_node]
                node_to_add_to["graph"]["node"] = nodes_to_add
        return copied_node

    def _find_diff(self, g1, g2, dg, colors):
        # first find differences in nodes
        # FIXME: Check for single nodes before looping
        node_stack = [(["graphml"], [], g1["graphml"])]
        dnode_stack = [(["graphml"], [], dg["graphml"])]
        while len(node_stack) > 0:
            curr_node, curr_dnode = None, None
            curr_keys, curr_names, curr_node = node_stack.pop(-1)
            curr_dkeys, curr_dnames, curr_dnode = dnode_stack.pop(-1)
            # let's take a look at the difference
            g2name = None
            curr_name = None
            g2node = self._get_node_from_names(g2, curr_names)
            if len(curr_names) > 0:
                if not (g2node is None):
                    # also check for name
                    if "data" in g2node.keys():
                        g2name = self._get_node_name(g2node)
                        curr_name = self._get_node_name(curr_node)
                        if g2name is not None or curr_name is not None:
                            if g2name == curr_name:
                                # we have the node in g2, we color it appropriately
                                self._color_node(
                                    curr_dnode,
                                    colors["intersect"][self._get_color_id(curr_dnode)],
                                )
                            else:
                                self._color_node(
                                    curr_dnode,
                                    colors["g1"][self._get_color_id(curr_dnode)],
                                )
                else:
                    if "data" in curr_dnode.keys():
                        # we don't have the node in g2, we color it appropriately
                        self._color_node(
                            curr_dnode, colors["g1"][self._get_color_id(curr_dnode)]
                        )
            # if we have graphs in there, add the nodes to the stack
            if "graph" in curr_node.keys():
                # there is a graph in the node, add the nodes to stack
                if isinstance(curr_node["graph"]["node"], list):
                    for inode, node in enumerate(curr_node["graph"]["node"]):
                        ckey = curr_keys + [node["@id"]]
                        node_stack.append(
                            (ckey, curr_names + [self._get_node_name(node)], node)
                        )
                        dnode = curr_dnode["graph"]["node"][inode]
                        dnode_stack.append(
                            (
                                curr_dkeys + [dnode["@id"]],
                                curr_dnames + [self._get_node_name(dnode)],
                                dnode,
                            )
                        )
                else:
                    ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
                    node_stack.append(
                        (
                            ckey,
                            curr_names
                            + [self._get_node_name(curr_node["graph"]["node"])],
                            curr_node["graph"]["node"],
                        )
                    )
                    dnode_stack.append(
                        (
                            ckey,
                            curr_dnames
                            + [self._get_node_name(curr_dnode["graph"]["node"])],
                            curr_dnode["graph"]["node"],
                        )
                    )
        # let's recolor both graphs
        self.gdict_1_recolor = self._recolor_graph(self.gdict_1, self.colors["g1"])
        self.gdict_2_recolor = self._recolor_graph(self.gdict_2, self.colors["g2"])
        # resize all fonts, this adds +20
        self._resize_fonts(self.gdict_1, 20)
        self._resize_fonts(self.gdict_2, 20)
        self._resize_fonts(dg, 20)

    def _recolor_graph(self, g, color_list):
        recol_g = copy.deepcopy(g)
        node_stack = [(["graphml"], [], recol_g["graphml"])]
        while len(node_stack) > 0:
            curr_node, curr_dnode = None, None
            curr_keys, curr_names, curr_node = node_stack.pop(-1)
            if len(curr_names) > 0:
                self._color_node(curr_node, color_list[self._get_color_id(curr_node)])
            # if we have graphs in there, add the nodes to the stack
            if "graph" in curr_node.keys():
                # there is a graph in the node, add the nodes to stack
                if isinstance(curr_node["graph"]["node"], list):
                    for inode, node in enumerate(curr_node["graph"]["node"]):
                        ckey = curr_keys + [node["@id"]]
                        node_stack.append(
                            (ckey, curr_names + [self._get_node_name(node)], node)
                        )
                else:
                    ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
                    node_stack.append(
                        (
                            ckey,
                            curr_names
                            + [self._get_node_name(curr_node["graph"]["node"])],
                            curr_node["graph"]["node"],
                        )
                    )
        return recol_g

    def _resize_fonts(self, g, add_to_font):
        node_stack = [(["graphml"], [], g["graphml"])]
        while len(node_stack) > 0:
            curr_node, curr_dnode = None, None
            curr_keys, curr_names, curr_node = node_stack.pop(-1)
            if len(curr_names) > 0:
                self._resize_node_font(curr_node, add_to_font)
            # if we have graphs in there, add the nodes to the stack
            if "graph" in curr_node.keys():
                # there is a graph in the node, add the nodes to stack
                if isinstance(curr_node["graph"]["node"], list):
                    for inode, node in enumerate(curr_node["graph"]["node"]):
                        ckey = curr_keys + [node["@id"]]
                        node_stack.append(
                            (ckey, curr_names + [self._get_node_name(node)], node)
                        )
                else:
                    ckey = curr_keys + [curr_node["graph"]["node"]["@id"]]
                    node_stack.append(
                        (
                            ckey,
                            curr_names
                            + [self._get_node_name(curr_node["graph"]["node"])],
                            curr_node["graph"]["node"],
                        )
                    )

    def _get_node_from_names(self, g, names):
        nodes = g["graphml"]["graph"]["node"]
        if len(names) == 0:
            return g["graphml"]
        copy_names = copy.copy(names)
        found = False
        while len(copy_names) > 0:
            key = copy_names.pop(0)
            if isinstance(nodes, list):
                for cnode in nodes:
                    cname = self._get_node_name(cnode)
                    if cname == key:
                        found = True
                        node = cnode
                        try:
                            nodes = node["graph"]["node"]
                        except:
                            break
            else:
                cname = self._get_node_name(nodes)
                found = True
                node = nodes
        if not found:
            return None
        return node

    def _get_node_properties(self, node):
        if isinstance(node["data"], list):
            found = False
            for datum in node["data"]:
                if "y:ProxyAutoBoundsNode" in datum.keys():
                    gnode = datum["y:ProxyAutoBoundsNode"]["y:Realizers"]["y:GroupNode"]
                    if isinstance(gnode, list):
                        properties = gnode[0]
                    else:
                        properties = gnode
                    found = True
                elif "y:ShapeNode" in datum.keys():
                    snode = datum["y:ShapeNode"]
                    if isinstance(snode, list):
                        properties = snode[0]
                    else:
                        properties = snode
                    found = True
            if not found:
                raise RuntimeError("Can't find properties for nodes")
        else:
            if "y:ProxyAutoBoundsNode" in node["data"].keys():
                properties = node["data"]["y:ProxyAutoBoundsNode"]["y:Realizers"][
                    "y:GroupNode"
                ]
            elif "y:ShapeNode" in node["data"].keys():
                properties = node["data"]["y:ShapeNode"]
            else:
                raise RuntimeError("Can't find properties for nodes")
        return properties

    def _get_node_name(self, node):
        # node['data'] can be a list if there are
        # multiple data types
        properties = self._get_node_properties(node)
        return properties["y:NodeLabel"]["#text"]

    def _get_node_fill(self, node):
        properties = self._get_node_properties(node)
        return properties["y:Fill"]

    def _get_node_color(self, node):
        return self._get_node_fill(node)["@color"]

    def _resize_node_font(self, node, size):
        properties = self._get_node_properties(node)
        properties["y:NodeLabel"]["@fontSize"] = str(size)

    def _get_font_size(self, node):
        properties = self._get_node_properties(node)
        return int(properties["y:NodeLabel"]["@fontSize"])

    def _get_color_id(self, node):
        # FIXME: This should be fixed at bng level by attaching
        # an attribute to graphml node stating the type of node
        # instead of using colors to check the type
        curr_color = self._get_node_color(node)
        if curr_color == "#D2D2D2":
            # grey indicates a species
            cid = 0
        elif curr_color == "#FFFFFF":
            # white indicates a component
            cid = 1
        elif curr_color == "#FFCC00":
            # yellow indicates a state
            cid = 2
        else:
            raise RuntimeError(f"Node color {curr_color} doesn't match known colors")
        return cid

    def _get_node_from_keylist(self, g, keylist):
        copy_keylist = copy.copy(keylist)
        gkey = copy_keylist.pop(0)
        if len(copy_keylist) == 0:
            # we only have "graphml" as key
            return g[gkey]
        # we are out of group nodes
        if "graph" not in g[gkey].keys():
            return None
        # everything up to here is good,
        # loop over to find the node
        nodes = g[gkey]["graph"]["node"]
        while len(copy_keylist) > 0:
            key = copy_keylist.pop(0)
            found = False
            if isinstance(nodes, list):
                for cnode in nodes:
                    if cnode["@id"] == key:
                        found = True
                        node = cnode
                        try:
                            nodes = node["graph"]["node"]
                        except:
                            break
            else:
                if cnode["@id"] == key:
                    found = True
                    node = cnode
            if not found:
                return None
        return node

    def _color_node(self, node, color) -> bool:
        """
        This uses yEd attributes to change the color of a node

        arguments
            node
            color
        returns
            boolean
        """
        fill = self._get_node_fill(node)
        fill["@color"] = color
        return True

    def _get_node_text(self, node):
        noded = node["data"]["y:ProxyAutoBoundsNode"]["y:Realizers"]
        for key in noded.keys():
            if "y:" in key:
                return noded[key]["y:NodeLabel"]["#text"]
        return None

    def run(self) -> None:
        # Now we have the graphml files, now we do diff
        self.diff_graphs(self.gdict_1, self.gdict_2, self.colors)
