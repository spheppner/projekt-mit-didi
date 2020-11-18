#!/usr/bin/python3
# requires svg.path, install it like this: pip3 install svg.path

# converts a list of path elements of a SVG file to simple line drawing commands
from svg.path import parse_path
from svg.path.path import Line
from xml.dom import minidom

# read the SVG file
doc = minidom.parse('test.svg')
path_strings = [path.getAttribute('d') for path
                in doc.getElementsByTagName('path')]
doc.unlink()

# print the line draw commands
for path_string in path_strings:
    path = parse_path(path_string)
    for e in path:
        if isinstance(e, Line):
            x0 = e.start.real
            y0 = e.start.imag
            x1 = e.end.real
            y1 = e.end.imag
            print("(%.2f, %.2f) - (%.2f, %.2f)" % (x0, y0, x1, y1))
