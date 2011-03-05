#!/usr/bin/env python

#  expand-terrain-macros.py - Expand "meta-macros" for terrain WML
#
#  Copyright (C) 2008 - 2009 by Moritz Goebelbecker
#  Part of the Battle for Wesnoth Project http://www.wesnoth.org
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 2
#  or at your option any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY.
#
#  See the COPYING file for more details.
# 


#
#  Meta-Macro syntax:
#  #meta-macro BASENAME [{NORMAL_PARAM, OPTIONAL_PARAM} [...]]
#
#  NORMAL_PARAM: Macro parameter that will be passed unmodified to the base
#  macro
#  OPTIONAL_PARAM: Macro parameter that will sometimes be passed to the base 
#  macro and sometimes be replaced with a default value. The script will
#  create one macro for each possible combination of optional parameters
#
#  Syntax:         ABBREV=NAME=DEFAULT
#    ABBREV:       One letter that is appended to macros taking that argument
#    NAME:         Name of the parameter that is used when it's passed to the
#                  base macro
#    ABBREV:       Default value that is used when the parameter is not passed
#                  to the base macro
#
#
#  !!! ONLY USE THIS IF YOU KNOW WHAT YOU ARE DOING !!!

import sys
import getopt

def printUsage():
    print "Usage: expand-terrain-macros.py [OPTIONS] filename1\
 [filename2 [...]]\n"
    print """Options:
  -i  Insert the expanded sections into the input file(s) immediately after
      their macro definitions.
  -a  Append the expanded sections to the input file(s)
  -r  Replace the input file(s) with the resulting output. Previously generated
      expansions will be removed. Implies -i if nothing else is specified.

If no options are specified, only the expanded sections will be printed to 
stdout"""

insert = False
append = False
replace = False

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'iar')
except getopt.GetoptError, e:
    print 'Error parsing command-line arguments: %s' % e
    printUsage()
    sys.exit(1)
for (option, parameter) in opts:
    if option == '-i':
        insert = True
    if option == '-a':
        append = True
    if option == '-r':
        replace = True

if replace and not append:
    insert = True

if insert and append:
    print "Error: cannot use -i and -a at the same time"
    printUsage()
    sys.exit(1)
    

if len(args) == 0:
    printUsage()
    sys.exit(1)

for filename in args:
    f = file(filename)
    content = f.readlines()
    f.close()

    changed = False
    output = []
    appended = []
    
    autogenerated = False
    for line in content:
        if line.strip() == "#The following code is autogenerated\
 by expand-terrain-macros.py":
            autogenerated = True

        if (insert or append)  and not autogenerated:
            output.append(line.rstrip("\n"))

        if line.strip() == "#end of generated code":
            autogenerated = False

        if line.startswith('#meta-macro'):
            elems = line[12:].strip().split()
            basename = elems[0]
            params = []
            optional_params = []
            
            for param in elems[1:]:
                split_param = param.split('=')
                if len(split_param) == 3:
                    optional_params.append(split_param[0])
                elif len(split_param) != 1:
                    print "Error in line:\n" + line
                    sys.exit(1)
                    
                params.append(split_param)

            base_macro_suffix = "_" + "".join(optional_params)

            result = []
            result.append("#The following code is autogenerated\
 by expand-terrain-macros.py")
            if append:
                result.append("#generated from: " + line.strip())
            result.append("#Please do not modify")
            
            for i in range(2**len(optional_params) - 2, -1, -1):
                enabled_map = dict([(param, i & (1<<index) != 0) for index, param in enumerate(optional_params)])

                suffix = ""
                params_external = []
                params_internal = []

                for param in params:
                    #normal parameter
                    if len(param) == 1:
                        params_external.append(param[0])
                        params_internal.append('({'+param[0]+'})')
                    else:
                        #enabled optional parameter
                        if enabled_map[param[0]]:
                            suffix += param[0]
                            params_external.append(param[1])
                            params_internal.append('({'+param[1]+'})')
                        else:
                            params_internal.append(param[2])

                if len(suffix) > 0:
                    suffix = "_"+suffix
                            
                result.append("#define " + basename + suffix + " " + " ".join(params_external))
                result.append("    {" + basename + base_macro_suffix + " "  + " ".join(params_internal) + "}")
                result.append("#enddef")
                
            result.append("#end of generated code")
            changed = True

            if insert:
                output += result
            elif append:
                appended += result
            else:
                for r in result:
                    print r

    if (insert or append) and not replace:
        for line in output:
            print line
        if append:
            for line in appended:
                print line
                
    elif replace and changed:
        f = open(filename, 'w')
        for line in output:
            f.write(line+"\n")
        if append:
            for line in appended:
                f.write(line+"\n")
        f.close()
