# -*- coding: utf-8 -*-
"""
Created on Sun Mar 25 21:26:49 2012

@author: proto
"""
from __future__ import division
import json
from functools import partial
import marshal

from pyparsing import (
    Literal,
    CaselessLiteral,
    Word,
    Combine,
    Group,
    Optional,
    ZeroOrMore,
    Forward,
    nums,
    alphas,
    oneOf,
    alphanums,
)
import math
import operator
import logging
import pickle
import os
from subprocess import call
import sys
import fnmatch
import functools
import pylru


def pmemoize(obj):
    cache = obj.cache = pylru.lrucache(500)

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = marshal.dumps([args, kwargs])
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer


# import progressbar

# sys.path.insert(0, '../utils/')
# import consoleCommands as console


class memoize(object):
    """cache the return value of a method

    This class is meant to be used as a decorator of methods. The return value
    from a given method invocation will be cached on the instance whose method
    was invoked. All arguments passed to a method decorated with memoize must
    be hashable.

    If a memoized method is invoked directly on its class the result will not
    be cached. Instead the method will be invoked like a static method:
    class Obj(object):
        @memoize
        def add_to(self, arg):
            return self + arg
    Obj.add_to(1) # not enough arguments
    Obj.add_to(1, 2) # returns 3, result is not cached
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.func
        return partial(self, obj)

    def __call__(self, *args, **kw):
        obj = args[0]
        try:
            cache = obj.__cache
        except AttributeError:
            cache = obj.__cache = {}
        key = (self.func, marshal.dumps(args[1:]), frozenset(kw.items()))
        try:
            res = cache[key]
        except KeyError:
            res = cache[key] = self.func(*args, **kw)
        return res


# ASS: optimizing the memoization method used with
# resolveHelper method specifically to use less
# memory, important in certain larger models
class memoizeMapped(object):
    """
    Optimized local cache for recursive resolveHelper method
    to limit memory usage
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.func
        return partial(self, obj)

    def __call__(self, obj, gkey, react, mem, withMod):
        key1 = gkey
        key2 = react
        # This memory hash is a bit suspect,
        key3 = hash(tuple(sorted(mem)))
        key4 = withMod
        try:
            res = self.cache[key1][key2][key3][key4]
        except KeyError:
            try:
                d = self.cache[key1]
            except KeyError:
                self.cache[key1] = {}
            try:
                d = self.cache[key1][key2]
            except KeyError:
                self.cache[key1][key2] = {}
            try:
                d = self.cache[key1][key2][key3]
            except KeyError:
                self.cache[key1][key2][key3] = {}
            try:
                d = self.cache[key1][key2][key3][key4]
            except KeyError:
                self.cache[key1][key2][key3][key4] = None
            res = self.cache[key1][key2][key3][key4] = self.func(
                obj, gkey, react, mem, withMod
            )
        return res


class TranslationException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NumericStringParser(object):

    """
    Most of this code comes from the fourFn.py pyparsing example

    """

    def pushFirst(self, strg, loc, toks):
        self.exprStack.append(toks[0])

    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0] == "-":
            self.exprStack.append("unary -")

    def __init__(self):
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(
            Word("+-" + alphanums + "_", alphanums + "_")
            + Optional(point + Optional(Word(alphanums + "_")))
            + Optional(e + Word("+-" + alphanums + "_", alphanums + "_"))
        )

        ident = Word(alphas, alphanums + "_")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()

        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        function = ident + lpar + expr + ZeroOrMore("," + expr) + rpar
        atom = (
            (
                Optional(oneOf("- +"))
                + (pi | e | function | fnumber).setParseAction(self.pushFirst)
            )
            | Optional(oneOf("- +")) + Group(lpar + expr + rpar)
        ).setParseAction(self.pushUMinus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor + ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        expr << term + ZeroOrMore((addop + term).setParseAction(self.pushFirst))
        # addop_term = ( addop + term ).setParseAction( self.pushFirst )
        # general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        # expr <<  general_term
        self.bnf = expr
        # map operator symbols to corresponding arithmetic operations
        epsilon = 1e-12
        self.opn = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "^": operator.pow,
        }
        self.fn = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "abs": abs,
            "trunc": lambda a: int(a),
            "round": round,
            "sgn": lambda a: abs(a) > epsilon and cmp(a, 0) or 0,
        }

    def evaluateStack(self, s):
        op = s.pop()
        print(op)
        if op == "unary -":
            return -self.evaluateStack(s)
        if op in "+-*/^":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op](self.evaluateStack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string, parseAll=True):
        self.exprStack = []
        # remove comments
        if num_string.find("#") != -1:
            num_string = num_string[0 : num_string.find("#")]
        try:
            results = self.bnf.parseString(num_string, parseAll)
            return True
        except:
            return False

        # val=self.evaluateStack( self.exprStack[:] )
        # return val


def defaultReactionDefinition():
    listOfReactions = {"1": [["S0", "S1"], ["S2"]], "2": [["S2"], ["S0", "S1"]]}
    listOfDefinitions = {"Binding": [1, 2]}
    final = {"reactions": listOfReactions, "definitions": listOfDefinitions}
    with open("reactionDefinition.json", "w") as fp:
        json.dump(final, fp)


def setupLog(fileName, level, quietMode=False):
    if quietMode:
        logging.basicConfig(filename=fileName, level=level, filemode="w")
    else:
        logging.basicConfig(level=level)


def setupStreamLog(console):
    formatter = logging.Formatter("%(name)-10s:%(levelname)-8s:%(message)s")
    # tell the handler to use this format
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

    # set a format which is simpler for console use
    # formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # console.setFormatter(formatter)
    # add the handler to the root logger
    # console = logging.StreamHandler()
    # console.setLevel(logging.WARNING)
    # logging.getLogger('').addHandler(console)

    # logging.basicConfig(stream=stream, level=level, filemode='w')


def finishStreamLog(console):
    logging.getLogger().removeHandler(console)


def logMess(logType, logMessage):

    level = logType.split(":")[0]
    module = logType.split(":")[1]
    logger = logging.getLogger(module)

    if level == "INFO":
        logger.info(logMessage)
    elif level == "DEBUG":
        logger.debug(logMessage)
    elif level == "WARNING":
        logger.warning(logMessage)
    elif level == "CRITICAL":
        logger.critical(logMessage)
    elif level == "ERROR":
        logger.error(logMessage)


def testBNGFailure(fileName):
    with open(os.devnull, "w") as f:
        result = call(["bngdev", fileName], stdout=f)
    return result


import os.path

'''
def getValidFiles(directory, extension):
    """
    Gets a list of bngl files that could be correctly translated in a given 'directory'
    """
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, '*.{0}'.format(extension)):
            matches.append(os.path.join(root, filename))
    for i in xrange(len(matches)):
        matches[i] = (matches[i], os.path.getsize(matches[i]))
    matches.sort(key=lambda filename: filename[1], reverse=False)
    matches = [x[0] for x in matches]
    return matches


def generateBNGXML(directory):

    bnglFiles = getValidFiles(directory, 'bngl')
    print('converting {0} bnglfiles'.format(len(bnglFiles)))
    progress = progressbar.ProgressBar()
    for i in progress(range(len(bnglFiles))):
        xmlName = '.'.join(bnglFiles[i].split('.')[:-1]) + '.xml'
        

        if os.path.exists(xmlName):
            continue
        console.bngl2xml(bnglFiles[i], timeout=10)

    print('moving xml files')
    files = glob.iglob(os.path.join('.', "*.xml"))
    for xmlfile in files:
        if os.path.isfile(xmlfile):
            shutil.move(xmlfile, directory)
'''


if __name__ == "__main__":
    """
    with open('failure.dump','rb') as f:
        failedFiles = pickle.load(f)
    failedFiles.sort()
    for bng in failedFiles:
        sys.stderr.write(bng)
        testBNGFailure(bng)
    """
    generateBNGXML("new_non_curated")
