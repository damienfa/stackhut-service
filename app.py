#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slackhut-service Service
"""
import stackhut
import sys
import json
from generateConfFromPDF import PDF

class Default(stackhut.Service):
    def add(self, x, y):
        return x + y

    def generateConfFromPDF(self, pdfUrl):
    	in_file = stackhut.download_file(pdfUrl)
    	return json.dumps( PDF(in_file).getAllAnnots() ,indent=4)


# export the services
SERVICES = {"Default": Default()}