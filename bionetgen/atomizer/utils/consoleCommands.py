# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 18:11:35 2013

@author: proto
"""

import platform

import bionetgen
import subprocess
import os

from os.path import expanduser, join

home = expanduser("~")


def setBngExecutable(executable):
    global bngExecutable
    bngExecutable = executable


def getBngExecutable():
    return bngExecutable


def bngl2xml(bnglFile, timeout=60):
    mdl = bionetgen.modelapi.bngmodel(bnglFile)
    mdl.bngparser.bngfile.write_xml(bnglFile, xml_type="bngxml", bngl_str=str(mdl))
    # TODO: Deal with timeout here
