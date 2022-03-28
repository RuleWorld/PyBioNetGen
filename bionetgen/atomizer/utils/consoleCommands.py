# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 18:11:35 2013

@author: proto
"""
import bionetgen


def setBngExecutable(executable):
    global bngExecutable
    bngExecutable = executable


def getBngExecutable():
    return bngExecutable


def bngl2xml(bnglFile, timeout=60):
    mdl = bionetgen.modelapi.bngmodel(bnglFile)
    xml_file = bnglFile.replace(".bngl", ".xml")
    with open(xml_file, "w+") as f:
        mdl.bngparser.bngfile.write_xml(f, xml_type="bngxml", bngl_str=str(mdl))
    # TODO: Deal with timeout here
