import os
import json
import shutil
import dates
import utils

import bottle


@bottle.get('/:filename#.*#')
def get_file(filename):    
    d = True if ('downloads' in filename or 'attachments' in filename) else False
    response =  bottle.static_file(filename, 
                              root='.',
                              download = d)
    #no caching !!!
    #http://stackoverflow.com/questions/24672996/python-bottle-and-cache-control
    response.set_header("Cache-Control", "public, max-age=604800")
    return response    
    
        
"""
If you look at the Google URL below - the version of jQuery can be specified in the URL (1.8.0).
If you would like to use the latest version of jQuery, you can either remove a number from 
the end of the version string (for example 1.8), then Google will return the latest version 
available in the 1.8 series (1.8.0, 1.8.1, etc.), or you can take it up to the whole number (1),
and Google will return the latest version available in the 1 series (from 1.1.0 to 1.9.9).
"""

JQUERY_CODE = """
<script src='http://ajax.googleapis.com/ajax/libs/jquery/2.0.3/jquery.min.js'></script>
<script src='http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.3/jquery-ui.js'></script>
"""

JQUERY_CSS = """
<link href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/themes/base/jquery-ui.css" rel="stylesheet" type="text/css"/>
<link href="http://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" rel="stylesheet" type="text/css"/>
"""

GOOGLE_JS_API = """
<script type="text/javascript" src = "http://www.google.com/jsapi" charset="utf-8"></script>
"""

def CSS(cssFile):
    return '<link href="/%s" rel="stylesheet">' % cssFile

def CSS_PRINT(cssFile):
    return '<link href="/%s" rel="stylesheet" media="print">' % cssFile

def JS(jsFile):
    return '<script src="/%s"></script>' % jsFile
