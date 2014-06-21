""" SoLoud Python wrapper generator """

import soloud_codegen

fo = open("soloud.py", "w")

#
#    from ctypes import *
#
#    soloud_dll = CDLL("soloud_x86")
#
#    myfunc = soloud_dll.myfunc
#    myfunc.argtypes = [c_char_p, c_int, c_double]
#    myfunc.restype = c_int
#

C_TO_PY_TYPES = {
    "int":"ctypes.c_int",
    "void":"None",
    "const char *":"ctypes.c_char_p",
    "unsigned int":"ctypes.c_uint",
    "float":"ctypes.c_float",
    "double":"ctypes.c_double",
    "float *":"ctypes.POINTER(ctypes.c_float * 256)",
    "unsigned char *":"ctypes.POINTER(ctypes.c_ubyte)"
}

for soloud_type in soloud_codegen.soloud_type:
    C_TO_PY_TYPES[soloud_type + " *"] = "ctypes.c_void_p"

def fudge_types(origtype):
    """ Map ctypes to parameter types """
    return C_TO_PY_TYPES[origtype]

def pythonize_camelcase(origstr):
    """ Turns camelCase into underscore_style """
    ret = ""
    for letter in origstr:
        if letter.isupper():
            ret += '_' + letter.lower()
        else:
            ret += letter
    # kludge, because calc_f_f_t is silly.
    ret = ret.replace("_f_f_t", "_fft")
    return ret

def has_ex_variant(funcname):
    """ Checks if this function has an "Ex" variant """    
    if funcname[-2::] == "Ex":
        # Already an Ex..
        return False
    for func in soloud_codegen.soloud_func:
        if func[1] == (funcname + "Ex"):
            return True
    return False

fo.write("# SoLoud wrapper for Python\n")
fo.write("# This file is autogenerated; any changes will be overwritten\n")

fo.write("\n")
fo.write('import ctypes\n')
fo.write('import sys\n')
fo.write('\n')
fo.write('try:\n')
fo.write('\tsoloud_dll = ctypes.CDLL("soloud_x86")\n')
fo.write('except:\n')
fo.write('\tprint "SoLoud dynamic link library (soloud_x86.dll on Windows) not found. Terminating."\n')
fo.write('\tsys.exit()')
fo.write("\n")

# Since there's no reason to use the "raw" data anymore,
# skip generating the enum dictionary
#
#fo.write("# Enumerations\n")
#fo.write("soloud_enum = {\n")
#first = True
#for x in soloud_codegen.soloud_enum:
#    if first:
#        first = False
#    else:
#        fo.write(",\n")
#    fo.write('"' + x + '": ' + str(soloud_codegen.soloud_enum[x]))
#fo.write("\n}\n")

fo.write("\n")
fo.write("# Raw DLL functions\n")
for x in soloud_codegen.soloud_func:
    fo.write(x[1] + ' = soloud_dll.' + x[1] + '\n')
    fo.write(x[1] + '.restype = ' + fudge_types(x[0]) + '\n')
    fo.write(x[1] + '.argtypes = [')
    first = True
    for y in x[2]:
        if len(y) > 0:
            if first:
                first = False
            else:
                fo.write(", ")
            fo.write(fudge_types(y[0]))
    fo.write(']\n')
    fo.write('\n')

#################################################################
#
# oop
#

#    class cname(object):
#        def __init__(self):
#            self.objhandle = cname_create()
#        def __enter__(self):
#            return self
#        def __exit__(self, eType, eValue, eTrace):
#            cname_destroy(self.objhandle)
#            return False
#        def close(self)
#            cname_destroy(self.objhandle)
#


fo.write('# OOP wrappers\n')

def fix_default_param(defparam, classname):
    """ 'fixes' default parameters from C to what python expectes """
    if (classname + '::') == defparam[0:len(classname)+2:]:
        return defparam[len(classname)+2::]
    if defparam[len(defparam)-1] == "f":
        return defparam[0:len(defparam)-1]
    return defparam

for x in soloud_codegen.soloud_type:
    first = True
    for y in soloud_codegen.soloud_func:
        if (x + "_") == y[1][0:len(x)+1:]:
            if first:
                fo.write('\n')
                fo.write('class %s(object):\n'%(x))
                for z in soloud_codegen.soloud_enum:
                    if z[0:len(x)+1] == x.upper()+'_':
                        s = str(soloud_codegen.soloud_enum[z])
                        fo.write('\t%s = %s\n'%(z[len(x)+1::], s))
                fo.write('\tdef __init__(self):\n')
                fo.write('\t\tself.objhandle = %s_create()\n'%(x))

                fo.write('\tdef __enter__(self):\n')
                fo.write('\t\treturn self\n')

                fo.write('\tdef __exit__(self, eType, eValue, eTrace):\n')
                fo.write('\t\t%s_destroy(self.objhandle)\n'%(x))
                fo.write('\t\tself.objhandle = ctypes.c_void_p(0)\n')
                fo.write('\t\treturn False\n')

                # Not sure which of the "destroy" funcs would be most suitable,
                # so let's generate three equally suitable options
                fo.write('\tdef close(self):\n')
                fo.write('\t\t%s_destroy(self.objhandle)\n'%(x))
                fo.write('\t\tself.objhandle = ctypes.c_void_p(0)\n')

                fo.write('\tdef destroy(self):\n')
                fo.write('\t\t%s_destroy(self.objhandle)\n'%(x))
                fo.write('\t\tself.objhandle = ctypes.c_void_p(0)\n')

                fo.write('\tdef quit(self):\n')
                fo.write('\t\t%s_destroy(self.objhandle)\n'%(x))
                fo.write('\t\tself.objhandle = ctypes.c_void_p(0)\n')
                first = False
            funcname = y[1][len(x)+1::]
            # If the function has the name "Ex", remove the subfix
            if funcname[-2::] == "Ex":
                funcname = funcname[:len(funcname)-2]
            # Skip generating functions that have an Ex variant            
            if funcname == "create" or funcname == "destroy" or has_ex_variant(y[1]):
                pass # omit create/destroy, handled by __exit__ / close
            else:
                fo.write('\tdef %s(self'%(pythonize_camelcase(funcname)))
                for z in y[2]:
                    if len(z) > 1:
                        if z[1] == 'a'+x:
                            pass # skip the 'self' pointer
                        else:
                            fo.write(', ' + z[1])
                            if len(z) > 2:
                                fo.write(' = ' + fix_default_param(z[2], x))
                fo.write('):\n')
                fo.write('\t\t')
                floatbufreturn = False
                if y[0] == 'void':
                    pass
                elif y[0] == 'float *':
                    floatbufreturn = True
                    fo.write('floatbuf = ')
                else:
                    fo.write('return ')
                fo.write(y[1] + '(self.objhandle')
                for z in y[2]:
                    if len(z) > 1:
                        if z[1] == 'a'+x:
                            pass # skip the 'self' pointer
                        else:
                            fo.write(', ')
                            fudged_type = fudge_types(z[0])
                            if fudged_type == 'ctypes.c_void_p':
                                fo.write(z[1] + '.objhandle')
                            else:
                                fo.write(fudged_type + '(' +  z[1] + ')')
                fo.write(')\n')
                if floatbufreturn:
                    fo.write('\t\treturn [f for f in floatbuf.contents]\n')



print "soloud.py generated"

fo.close()
