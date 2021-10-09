import re, pyparsing, sympy
from sympy.printing.str import StrPrinter

prnter = StrPrinter({"full_prec": False})


class Parameter:
    def __init__(self):
        # spec is ID, value, constant or not, units
        self.Id = None
        self.val = None
        self.cts = None
        self.units = None
        self.rxn_ind = None

    def __str__(self):
        if self.units is not None and self.units != "":
            return "{} {} #{}".format(self.Id, self.val, self.units)
        else:
            return "{} {}".format(self.Id, self.val)

    def __repr__(self):
        return str(self)


class Compartment:
    def __init__(self):
        self.Id = None
        self.dim = None
        self.size = None
        self.cmt = None
        self.unit = None

    def __str__(self):
        if self.cmt is not None and self.cmt != "":
            txt = "{} {} {} #{}".format(self.Id, self.dim, self.size, self.cmt)
        else:
            txt = "{} {} {}".format(self.Id, self.dim, self.size)
        return txt

    def __repr__(self):
        return str(self)


class Molecule:
    def __init__(self):
        self.translator = {}
        self.initConc = -1
        self.initAmount = -1
        self.isConstant = False
        self.isBoundary = False
        self.compartment = None

    def parse_raw(self, raw):
        self.raw = raw
        self.Id = raw["returnID"]
        self.initConc = raw["initialConcentration"]
        self.initAmount = raw["initialAmount"]
        self.isConstant = raw["isConstant"]
        self.isBoundary = raw["isBoundary"]
        self.compartment = raw["compartment"]
        self.name = raw["name"].replace(" ", "").replace("*", "m")
        self.identifier = raw["identifier"]

    def __str__(self):
        if self.Id in self.translator:
            # str2 is molecule types?
            txt = "{}".format(self.translator[self.Id].str2())
        else:
            txt = "{}()".format(self.Id)
        return txt

    def __repr__(self):
        return str(self)


class Species:
    def __init__(self):
        self.noCompartment = False
        self.translator = {}
        self.raw = None
        self.compartment = None
        self.Id = None
        self.initConc = None
        self.initAmount = None
        self.isConstant = None
        self.isBoundary = None
        self.name = None
        self.identifier = None

    def parse_raw(self, raw):
        self.raw = raw
        self.Id = raw["returnID"]
        self.initConc = raw["initialConcentration"]
        self.initAmount = raw["initialAmount"]
        self.isConstant = raw["isConstant"]
        self.isBoundary = raw["isBoundary"]
        self.compartment = raw["compartment"]
        self.name = raw["name"].replace(" ", "")
        self.identifier = raw["identifier"]
        if self.initAmount > 0:
            self.val = self.initAmount
        elif self.initConc > 0:
            # TODO: Figure out what to do w/ conc
            self.val = self.initConc

    def __str__(self):
        trans_id = (
            str(self.translator[self.Id])
            if self.Id in self.translator
            else self.Id + "()"
        )
        mod = "$" if self.isConstant else ""
        if self.noCompartment or self.compartment == "" or self.compartment is None:
            if self.raw is not None:
                txt = "{}{} {} #{} #{}".format(
                    mod,
                    trans_id,
                    self.val,
                    self.raw["returnID"],
                    self.raw["identifier"],
                )
            else:
                txt = "{}{} {}".format(mod, trans_id, self.val)
        else:
            # we have a compartment in our ID
            # need to make sure it's correct
            if "@" in trans_id:
                if re.search(r"(^@)", trans_id):
                    # @X: or @X:: syntax
                    if re.search(r"^@[\S\s]*::", trans_id):
                        trans_id = trans_id.split("::")[1]
                    else:
                        trans_id = trans_id.split(":")[1]
                else:
                    # X@Y syntax
                    trans_id = "@".join(trans_id.split("@")[:-1])
            # removing identical compartments because
            # we'll be usgin @comp: notation
            comp_str = "@{}".format(self.compartment)
            if comp_str in str(trans_id):
                trans_id = str(trans_id).replace(comp_str, "")
            if self.raw is not None:
                txt = "@{}:{}{} {} #{} #{}".format(
                    self.compartment,
                    mod,
                    trans_id,
                    self.val,
                    self.raw["returnID"],
                    self.raw["identifier"],
                )
            else:
                txt = "@{}:{}{} {}".format(self.compartment, mod, trans_id, self.val)
        return txt

    def __repr__(self):
        return str(self)


class Observable:
    def __init__(self):
        self.Id = None
        self.type = "Species"
        self.compartment = None
        self.noCompartment = False
        self.translator = {}
        self.raw = None

    def parse_raw(self, raw):
        self.raw = raw
        self.Id = raw["returnID"]
        self.initConc = raw["initialConcentration"]
        self.initAmount = raw["initialAmount"]
        self.isConstant = raw["isConstant"]
        self.isBoundary = raw["isBoundary"]
        self.compartment = raw["compartment"]
        self.name = raw["name"].replace(" ", "")
        self.identifier = raw["identifier"]

    def get_obs_name(self):
        if self.noCompartment or self.compartment == "" or self.compartment is None:
            return self.Id
        else:
            return "{0}_{1}".format(self.Id, self.compartment)

    def __str__(self):
        txt = self.type
        obs_name = self.get_obs_name()
        if self.raw is not None:
            pattern = (
                self.translator[self.raw["returnID"]]
                if self.Id in self.translator
                else self.raw["returnID"] + "()"
            )
        else:
            pattern = self.Id + "()"
        if self.noCompartment or self.compartment == "":
            txt += " {0} {1} #{2}".format(obs_name, pattern, self.name)
        else:
            # removing identical compartments because
            # we'll be usgin @comp: notation
            comp_str = "@{}".format(self.compartment)
            if comp_str in str(pattern):
                pattern = str(pattern).replace(comp_str, "")
            txt += " {0} @{2}:{1} #{3}".format(
                obs_name, pattern, self.compartment, self.name
            )
        return txt

    def __repr__(self):
        return str(self)


class Function:
    def __init__(self):
        self.Id = None
        self.definition = None
        self.rule_ptr = None
        self.local_dict = None
        self.replaceLocParams = False
        self.all_syms = None
        self.sbmlFunctions = None
        self.compartmentList = None

    def replaceLoc(self, func_def, pdict):
        if self.compartmentList is not None:
            if len(self.compartmentList) > 0:
                for comp in self.compartmentList:
                    cname, cval = comp
                    pdict[cname] = cval
        for parameter in pdict:
            func_def = re.sub(
                r"(\W|^)({0})(\W|$)".format(parameter),
                r"\g<1>{0}\g<3>".format(pdict[parameter]),
                func_def,
            )
        return func_def

    def renameLoc(self, pname, rind):
        return "r{}_{}".format(rind, pname)

    def __str__(self):
        fdef = self.definition
        if self.replaceLocParams:
            # check possible places, local dict first
            if self.local_dict is not None:
                fdef = self.replaceLoc(self.definition, self.local_dict)
            # or pull from the pointer to the rule itself
            elif self.rule_ptr is not None:
                if len(self.rule_ptr.raw_param) > 0:
                    rule_dict = dict([(i[0], i[1]) for i in self.rule_ptr.raw_param])
                    fdef = self.replaceLoc(self.definition, rule_dict)
        # if we are not replacing, we need to rename local parameters
        # to the correct index if the function is related to a rule
        else:
            if self.rule_ptr is not None:
                # this is a fRate, check for local parameters
                if len(self.rule_ptr.raw_param) > 0:
                    # gotta rename these in the function
                    rule_dict = dict(
                        [
                            (i[0], self.renameLoc(i[0], self.rule_ptr.rule_ind))
                            for i in self.rule_ptr.raw_param
                        ]
                    )
                    fdef = self.replaceLoc(self.definition, rule_dict)
        fdef = self.adjust_func_def(fdef)
        return "{} = {}".format(self.Id, fdef)

    def __repr__(self):
        return str(self)

    def adjust_func_def(self, fdef):
        # if this function is related to a rule, we'll pull all the
        # relevant info
        # TODO: Add sbml function resolution here
        if self.sbmlFunctions is not None:
            fdef = self.resolve_sbmlfuncs(fdef)

        if self.rule_ptr is not None:
            # TODO: pull info
            # react/prod/comp
            pass

        # This is stuff ported from bnglWriter
        # deals with comparison operators
        def compParse(match):
            translator = {
                "gt": ">",
                "lt": "<",
                "and": "&&",
                "or": "||",
                "geq": ">=",
                "leq": "<=",
                "eq": "==",
                "neq": "!=",
            }
            exponent = match.group(3)
            operator = translator[match.group(1)]
            return "{0} {1} {2}".format(match.group(2), operator, exponent)

        def changeToBNGL(functionList, rule, function):
            oldrule = ""
            # if the rule contains any mathematical function we need to reformat
            while any(
                [
                    re.search(r"(\W|^)({0})(\W|$)".format(x), rule) != None
                    for x in functionList
                ]
            ) and (oldrule != rule):
                oldrule = rule
                for x in functionList:
                    rule = re.sub("({0})\(([^,]+),([^)]+)\)".format(x), function, rule)
                if rule == oldrule:
                    logMess("ERROR:TRS001", "Malformed pow or root function %s" % rule)
            return rule

        def constructFromList(argList, optionList):
            parsedString = ""
            idx = 0
            translator = {
                "gt": ">",
                "lt": "<",
                "and": "&&",
                "or": "||",
                "geq": ">=",
                "leq": "<=",
                "eq": "==",
            }
            while idx < len(argList):
                if type(argList[idx]) is list:
                    parsedString += (
                        "(" + constructFromList(argList[idx], optionList) + ")"
                    )
                elif argList[idx] in optionList:
                    if argList[idx] == "ceil":
                        parsedString += "min(rint(({0}) + 0.5),rint(({0}) + 1))".format(
                            constructFromList(argList[idx + 1], optionList)
                        )
                        idx += 1
                    elif argList[idx] == "floor":
                        parsedString += (
                            "min(rint(({0}) -0.5),rint(({0}) + 0.5))".format(
                                constructFromList(argList[idx + 1], optionList)
                            )
                        )
                        idx += 1
                    elif argList[idx] in ["pow"]:
                        index = rindex(argList[idx + 1], ",")
                        parsedString += (
                            "(("
                            + constructFromList(argList[idx + 1][0:index], optionList)
                            + ")"
                        )
                        parsedString += (
                            " ^ "
                            + "("
                            + constructFromList(
                                argList[idx + 1][index + 1 :], optionList
                            )
                            + "))"
                        )
                        idx += 1
                    elif argList[idx] in ["sqr", "sqrt"]:
                        tag = "1/" if argList[idx] == "sqrt" else ""
                        parsedString += (
                            "(("
                            + constructFromList(argList[idx + 1], optionList)
                            + ") ^ ({0}2))".format(tag)
                        )
                        idx += 1
                    elif argList[idx] == "root":
                        index = rindex(argList[idx + 1], ",")
                        tmp = (
                            "1/("
                            + constructFromList(argList[idx + 1][0:index], optionList)
                            + "))"
                        )
                        parsedString += (
                            "(("
                            + constructFromList(
                                argList[idx + 1][index + 1 :], optionList
                            )
                            + ") ^ "
                            + tmp
                        )
                        idx += 1
                    elif argList[idx] == "piecewise":
                        index1 = argList[idx + 1].index(",")
                        try:
                            index2 = (
                                argList[idx + 1][index1 + 1 :].index(",") + index1 + 1
                            )
                            try:
                                index3 = (
                                    argList[idx + 1][index2 + 1 :].index(",")
                                    + index2
                                    + 1
                                )
                            except ValueError:
                                index3 = -1
                        except ValueError:
                            parsedString += constructFromList(
                                [argList[idx + 1][index1 + 1 :]], optionList
                            )
                            index2 = -1
                        if index2 != -1:
                            condition = constructFromList(
                                [argList[idx + 1][index1 + 1 : index2]], optionList
                            )
                            result = constructFromList(
                                [argList[idx + 1][:index1]], optionList
                            )
                            if index3 == -1:
                                result2 = constructFromList(
                                    [argList[idx + 1][index2 + 1 :]], optionList
                                )
                            else:
                                result2 = constructFromList(
                                    ["piecewise", argList[idx + 1][index2 + 1 :]],
                                    optionList,
                                )
                            parsedString += "if({0},{1},{2})".format(
                                condition, result, result2
                            )
                        idx += 1
                    elif argList[idx] in ["and", "or"]:
                        symbolDict = {"and": " && ", "or": " || "}
                        indexArray = [-1]
                        elementArray = []
                        for idx2, element in enumerate(argList[idx + 1]):
                            if element == ",":
                                indexArray.append(idx2)
                        indexArray.append(len(argList[idx + 1]))
                        tmpStr = argList[idx + 1]
                        for idx2, _ in enumerate(indexArray[0:-1]):
                            elementArray.append(
                                constructFromList(
                                    tmpStr[indexArray[idx2] + 1 : indexArray[idx2 + 1]],
                                    optionList,
                                )
                            )
                        parsedString += symbolDict[argList[idx]].join(elementArray)
                        idx += 1
                    elif argList[idx] == "lambda":
                        tmp = "("
                        try:
                            upperLimit = rindex(argList[idx + 1], ",")
                        except ValueError:
                            idx += 1
                            continue
                        parsedParams = []
                        for x in argList[idx + 1][0:upperLimit]:
                            if x == ",":
                                tmp += ", "
                            else:
                                tmp += "param_" + x
                                parsedParams.append(x)
                        tmp2 = ") = " + constructFromList(
                            argList[idx + 1][rindex(argList[idx + 1], ",") + 1 :],
                            optionList,
                        )
                        for x in parsedParams:
                            while (
                                re.search(r"(\W|^)({0})(\W|$)".format(x), tmp2) != None
                            ):
                                tmp2 = re.sub(
                                    r"(\W|^)({0})(\W|$)".format(x),
                                    r"\1param_\2 \3",
                                    tmp2,
                                )
                        idx += 1
                        parsedString += tmp + tmp2
                else:
                    parsedString += argList[idx]
                idx += 1
            return parsedString

        # This is where the changes happen
        # comparison operators sorted here
        fdef = changeToBNGL(["gt", "lt", "leq", "geq", "eq"], fdef, compParse)

        contentRule = (
            pyparsing.Word(pyparsing.alphanums + "_")
            | ","
            | "."
            | "+"
            | "-"
            | "*"
            | "/"
            | "^"
            | "&"
            | ">"
            | "<"
            | "="
            | "|"
        )
        parens = pyparsing.nestedExpr("(", ")", content=contentRule)
        finalString = ""

        if any(
            [
                re.search(r"(\W|^)({0})(\W|$)".format(x), fdef) != None
                for x in ["ceil", "floor", "pow", "sqrt", "sqr", "root", "and", "or"]
            ]
        ):
            argList = parens.parseString("(" + fdef + ")").asList()
            fdef = constructFromList(
                argList[0], ["floor", "ceil", "pow", "sqrt", "sqr", "root", "and", "or"]
            )

        while "piecewise" in fdef:
            argList = parens.parseString("(" + fdef + ")").asList()
            fdef = constructFromList(argList[0], ["piecewise"])
        # remove references to lambda functions
        if "lambda(" in fdef:
            lambdaList = parens.parseString("(" + fdef + ")")
            functionBody = constructFromList(lambdaList[0].asList(), ["lambda"])
            fdef = "{0}{1}".format(self.Id, functionBody)

        # change references to time for time()
        while re.search(r"(\W|^)inf(\W|$)", fdef) != None:
            fdef = re.sub(r"(\W|^)(inf)(\W|$)", r"\1 1e20 \3", fdef)

        # combinations '+ -' break bionetgen
        fdef = re.sub(r"(\W|^)([-])(\s)+", r"\1-", fdef)
        # pi
        fdef = re.sub(r"(\W|^)(pi)(\W|$)", r"\g<1>3.1415926535\g<3>", fdef)
        # log for log 10
        fdef = re.sub(r"(\W|^)log\(", r"\1 ln(", fdef)
        # reserved keyword: e
        fdef = re.sub(r"(\W|^)(e)(\W|$)", r"\g<1>__e__\g<3>", fdef)
        # TODO: Check if we need to replace local parameters
        # change references to local parameters
        # for parameter in parameterDict:
        #     finalString = re.sub(r'(\W|^)({0})(\W|$)'.format(parameter),r'\g<1>{0}\g<3>'.format(parameterDict[parameter]),finalString)
        # doing simplification
        try:
            sdef = sympy.sympify(fdef, locals=self.all_syms)
            fdef = prnter.doprint(sdef.nsimplify().evalf().simplify())
            fdef = fdef.replace("**", "^")
        except:
            pass
        return fdef

    def extendFunction(self, function, subfunctionName, subfunction):
        def constructFromList(argList, optionList, subfunctionParam, subfunctionBody):
            parsedString = ""
            idx = 0
            while idx < len(argList):
                if type(argList[idx]) is list:
                    parsedString += (
                        "("
                        + constructFromList(
                            argList[idx], optionList, subfunctionParam, subfunctionBody
                        )
                        + ")"
                    )
                elif argList[idx] in optionList:
                    tmp = subfunctionBody
                    commaIndexes = [0]
                    commaIndexes.extend(
                        [i for i, x in enumerate(argList[idx + 1]) if x == ","]
                    )
                    commaIndexes.append(len(argList[idx + 1]))
                    instancedParameters = [
                        argList[idx + 1][commaIndexes[i] : commaIndexes[i + 1]]
                        for i in range(0, len(commaIndexes) - 1)
                    ]
                    for parameter, instance in zip(
                        subfunctionParam, instancedParameters
                    ):
                        if "," in instance:
                            instance.remove(",")
                        parsedParameter = (
                            " ( "
                            + constructFromList(
                                instance, optionList, subfunctionParam, subfunctionBody
                            )
                            + " ) "
                        )
                        tmp = re.sub(
                            r"(\W|^)({0})(\W|$)".format(parameter.strip()),
                            r"\1{0} \3".format(parsedParameter),
                            tmp,
                        )
                    parsedString += " " + tmp + " "
                    idx += 1
                else:
                    if argList[idx] == "=":
                        parsedString += " " + argList[idx] + " "
                    else:
                        parsedString += argList[idx]
                idx += 1
            return parsedString

        param = subfunction.split(" = ")[0][len(subfunctionName) + 1 : -1]
        # ASS2019: There are cases where the fuction doesn't have a definition and the
        # following line errors out with IndexError, let's handle it.
        try:
            body = subfunction.split(" = ")[1]
        except IndexError as e:
            logMess(
                "ERROR:TRS002",
                "This function doesn't have a definition, note that atomizer doesn't allow for function linking: {}".format(
                    subfunction
                ),
            )
            raise e
        while (
            re.search(r"(\W|^){0}\([^)]*\)(\W|$)".format(subfunctionName), function)
            != None
        ):
            contentRule = (
                pyparsing.Word(pyparsing.alphanums + "_.")
                | ","
                | "+"
                | "-"
                | "*"
                | "/"
                | "^"
                | "&"
                | ">"
                | "<"
                | "="
                | "|"
            )
            parens = pyparsing.nestedExpr("(", ")", content=contentRule)
            subfunctionList = parens.parseString("(" + function + ")").asList()
            function = constructFromList(
                subfunctionList[0], [subfunctionName], param.split(","), body
            )
        return function

    def resolve_sbmlfuncs(self, defn):
        modificationFlag = True
        recursionIndex = 0
        # remove calls to other sbml functions
        while modificationFlag and recursionIndex < 20:
            modificationFlag = False
            for sbml in self.sbmlFunctions:
                if sbml in defn:
                    temp = self.extendFunction(defn, sbml, self.sbmlFunctions[sbml])
                    if temp != defn:
                        defn = temp
                        modificationFlag = True
                        recursionIndex += 1
                        break

        defn = re.sub(r"(\W|^)(time)(\W|$)", r"\1time()\3", defn)
        defn = re.sub(r"(\W|^)(Time)(\W|$)", r"\1time()\3", defn)
        defn = re.sub(r"(\W|^)(t)(\W|$)", r"\1time()\3", defn)

        # remove true and false
        defn = re.sub(r"(\W|^)(true)(\W|$)", r"\1 1\3", defn)
        defn = re.sub(r"(\W|^)(false)(\W|$)", r"\1 0\3", defn)

        # TODO: Make sure we don't need these
        # dependencies2 = {}
        # for idx in range(0, len(functions)):
        #     dependencies2[functions[idx].split(' = ')[0].split('(')[0].strip()] = []
        #     for key in artificialObservables:
        #         oldfunc = functions[idx]
        #         functions[idx] = (re.sub(r'(\W|^)({0})([^\w(]|$)'.format(key), r'\1\2()\3', functions[idx]))
        #         if oldfunc != functions[idx]:
        #             dependencies2[functions[idx].split(' = ')[0].split('(')[0]].append(key)
        #     for element in sbmlfunctions:
        #         oldfunc = functions[idx]
        #         key = element.split(' = ')[0].split('(')[0]
        #         if re.search('(\W|^){0}(\W|$)'.format(key), functions[idx].split(' = ')[1]) != None:
        #             dependencies2[functions[idx].split(' = ')[0].split('(')[0]].append(key)
        #     for element in tfunc:
        #         key = element.split(' = ')[0].split('(')[0]
        #         if key in functions[idx].split(' = ')[1]:
        #             dependencies2[functions[idx].split( ' = ')[0].split('(')[0]].append(key)

        # fd = []
        # for function in functions:
        #     # print(function, '---', dependencies2[function.split(' = ' )[0].split('(')[0]], '---', function.split(' = ' )[0].split('(')[0], 0)
        #     fd.append([function, resolveDependencies(dependencies2, function.split(' = ' )[0].split('(')[0], 0)])
        # fd = sorted(fd, key= lambda rule:rule[1])
        # functions = [x[0] for x in fd]
        # return functions

        # returning expanded definition
        return defn


class Rule:
    def __init__(self):
        self.Id = ""
        self.reactants = []
        self.products = []
        self.rate_cts = (None,)
        self.comment = ""
        self.reversible = False
        self.translator = {}
        self.raw = None
        self.tags = None
        self.model = None

    def parse_raw(self, raw):
        self.raw = raw
        self.raw_react = raw["reactants"]
        self.raw_prod = raw["products"]
        self.raw_param = raw["parameters"]
        self.raw_rates = raw["rates"]
        # self.raw_orates = raw['orates']
        self.raw_num = raw["numbers"]
        self.raw_splt = raw["split_rxn"]
        self.reversible = raw["reversible"]
        self.Id = raw["reactionID"]

    def __str__(self):
        if self.Id != "":
            txt = "{}: ".format(self.Id)
        else:
            txt = ""
        # reactants
        if len(self.reactants) == 0:
            txt += "0"
        else:
            for ir, react in enumerate(self.reactants):
                if ir != 0:
                    txt += " + "
                if react[0] in self.translator:
                    if self.tags is not None and not self.noCompartment:
                        if react[2] in self.tags:
                            tag = self.tags[react[2]]
                        elif react[0] in self.tags:
                            tag = self.tags[react[0]]
                        else:
                            tag = ""
                        react_str = str(self.translator[react[0]])
                        if not react_str.endswith(tag):
                            if "@" in tag:
                                splt = react_str.split("@")
                                tspl = tag.split("@")
                                if splt[-1] != tspl[-1]:
                                    splt[-1] = tspl[-1]
                                    react_str = "@".join(splt)
                    else:
                        react_str = str(self.translator[react[0]])
                else:
                    if self.tags is not None and not self.noCompartment:
                        if react[2] in self.tags:
                            react_str = str(react[0]) + "()" + self.tags[react[2]]
                        elif react[0] in self.tags:
                            react_str = str(react[0]) + "()" + self.tags[react[0]]
                        else:
                            react_str = str(react[0]) + "()"
                    else:
                        react_str = str(react[0]) + "()"
                # Apply stoichiometry
                # FIXME: What to do if stoichiometry is not an integer
                for i in range(int(react[1])):
                    if i > 0:
                        txt += " + "
                    txt += react_str
        # correct rxn arrow
        if self.reversible and len(self.rate_cts) == 2:
            txt += " <-> "
        else:
            txt += " -> "
        # products
        if len(self.products) == 0:
            txt += "0"
        else:
            for ip, prod in enumerate(self.products):
                if ip != 0:
                    txt += " + "
                if prod[0] in self.translator:
                    if self.tags is not None and not self.noCompartment:
                        if prod[2] in self.tags:
                            tag = self.tags[prod[2]]
                        elif react[0] in self.tags:
                            tag = self.tags[prod[0]]
                        else:
                            tag = ""
                        prod_str = str(self.translator[prod[0]])
                        if not prod_str.endswith(tag):
                            if "@" in tag:
                                splt = prod_str.split("@")
                                tspl = tag.split("@")
                                if splt[-1] != tspl[-1]:
                                    splt[-1] = tspl[-1]
                                    prod_str = "@".join(splt)
                    else:
                        prod_str = str(self.translator[prod[0]])
                else:
                    if self.tags is not None and not self.noCompartment:
                        if prod[2] in self.tags:
                            prod_str = str(prod[0]) + "()" + self.tags[prod[2]]
                        elif prod[0] in self.tags:
                            prod_str = str(prod[0]) + "()" + self.tags[prod[0]]
                        else:
                            prod_str = str(prod[0]) + "()"
                    else:
                        prod_str = str(prod[0]) + "()"
                # Apply stoichiometry
                # FIXME: What to do if stoichiometry is not an integer
                for i in range(int(prod[1])):
                    if i > 0:
                        txt += " + "
                    txt += prod_str
        if self.reversible and len(self.rate_cts) == 2:
            if self.model is not None:
                if len(self.model.param_repl) > 0:
                    for prep in self.model.param_repl:
                        if self.rate_cts[0] == prep:
                            self.rate_cts = (
                                self.model.param_repl[prep],
                                self.rate_cts[1],
                            )
                        if self.rate_cts[1] == prep:
                            self.rate_cts = (
                                self.rate_cts[0],
                                self.model.param_repl[prep],
                            )
        else:
            if self.model is not None:
                if len(self.model.param_repl) > 0:
                    for prep in self.model.param_repl:
                        if self.rate_cts[0] == prep:
                            self.rate_cts = (self.model.param_repl[prep],)
        if self.model is not None:
            # rate cts
            if self.reversible and len(self.rate_cts) == 2:
                # we need to check if the rate constant refers to an
                # observable and is alone
                if (
                    self.rate_cts[0] in self.model.obs_map
                    or self.rate_cts[0] in self.model.observables
                ):
                    r0 = "1*{0}".format(self.rate_cts[0])
                else:
                    r0 = "{}".format(self.rate_cts[0])
                if (
                    self.rate_cts[1] in self.model.obs_map
                    or self.rate_cts[1] in self.model.observables
                ):
                    r1 = "1*{0}".format(self.rate_cts[1])
                else:
                    r1 = "{}".format(self.rate_cts[1])
                txt += " {},{}".format(r0, r1)
            else:
                if (
                    self.rate_cts[0] in self.model.obs_map
                    or self.rate_cts[0] in self.model.observables
                ):
                    txt += " 1*{}".format(self.rate_cts[0])
                else:
                    txt += " {}".format(self.rate_cts[0])

        comment = ""
        if self.raw is not None:
            comment = (
                "Modifiers({0})".format(", ".join(self.raw["modifiers"]))
                if self.raw["modifiers"]
                else ""
            )
        if comment != "":
            txt += " #{}".format(comment)
        return txt

    def __repr__(self):
        return str(self)


class ARule:
    def __init__(self):
        self.Id = None
        self.rates = None
        self.isAssignment = None
        self.isRate = None

    def parse_raw(self, raw):
        self.Id = raw[0]
        self.rates = raw[1]
        self.isAssignment = raw[2]
        self.isRate = raw[3]

    def __str__(self):
        return "{} {}".format(self.Id, self.rates)

    def __repr__(self):
        return str(self)


# Model objects done


class bngModel:
    """
    Takes in atomizer stuff and turns everything
    into objects which can be used to print the
    final model
    """

    def __init__(self):
        self.parameters = {}
        self.compartments = {}
        self.molecules = {}
        self.species = {}
        self.observables = {}
        self.rules = {}
        self.arules = {}
        self.functions = {}
        #
        self.metaString = ""
        self.molecule_ids = {}
        self.translator = {}
        self.obs_map = {}
        self.molecule_mod_dict = {}
        self.parsed_func = {}
        self.noCompartment = None
        self.useID = False
        self.replaceLocParams = False
        self.all_syms = None
        self.function_order = None
        self.sbmlFunctions = None
        self.tags = None
        self.param_repl = []

    def __str__(self):
        txt = self.metaString

        txt += "begin model\n"

        if len(self.parameters.values()) > 0:
            txt += "begin parameters\n"
            for param in self.parameters.values():
                txt += "  " + str(param) + "\n"
            txt += "end parameters\n"

        if not self.noCompartment:
            txt += "begin compartments\n"
            for comp in self.compartments.values():
                txt += "  " + str(comp) + "\n"
            txt += "end compartments\n"

        if len(self.molecules.values()) > 0:
            txt += "begin molecule types\n"
            for molec in self.molecules.values():
                molec.translator = self.translator
                txt += "  " + str(molec) + "\n"
            txt += "end molecule types\n"

        if len(self.species.values()) > 0:
            txt += "begin seed species\n"
            for spec in self.species.values():
                spec.translator = self.translator
                if spec.val > 0:
                    spec.noCompartment = self.noCompartment
                    txt += "  " + str(spec) + "\n"
            txt += "end seed species\n"

        if len(self.observables.values()) > 0:
            txt += "begin observables\n"
            for obs in self.observables.values():
                obs.translator = self.translator
                obs.noCompartment = self.noCompartment
                txt += "  " + str(obs) + "\n"
            txt += "end observables\n"

        if len(self.functions) > 0:
            txt += "begin functions\n"
            if self.function_order is None:
                for func in self.functions.values():
                    func.sbmlFunctions = self.sbmlFunctions
                    func.replaceLocParams = self.replaceLocParams
                    # we need to update the local dictionary
                    # with potential observable name changes
                    if len(self.obs_map) > 1:
                        if func.local_dict is not None:
                            func.local_dict.update(self.obs_map)
                        else:
                            func.local_dict = self.obs_map
                    if len(self.param_repl) > 1:
                        if func.local_dict is not None:
                            func.local_dict.update(self.param_repl)
                        else:
                            func.local_dict = self.param_repl
                    if func.Id in self.parsed_func:
                        func.sympy_parsed = self.parsed_func[fkey]
                    func.all_syms = self.all_syms
                    txt += "  " + str(func) + "\n"
            else:
                for fkey in self.function_order:
                    func = self.functions[fkey]
                    func.sbmlFunctions = self.sbmlFunctions
                    func.replaceLocParams = self.replaceLocParams
                    # we need to update the local dictionary
                    # with potential observable name changes
                    if len(self.obs_map) > 1:
                        if func.local_dict is not None:
                            func.local_dict.update(self.obs_map)
                        else:
                            func.local_dict = self.obs_map
                    if len(self.param_repl) > 1:
                        if func.local_dict is not None:
                            func.local_dict.update(self.param_repl)
                        else:
                            func.local_dict = self.param_repl
                    if func.Id in self.parsed_func:
                        func.sympy_parsed = self.parsed_func[fkey]
                    func.all_syms = self.all_syms
                    txt += "  " + str(func) + "\n"
            txt += "end functions\n"

        if len(self.rules.values()) > 0:
            txt += "begin reaction rules\n"
            for rule in self.rules.values():
                rule.translator = self.translator
                rule.tags = self.tags
                rule.noCompartment = self.noCompartment
                rule.model = self
                txt += "  " + str(rule) + "\n"
            txt += "end reaction rules\n"

        txt += "end model"

        return txt

    def __repr__(self):
        return str((self.parameters, self.molecules))

    def consolidate_arules(self):
        """
        this figures out what to do with particular
        assignment rules pulled from SBML.
        a) A non-constant parameter gets turned into
           a function
        b) Any species in the system can be modified
           by an assignment rule. This turns the species
           into a function which also requires a modification
           of any reaction rules the species is associated with
        c) rate rules get turned into syn reactions
        """
        for arule in self.arules.values():
            # first one is to check parameters
            if arule.isRate:
                # this is a rate rule, it'll be turned into a reaction
                # first make the entry in molecules
                if len(self.compartments) > 0 and not self.noCompartment:
                    comp = list(self.compartments.values())[0].Id
                else:
                    comp = None
                amolec = self.make_molecule()
                amolec.Id = arule.Id
                amolec.name = arule.Id
                if comp is not None:
                    amolec.compartment = self.compartments[comp]
                self.add_molecule(amolec)
                # turn the rate cts into a function
                nfunc = self.make_function()
                nfunc.Id = "rrate_{}".format(amolec.Id)
                nfunc.definition = arule.rates[0]
                self.add_function(nfunc)
                # now make the rule
                if comp is not None:
                    prod_id = "{}()@{}".format(arule.Id, comp)
                else:
                    prod_id = "{}".format(arule.Id)
                nrule = self.make_rule()
                nrule.Id = "rrule_{}".format(arule.Id)
                nrule.products.append([prod_id, 1.0, prod_id])
                nrule.rate_cts = (nfunc.Id,)
                self.add_rule(nrule)
                # add observable
                nobs = self.make_observable()
                nobs.Id = arule.Id
                nobs.name = "rrule_{}".format(arule.Id)
                nobs.compartment = comp
                self.add_observable(nobs)
                # remove from parameters if exists
                # otherwise we can get namespace clashes
                # with observables
                if arule.Id in self.parameters:
                    seed_val = self.parameters.pop(arule.Id).val
                else:
                    seed_val = 0
                # add species
                nspec = self.make_species()
                nspec.Id = arule.Id
                nspec.name = arule.Id
                nspec.val = seed_val
                nspec.isConstant = False
                if comp is not None:
                    nspec.compartment = comp
                self.add_species(nspec)
            elif arule.isAssignment:
                # rule is an assignment rule
                # let's first check parameters
                if arule.Id in self.parameters:
                    a_param = self.parameters[arule.Id]
                    # if not a_param.cts:
                    # this means that one of our parameters
                    # is _not_ a constant and is modified by
                    # an assignment rule
                    # TODO: Not sure if anything else
                    # can happen here. Confirm via SBML spec
                    a_param = self.parameters.pop(arule.Id)
                    # TODO: check if an initial value to
                    # a non-constant parameter is relevant?
                    # I think the only thing we need is to
                    # turn this into a function
                    fobj = self.make_function()
                    fobj.Id = arule.Id
                    fobj.definition = arule.rates[0]
                    self.add_function(fobj)
                elif arule.Id in self.molecule_ids:
                    # we are an assignment rule that modifies
                    # a molecule, this will be converted to
                    # a function if true
                    mname = self.molecule_ids[arule.Id]
                    molec = self.molecules[mname]
                    # We can't have the molecule be _constant_
                    # at which point it's supposed to be encoded
                    # with "$" in BNGL
                    if not molec.isConstant:
                        # we can have it be boundary or not, doesn't
                        # matter since we know an assignment rule is
                        # modifying it and it will take over reactions

                        # this should be guarantee
                        molec = self.molecules.pop(mname)

                        # we should also remove this from species
                        # and/or observables, this checks for
                        # namespace collisions.
                        # TODO: We might want to
                        # remove parameters as well
                        if molec.name in self.observables:
                            obs = self.observables.pop(molec.name)
                            self.obs_map[obs.get_obs_name()] = molec.Id + "()"
                        elif molec.Id in self.observables:
                            obs = self.observables.pop(molec.Id)
                            self.obs_map[obs.get_obs_name()] = molec.Id + "()"
                        if molec.name in self.species:
                            spec = self.species.pop(molec.name)
                        elif molec.Id in self.species:
                            spec = self.species.pop(molec.Id)
                        if molec.Id in self.parameters:
                            param = self.parameters.pop(molec.Id)

                        # this will be a function
                        fobj = self.make_function()
                        # TODO: sometimes molec.name is not
                        # normalized, check if .Id works consistently
                        fobj.Id = molec.Id + "()"
                        fobj.definition = arule.rates[0]
                        if len(arule.compartmentList) > 0:
                            fobj.local_dict = {}
                            for comp in arule.compartmentList:
                                cname, cval = comp
                                fobj.local_dict[cname] = cval
                        self.add_function(fobj)
                        # we want to make sure arules are the only
                        # things that change species concentrations
                        if (
                            mname in self.molecule_mod_dict
                            or molec.Id in self.molecule_mod_dict
                        ):
                            if mname in self.molecule_mod_dict:
                                mkey = mname
                            else:
                                mkey = molec.Id
                            for rule in self.molecule_mod_dict[mkey]:
                                if len(rule.reactants) == 0 and len(rule.products) == 1:
                                    # this is a syn rule, should be only generating the species in question
                                    if mkey == rule.products[0][0]:
                                        if rule.Id in self.rules:
                                            self.rules.pop(rule.Id)
                                else:
                                    # this is a more complicated rule, we need to adjust the rates
                                    for ir, react in enumerate(rule.reactants):
                                        if react[0] == mkey:
                                            # we have the molecule in reactants
                                            if len(rule.rate_cts) == 2:
                                                r = rule.reactants.pop(ir)
                                                fw, bk = rule.rate_cts
                                                rule.rate_cts = (
                                                    "{0}*".format(mkey) + fw,
                                                    bk,
                                                )
                                            else:
                                                r = rule.reactants.pop(ir)
                                                fw = rule.rate_cts[0]
                                                rule.rate_cts = (
                                                    "{0}*".format(mkey) + fw,
                                                )
                                    for ip, prod in enumerate(rule.products):
                                        if prod[0] == mkey:
                                            # molecule in products
                                            if len(rule.rate_cts) == 2:
                                                # adjust back rate
                                                p = rule.products.pop(ip)
                                                fw, bk = rule.rate_cts
                                                rule.rate_cts = (
                                                    fw,
                                                    "{0}*".format(mkey) + bk,
                                                )
                                            else:
                                                # we can just remove
                                                rule.products.pop(ip)
                                    if len(rule.reactants) == 0 and len(rule.products):
                                        if rule.Id in self.rules:
                                            self.rules.pop(rule.Id)

                else:
                    # this is just a simple assignment (hopefully)
                    # just convert to a function
                    fobj = self.make_function()
                    fobj.Id = arule.Id + "()"
                    fobj.definition = arule.rates[0]
                    self.add_function(fobj)
                    # we also might need to remove these from
                    # observables
                    if arule.Id in self.observables:
                        obs = self.observables.pop(arule.Id)
                        self.obs_map[obs.get_obs_name()] = fobj.Id
                    # we also have to remove this from rules
                    if arule.Id in self.molecule_mod_dict:
                        mkey = arule.Id
                        for rule in self.molecule_mod_dict[mkey]:
                            if len(rule.reactants) == 0 and len(rule.products) == 1:
                                # this is a syn rule, should be only generating the species in question
                                if mkey == rule.products[0][0]:
                                    if rule.Id in self.rules:
                                        self.rules.pop(rule.Id)
                            else:
                                # this is a more complicated rule, we need to adjust the rates
                                for ir, react in enumerate(rule.reactants):
                                    if react[0] == mkey:
                                        # we have the molecule in reactants
                                        if len(rule.rate_cts) == 2:
                                            r = rule.reactants.pop(ir)
                                            fw, bk = rule.rate_cts
                                            rule.rate_cts = (
                                                "{0}*".format(mkey) + fw,
                                                bk,
                                            )
                                        else:
                                            r = rule.reactants.pop(ir)
                                            fw = rule.rate_cts[0]
                                            rule.rate_cts = ("{0}*".format(mkey) + fw,)
                                for ip, prod in enumerate(rule.products):
                                    if prod[0] == mkey:
                                        # molecule in products
                                        if len(rule.rate_cts) == 2:
                                            # adjust back rate
                                            p = rule.products.pop(ip)
                                            fw, bk = rule.rate_cts
                                            rule.rate_cts = (
                                                fw,
                                                "{0}*".format(mkey) + bk,
                                            )
                                        else:
                                            # we can just remove
                                            rule.products.pop(ip)
                                if len(rule.reactants) == 0 and len(rule.products):
                                    if rule.Id in self.rules:
                                        self.rules.pop(rule.Id)
            else:
                # not sure what this means, read SBML spec more
                pass

    def consolidate_molecules(self):
        # potentially remove unused ones
        # or EmptySet and similar useless ones
        turn_param = []
        str_comp = []
        to_remove = []
        for molec in self.molecules:
            if molec not in self.molecule_mod_dict:
                if self.molecules[molec].isConstant:
                    if not self.molecules[molec].isBoundary:
                        turn_param.append(molec)
                        continue
            mstr = str(self.molecules[molec])
            if mstr not in str_comp:
                str_comp.append(mstr)
            else:
                # we already have this
                to_remove.append(molec)
        for torem in to_remove:
            self.molecules.pop(torem)
        for molec in turn_param:
            m = self.molecules.pop(molec)
            param = self.make_parameter()
            param.Id = m.Id
            param.val = m.initConc if m.initConc > 0 else m.initAmount
            self.add_parameter(param)
            if m.name in self.observables:
                self.observables.pop(m.name)
            elif m.Id in self.observables:
                self.observables.pop(m.Id)
            if m.name in self.species:
                self.species.pop(m.name)
            elif m.Id in self.species:
                self.species.pop(m.Id)

    def consolidate_observables(self):
        # if we are using compartments, we need
        # to adjust names in functions to match
        # with new observable names
        for obs in self.observables:
            obs_obj = self.observables[obs]
            oname = obs_obj.get_obs_name()
            self.obs_map[obs_obj.Id] = oname
            if oname in self.parameters:
                self.parameters.pop(oname)

    def consolidate_compartments(self):
        if len(self.compartments) == 1:
            comp_key = list(self.compartments.keys())[0]
            comp = self.compartments[comp_key]
            if comp.size == 1.0:
                _ = self.compartments.pop(comp_key)
                self.noCompartment = True

    def consolidate(self):
        self.consolidate_compartments()
        self.consolidate_arules()
        self.consolidate_molecules()
        self.consolidate_observables()
        self.reorder_functions()

    def remove_sympy_symbols(self, fdef):
        to_replace = {
            "def": "__DEF__",
            "lambda": "__LAMBDA__",
            "as": "__AS__",
            "del": "__DEL__",
        }
        for rep_str in to_replace:
            if re.search(r"(\W|^)({0})(\W|$)".format(rep_str), fdef):
                fdef = re.sub(
                    r"(\W|^)({0})(\W|$)".format(rep_str),
                    r"\g<1>{0}\g<3>".format(to_replace[rep_str]),
                    fdef,
                )
        return fdef

    def reorder_functions(self):
        """
        this one is to make sure the functions are reordered
        correctly, should be ported from the original codebase
        """
        # initialize dependency graph
        func_names = {}
        dep_dict = {}
        for fkey in self.functions:
            func = self.functions[fkey]
            # this finds the pure function name
            # with or without parans
            ma = re.search(r"(\W|^)(\w*)(\(*)(\w*)(\)*)(\W|$)", fkey)
            pure_name = ma.group(2)
            func_names[pure_name] = func.Id
            if "fRate" not in func.Id:
                dep_dict[func.Id] = []
        # make dependency graph between funcs only
        func_order = []
        unparsed = []
        frates = []
        func_dict = {}
        # Let's replace and build dependency map
        for fkey in self.functions:
            func = self.functions[fkey]
            f = func.definition
            f = self.remove_sympy_symbols(f)
            try:
                fs = sympy.sympify(f, locals=self.all_syms)
                self.parsed_func[fkey] = fs
            except:
                # Can't parse this func
                if fkey.startswith("fRate"):
                    frates.append(fkey)
                else:
                    unparsed.append(fkey)
                continue
            func_dict[fkey] = fs
            # need to build a dependency graph to figure out what to
            # write first
            # We can skip this if it's a functionRate
            if "fRate" not in fkey:
                list_of_deps = list(map(str, fs.atoms(sympy.Symbol)))
                for dep in list_of_deps:
                    if dep in func_names:
                        dep_dict[fkey].append(func_names[dep])
            else:
                frates.append(fkey)
        # Now reorder accordingly
        ordered_funcs = []
        # this ensures we write the independendent functions first
        stck = sorted(dep_dict.keys(), key=lambda x: len(dep_dict[x]))
        # FIXME: This algorithm works but likely inefficient
        while len(stck) > 0:
            k = stck.pop()
            deps = dep_dict[k]
            if len(deps) == 0:
                if k not in ordered_funcs:
                    ordered_funcs.append(k)
            else:
                stck.append(k)
                for dep in deps:
                    if dep not in ordered_funcs:
                        stck.append(dep)
                    dep_dict[k].remove(dep)
        # print ordered functions and return
        ordered_funcs += frates
        self.function_order = ordered_funcs

    # model object creator and adder methods
    def add_parameter(self, param):
        self.parameters[param.Id] = param

    def make_parameter(self):
        return Parameter()

    def add_compartment(self, comp):
        # TODO: check if we really want this, this
        # replaces compartment in functions with their size
        self.obs_map[comp.Id] = comp.size
        self.compartments[comp.Id] = comp

    def make_compartment(self):
        return Compartment()

    def add_molecule(self, molec):
        # we might have to add molecules that
        # didn't have rawSpecies associated with
        if hasattr(molec, "raw"):
            self.molecule_ids[molec.raw["identifier"]] = molec.name
        if not molec.name in self.molecules:
            self.molecules[molec.name] = molec
        else:
            # TODO: check if this actually works for
            # everything, there are some cases where
            # the same molecule is actually different
            # e.g. 103
            if not molec.Id in self.molecules:
                self.molecules[molec.Id] = molec
            elif hasattr(molec, "raw"):
                self.molecules[molec.identifier] = molec
            else:
                print("molecule doesn't have identifier {}".format(molec))
                pass

    def make_molecule(self):
        return Molecule()

    def add_species(self, sspec):
        if not sspec.name in self.species:
            self.species[sspec.name] = sspec
        elif hasattr(sspec, "identifier"):
            self.species[sspec.identifier] = sspec
        else:
            print("species doesn't have identifier {}".format(sspec))
            pass

    def make_species(self):
        return Species()

    def add_observable(self, obs):
        if not obs.Id in self.observables:
            self.observables[obs.Id] = obs
        elif hasattr(obs, "identifier"):
            self.observables[obs.identifier] = obs
        else:
            print("observable doesn't have identifier {}".format(obs))
            pass

    def make_observable(self):
        return Observable()

    def make_function(self):
        return Function()

    def add_function(self, func):
        self.functions[func.Id] = func

    def make_rule(self):
        return Rule()

    def add_rule(self, rule):
        # add this to keep track of molecule modifications
        # this will allow us to quickly loop over reactons
        # a molecule is a part of if the molecule gets
        # turned to a function
        for react in rule.reactants:
            if react[0] not in self.molecule_mod_dict:
                self.molecule_mod_dict[react[0]] = []
            self.molecule_mod_dict[react[0]].append(rule)
        for prod in rule.products:
            if prod[0] not in self.molecule_mod_dict:
                self.molecule_mod_dict[prod[0]] = []
            self.molecule_mod_dict[prod[0]].append(rule)
        self.rules[rule.Id] = rule

    def make_arule(self):
        return ARule()

    def add_arule(self, arule):
        self.arules[arule.Id] = arule
