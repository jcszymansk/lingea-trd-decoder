#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Script for decoding Lingea Dictionary (.trd) file
# Result is <header>\t<definition> file, convertable easily
# by stardict-editor from package stardict-tools into native
# Stardict dictionary (stardict.sf.net and www.stardict.org)
# 
# Copyright (C) 2007 - Klokan Petr Přidal (www.klokan.cz)
#
# Based on script CobuildConv.rb by Nomad
# http://hp.vector.co.jp/authors/VA005784/cobuild/cobuildconv.html
#
# Version history:
# 0.6 (29.5.2008) Patch by Petr Dlouhy, added support for French-Czech and Spanish-Czech dictionaries; automatic encoding selection; all unrecognized characters are printed now as #something# (note: some of them are bugs in Lingea dictionaries); typo
# 0.5 (3.12.2007) Patch by Petr Dlouhy, iPaq and 2000 dicts support
#                 Patch by Josef Riha 
# 0.4 (30.10.2007) Patch by Petr Dlouhy, optional HTML generation
# 0.3 (28.10.2007) Patch by Petr Dlouhy, cleanup, bugfix. More dictionaries.
# 0.2 (19.7.2007) Changes, documentation, first 100% dictionary
# 0.1 (20.5.2006) Initial version based on Nomad specs
#
# Supported dictionaries:
# - Lingea Německý Kapesní slovník
# - Lingea Anglický Kapesní slovník
# - Lingea 2002 series (theoretically all of them)
# - Lingea 2000 series (theoretically all of them)
# - Lingea Pocket series
#
# Modified by:
# - Petr Dlouhy (petr.dlouhy | email.cz)
# Generalization of data block rules, sampleFlag 0x04, sound out fix, data phrase prefix with comment (0x04)
# HTML output, debugging patch, options on command line
# Decoding for 2000 and Pocket series.
#
# - Ing. Josef Riha ( jose1711 | gmail.com )
# Slovak letters support 
#
# <write your name here>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

# VERSION
VERSION = "0.6"

import getopt, sys
def usage():
   print "Lingea Dictionary Decoder"
   print "-------------------------"
   print "Version: %s" % VERSION
   print "Copyright (C) 2007 - Klokan Petr Pridal, Petr Dlouhy"
   print
   print "Usage: python lingea-trd-decoder.py DICTIONARY.trd > DICTIONARY.tab"
   print "Result conversion by stardict-tools: /usr/lib/stardict-tools/tabfile"
   print
   print "    -o <num>      --out-style        : Output style"
   print "                                          0   no tags"
   print "                                          1   \\n tags"
   print "                                          2   html tags"
   print "    -h            --help             : Print this message"
   print "    -d            --debug            : Debug"
   print "    -r            --debug-header     : Debug - print headers"
   print "    -a            --debug-all        : Debug - print all records"
   print "    -l            --debug-limit      : Debug limit"
   print
   print "For HTML support in StarDict dictionary .ifo has to contain:"
   print "sametypesequence=g"
   print "!!! Change the .ifo file after generation by tabfile !!!"
   print

try:
	opts, args = getopt.getopt(sys.argv[1:], "hdo:ral:e:", ["help", "debug", "out-style=", "debug-header", "debug-all", "debug-limit="])
except getopt.GetoptError:
   usage()
   print "ERROR: Bad option"
   sys.exit(2)
   
import locale
DEBUG = False
OUTSTYLE = 2
DEBUGHEADER = False
DEBUGALL = False
DEBUGLIMIT = 1
for o, a in opts:
   if o in ("-d", "-debug"):
      # DEBUGING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
      DEBUG = True
   if o in ("-o", "--out-style"):
      # output style
      OUTSTYLE = locale.atoi(a)
      if OUTSTYLE > 2:
         usage()
         print "ERROR: Output style not specified"
         sys.exit(2)
   if o in ("-r", "--debug-header"):
      # If DEBUG and DEBUGHEADER, then print just all header records
      DEBUGHEADER = True
   if o in ("-a", "--debug-all"):
      # If DEBUG and DEBUGALL then print debug info for all records
      DEBUGALL = True
   if o in ("-h", "--help"):
      usage()
      sys.exit(0)
   if o in ("-l", "--debug-limit"):
      # Number of wrong records for printing to stop during debugging 
      DEBUGLIMIT = locale.atoi(a)
# FILENAME is a first parameter on the command line now

if len(args) == 1:
    FILENAME = args[0]
else:
   usage()
   print "ERROR: You have to specify .trd file to decode"
   sys.exit(2)

from struct import *
import re


if OUTSTYLE == 0:
    tag = {
           'db':(''   ,''),    #Data beginning
           'rn':(''   ,'\t'),  #Record name
           'va':(''   ,' '),   #Header variant
           'wc':('('  ,')'),   #WordClass
           'pa':(''   ,' '),   #Header parts
           'fo':('('  ,') '),  #Header forms
           'on':('('  ,')' ),  #Header origin note
           'pr':('['  ,']'),   #Header pronunciation; not printed by Lingea
           'du':('('  ,')'),   #Data sub example
           'hs':('('  ,') '),  #Header source
           'dv':('{'  ,'} '),  #Header dataVariant
           'pv':('/'  ,'/ '),  #Header plural variant
           'ex':('('  ,') '),  #Header example
           'sa':('`'  ,'`' ),  #Data sample
           'sw':(''   ,''),    #Data sample wordclass; is no printed by Lingea (it is printed only in French?)
           'do':('`'  ,'`' ),  #Data origin note
           'df':(''   ,' '),   #Data definition
           'nt':(''   ,' '),   #Data note
           'ps':('"'  ,'" '),  #Data phrase short form
           'pg':('"'  ,' = '), #Data phrase green
           'pc':('`'  ,'`'),   #Data phrase comment; this comment is not printed by Lingea, but it seems useful
           'p1':('"'  ,' = '), #Data phrase 1
           'p2':(''   ,'" ' ), #Data phrase 2
           'sp':('"'  ,' = ' ),#Data simple phrase
           'b1':('"'  ,' = '), #Data phrase (block) 1
           'b2':('" ' ,''),    #Data phrase (block) 2
           }
if OUTSTYLE == 1:
    tag = {
           'db':('•'       ,''),      #Data beginning
           'rn':(''        ,'\t'),    #Record name
           'va':(''        ,' '),     #Header variant
           'wc':(''        ,'\\n'),   #WordClass
           'pa':(''        ,':\\n'),  #Header parts
           'fo':('('       ,') '),    #Header forms
           'on':('('       ,')\\n' ), #Header origin note
           'pr':('['       ,']\\n'),  #Header pronunciation; not printed by Lingea
           'du':('('       ,')'),     #Data sub example
           'hs':('('       ,')\\n'),  #Header source
           'dv':('{'       ,'} '),    #Header dataVariant
           'pv':('/'       ,'/\\n'),  #Header plural variant
           'ex':('('       ,')\\n'),    #Header example
           'sa':('    '    ,'\\n' ),  #Data sample
           'sw':(''        ,''),      #Data sample wordclass; is not printed by Lingea (it is printed in only in French?)
           'do':('    '    ,' ' ),    #Data origin note
           'df':('    '    ,'\\n'),   #Data definition
           'nt':('    '    ,'\\n'),   #Data note
           'ps':('    '    ,'\\n'),   #Data phrase short form
           'pg':('    '    ,' '),     #Data phrase green
           'pc':('    '    ,' '),     #Data phrase comment; this comment is not printed by Lingea, but it seems useful
           'p1':('    '    ,' '),     #Data phrase 1
           'p2':('      '  ,'\\n' ),  #Data phrase 2
           'sp':('    '    ,'\\n' ),  #Data simple phrase
           'b1':('"'       ,' = '),   #Data phrase (block) 1
           'b2':('" '      ,''),      #Data phrase (block) 2
          }
if OUTSTYLE == 2:
    tag = {
           'db':('•'                                                 ,''),              #Data beginning
           'rn':(''                                                  ,'\t'),            #Record name
           'va':(''                                                  ,' '),             #Header variant
           'wc':('<span size="larger" color="darkred" weight="bold">','</span>\\n'),    #WordClass
           'pa':('<span size="larger" color="darkred" weight="bold">',':</span>\\n'),   #Header parts
           'fo':('('                                                 ,') '),            #Header forms
           'on':('<span color="blue">('                              ,')</span>\\n' ),  #Header origin note
           'pr':('['                                                 ,']\\n'),          #Header pronunciation; not printed by Lingea
           'du':('('                                                 ,')'),             #Data sub example
           'hs':('('                                                 ,')\\n'),          #Header source
           'dv':('{'                                                 ,'} '),            #Header dataVariant
           'pv':('/'                                                 ,'/\\n'),          #Header plural variant
           'ex':('('                                                 ,')\\n'),          #Header example
           'sa':('    <span color="darkred" weight="bold">'          ,'</span>\\n' ),   #Data sample
           'sw':(''                                                  ,''),              #Data sample wordclass; is not printed by Lingea (it is printed in only in French?)
           'do':('    <span color="darkred" weight="bold">'          ,'</span> ' ),     #Data origin note
           'df':('    <span weight="bold">'                          ,'</span>\\n'),    #Data definition
           'nt':(''                                                  ,''),              #Data note
           'ps':('    <span color="dimgray" weight="bold">'          ,'</span>\\n'),    #Data phrase short form
           'pg':('    <span color="darkgreen" style="italic">'       ,'</span> '),      #Data phrase green
           'pc':('    <span color="darkgreen" style="italic">'       ,'</span> '),      #Data phrase comment; this comment is not printed by Lingea, but it seems useful
           'p1':('    <span color="dimgray" style="italic">'         ,'</span> '),      #Data phrase 1
           'p2':('      '                                            ,'\\n' ),          #Data phrase 2
           'sp':('    <span color="cyan">'                           ,'</span>\\n' ),   #Data simple phrase
           'b1':('"'                                                 ,' = '),           #Data phrase (block) 1
           'b2':('" '                                                ,''),              #Data phrase (block) 2
          }



# Print color debug functions
purple = lambda c: '\x1b[1;35m'+c+'\x1b[0m'
blue = lambda c: '\x1b[1;34m'+c+'\x1b[0m'
cyan = lambda c: '\x1b[36m'+c+'\x1b[0m'
gray = lambda c: '\x1b[1m'+c+'\x1b[0m'

def getRec(n):
    """Get data stream for record of given number"""
    if n >= 0 and n < entryCount:
        f.seek(index[n])
        return f.read(index[n+1] - index[n])
    else:
        return ''

def decode_alpha( stream, nullstop=True):
    """Decode 6-bit encoding data stream from the beginning until first NULL"""
    offset = 0
    triple = 0
    result = []
    while triple < len( stream ):
        if offset % 4 == 0:
            c = stream[triple] >> 2
            triple += 1
        if offset % 4 == 1:
            c = (stream[triple-1] & 3) << 4 | stream[triple] >> 4
            triple += 1
        if offset % 4 == 2:
            c = (stream[triple-1] & 15) << 2 | (stream[triple] & 192) >> 6
            triple += 1
        if offset % 4 == 3:
            c = stream[triple-1] & 63
        if c == 0 and nullstop:
            break
        offset += 1
        # TODO: ENCODE UNICODE 4 BYTE STREAM!!! and but it after #UNICODE# as unichr()
        result.append(c)
    return decode_alpha_postprocessing(result), triple - 1


def decode_alpha_postprocessing( input ):
    """Lowlevel alphabet decoding postprocessing, combines tuples into one character"""
    result = ""
    input.extend([0x00]*5)

    # UPCASE, UPCASE_PRON, SYMBOL, SPECIAL
    skip = False
    for i in range(0,len(input)-1):
        if skip > 0:
            skip -= 1
            continue

        bc = input[i]
        c = alpha[bc]
        bc1 = input[i+1]
        c1 = alpha[bc1]
        if c[0] == '#':
           skip = 1
           if c in subs:
              if c in ("#UPCASE#", "#SPECIAL#", "#SYMBOL#"):
                 result += subs[c][bc1]
              elif c in ("#PRON#"):
                 bc2 = input[i+2]
                 c2 = alpha[bc2]
                 cc = c1 + c2
                 if cc in subs[c]:
                    result += subs[c][cc]
                 else:
                    result += c + cc # debug
                 skip = 2
              elif c1 in subs[c]:
                 result += subs[c][c1]
              else:
                 result += c + c1 # debug
           else:
              result += c # debug
        else:
           result += c

    return result

def pronunciation_encode(s):
    """Encode pronunciation upcase symbols into IPA symbols"""
    for i in range(0, 64):
        s = s.replace(upcase[i], upcase_pron[i])
    return s

re_a = re.compile(r'<a(.*?)>') 
re_c = re.compile(r'<c(.*?)>')
re_d = re.compile(r'<d(.*?)>')
re_e = re.compile(r'<e(.*?)>')
re_E = re.compile(r'<E(.*?)>')
re_f = re.compile(r'<f(.*?)>')
re_g = re.compile(r'<g(.*?)>') #language
re_h = re.compile(r'<h(.*?)>')
re_i = re.compile(r'<i(.*?)>') 
re_I = re.compile(r'<I(.*?)>') 
re_l = re.compile(r'<l(.*?)>') 
re_L = re.compile(r'<L(.*?)>') 
re_n = re.compile(r'<n(.*?)>') 
re_N = re.compile(r'<N(.*?)>') 
re_o = re.compile(r'<o(.*?)>') 
re_p = re.compile(r'<p(.*?)>') 
re_q = re.compile(r'<q(.*?)>') 
re_r = re.compile(r'<r(.*?)>') 
re_t = re.compile(r'<t(.*?)>') 
re_u = re.compile(r'<u(.*?)>') 
re_v = re.compile(r'<v(.*?)>') 
re_w = re.compile(r'<w(.*?)>')
re_x = re.compile(r'<x(.*?)>')
re_y = re.compile(r'<y(.*?)>')
re_z = re.compile(r'<z(.*?)>')
re__ = re.compile(r'<\^(.*?)>')

def decode_tag_postprocessing(input):
    """Decode and replace tags used in Lingea dictionaries; decode internal tags"""
    s = input

    # General information in http://www.david-zbiral.cz/El-slovniky-plnaverze.htm#_Toc151656799
    # TODO: Better output handling

    if (OUTSTYLE == 0) or (OUTSTYLE == 1):
        s = re_a.sub(r'(\1)',s)
        s = re_c.sub(r'(\1)',s)
        s = re_d.sub(r'(\1)',s)
        s = re_e.sub(r'(\1)',s)
        s = re_E.sub(r'(\1)',s)
        s = re_f.sub(r'(\1)',s)
        s = re_g.sub(r'(\1)',s)
        s = re_h.sub(r'(\1)',s)
        s = re_i.sub(r'(\1)',s)
        s = re_I.sub(r'(\1)',s)
        s = re_l.sub(r'(\1)',s)
        s = re_L.sub(r'(\1)',s)
        s = re_n.sub(r'(\1)',s)
        s = re_N.sub(r'(\1)',s)
        s = re_o.sub(r'(\1)',s)
        s = re_p.sub(r'(\1)',s)
        s = re_q.sub(r'(\1)',s)
        s = re_r.sub(r'(\1)',s)
        s = re_t.sub(r'(\1)',s)
        s = re_u.sub(r'(\1)',s)
        s = re_v.sub(r'(\1)',s)
        s = re_w.sub(r'(\1)',s)
        s = re_x.sub(r'(\1)',s)
        s = re_y.sub(r'(\1)',s)
        s = re_z.sub(r'(\1)',s)
        s = re__.sub(r'(\1)',s)
    if OUTSTYLE == 2:
        s = re_a.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_c.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_d.sub(r'<span size="small" color="blue">(\1)</span>',s)
        s = re_e.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_E.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_f.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_g.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_h.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_i.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_I.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_l.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_L.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_n.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_N.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_o.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_p.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_q.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_r.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_t.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_u.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_v.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_w.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_x.sub(r'<span size="small" color="brown" style="italic">\1</span>',s)
        s = re_y.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re_z.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)
        s = re__.sub(r'<span size="small" color="blue" style="italic">\1</span>',s)

    return s

def toBin( b ):
    """Prettify debug output format: hex(bin)dec"""
    original = b
    r = 0;
    i = 1;
    while b > 0:
        if b & 0x01 != 0: r += i
        i *= 10
        b = b >> 1
    return "0x%02X(%08d)%03d" % (original, r, original)


def outInt( comment = "" ):
    """Read next byte and output DEBUG info"""
    global bs, pos

    if DEBUG: print "%03d %s %s | %03d" % (pos, toBin(bs[pos]),comment, pos)
    if (comment.find('%') != -1):
         comment = comment % bs[pos]
    pos += 1
    return bs[pos-1]

def outStr( comment = "" ):
    """Read next string and output DEBUG info"""
    global bs, pos

    s, triple  = decode_alpha(bs[pos:])
    s = s.split('\x00')[0] # give me string until first NULL
    if (comment.find('%') != -1):
        comment = comment % s
    if DEBUG: print "%03d %s %s | %s" % (pos, toBin(bs[pos]),comment, s)
    pos += triple + 1
    return s.replace('`','') # Remove '`' character from words

def decode(stream):
    """Decode byte stream of one record, return decoded string with formatting in utf"""
    result = ""
    global bs, pos
    # stream - data byte stream for one record
    bs = unpack("<%sB" % len(stream), stream)
    # bs - list of bytes from stream

    pos = 0
    itemCount = outInt("ItemCount: %s") # Number of blocks in the record
    mainFlag = outInt("MainFlag: %s")

    # HEADER BLOCK
    # ------------
    if mainFlag & 0x01:
        headerFlag = outInt("HeaderFlag: %s") # Blocks in header
        if headerFlag & 0x01:
            result += tag['rn'][0] + outStr("Header record name: %s").replace('_','') + tag['rn'][1]  # Remove character '_' from index
        if headerFlag & 0x02:
            result += tag['va'][0] + outStr("Header variant: %s") + tag['va'][1]
        if headerFlag & 0x04:
            s = outInt("Header wordclass: %s")
            if s < 32:
                result += tag['wc'][0] + wordclass[s] + tag['wc'][1]
            else:
                raise "Header wordclass out of range in: %s" % result
        if headerFlag & 0x08:
            result += tag['pa'][0] + outStr("Header parts: %s") + tag['pa'][1]
        if headerFlag & 0x10:
            result += tag['fo'][0] + outStr("Header forms: %s") + tag['fo'][1]
        if headerFlag & 0x20:
            result += tag['on'][0] + outStr("Header origin note: %s") +  tag['on'][1]
        if headerFlag & 0x80:
            result += tag['pr'][0] + pronunciation_encode(outStr("Header pronunciation: %s")) + tag['pr'][1]
    
    # Header data block
    if mainFlag & 0x02:
        headerFlag = outInt("Header dataFlag: %s") # Blocks in header
        if headerFlag & 0x01:
            result += tag['hs'][0] + outStr("Header source: %s")+ tag['hs'][1]
        if headerFlag & 0x02:
            result += tag['dv'][0] + outStr("Header dataVariant: %s")+ tag['dv'][1]
        if headerFlag & 0x08:
            result += tag['ex'][0] + outStr("Example: %s") + tag['ex'][1]
        if headerFlag & 0x40:
            result += tag['pv'][0] + outStr("Plural variant: %s") + tag['pv'][1] #???????????????

    # ??? Link elsewhere
    pass

    # SOUND DATA REFERENCE
    if mainFlag & 0x80:
       outInt("Sound reference byte #1: %s")
       outInt("Sound reference byte #2: %s")
       outInt("Sound reference byte #3: %s")
       outInt("Sound reference byte #4: %s")
       if outInt("Sound reference continue: %s") & 0x80:
          outInt("Sound reference byte #5: %s")
          outInt("Sound reference byte #6: %s")
          outInt("Sound reference byte #7: %s")
          outInt("Sound reference byte #8: %s")

    # TODO: Test all mainFlags in header!!!!

    #result += ': '
    li = 0
 
    #print just every first word class identifier
    # TODO: this is not systematic (should be handled by output)
    global lastWordClass
    lastWordClass = 0

    # DATA BLOCK(S)
    # -------------
    for i in range(0, itemCount):
        item = tag['db'][0] + tag['db'][1]
        ol = False
        dataFlag = outInt("DataFlag: %s -----------------------------")
        if dataFlag & 0x01: # small index
            sampleFlag = outInt("Data sampleFlag: %s")
            if sampleFlag & 0x01:
                result += tag['sa'][0] + outStr("Data sample: %s") +  tag['sa'][1]
            if sampleFlag & 0x02:
                result += tag['sa'][0] + outStr("Data sample variant: %s") +  tag['sa'][1]
            if sampleFlag & 0x04:
               s = outInt("Data wordclass: %s")
               if s != lastWordClass: 
                  if s < 32:
                      result += tag['wc'][0] + wordclass[s] + tag['wc'][1]
                  else:
                      raise "Header wordclass out of range in: %s" % result
               lastWordClass = s
            if sampleFlag & 0x08:
                result += tag['sw'][0] + outStr("Data sample wordclass: %s") + tag['sw'][1]
            if sampleFlag & 0x10:
                outInt("Data sample Int: %s")
                outInt("Data sample Int: %s")
                outInt("Data sample Int: %s")
            if sampleFlag & 0x20:
                item += tag['do'][0] + outStr("Data origin note: %s") + tag['do'][1]
            if sampleFlag & 0x80:
                item += "    "
                result += tag['pr'][0] + pronunciation_encode(outStr("Data sample pronunciation: %s")) + tag['pr'][1]
        if dataFlag & 0x02:
            item += "    "
            subFlag = outInt("Data subFlag: %s")
            if subFlag & 0x08:
                item += tag['du'][0] + outStr("Data sub example: %s") + tag['du'][1]
            if subFlag & 0x80:
                outStr("Data sub prefix: %s")
                # It seams that data sub prefix content is ignored and there is a generated number for the whole block instead.
                li += 1
                ol = True
        if dataFlag & 0x04: # chart
            pass # ???
        if dataFlag & 0x08: # reference
            item += tag['df'][0] + outStr("Data definition: %s") + tag['df'][1]
        if dataFlag & 0x10: # note???
            noteFlag = outInt("Data noteFlag: %s");
            if noteFlag & 0x08:
                outInt("Data note ???: %s");
            item += tag['nt'][0] + outStr("Data note: %s") + tag['nt'][1]
        if dataFlag & 0x20: # phrase
            phraseFlag1 = outInt("Data phraseFlag1: %s")
            if phraseFlag1 & 0x01:
                item += tag['ps'][0] + outStr("Data phrase short form: %s") + tag['ps'][1]
            if phraseFlag1 & 0x02:
                phraseCount = outInt("Data phraseCount: %s")
                for i in range(0, phraseCount):
                    phraseComment = outInt("Data phrase prefix")
                    if phraseComment & 0x04:
                       item += tag['pc'][0] + outStr("Data phrase comment: %s")  + tag['pc'][1]
                    item += tag['p1'][0] + outStr("Data phrase 1: %s") + tag['p1'][1]
                    item += tag['p2'][0] + outStr("Data phrase 2: %s") + tag['p2'][1]
            if phraseFlag1 & 0x04:
                phraseCount = outInt("Data phraseCount: %s")
                for i in range(0, phraseCount):
                    phraseComment = outInt("Data phrase prefix")
                    if phraseComment & 0x04:
                       item += tag['pc'][0] + outStr("Data phrase 1: %s")  + tag['pc'][1]
                    item += tag['pg'][0] + outStr("Data phrase comment: %s")  + tag['pg'][1]
                    item += tag['p2'][0] + outStr("Data phrase 2: %s") +  tag['p2'][1]
            if phraseFlag1 & 0x08:
                phraseCount = outInt("Data simple phraseCount: %s")
                for i in range(0, phraseCount):
                    item += tag['sp'][0] + outStr("Data simple phrase: %s") +  tag['sp'][1]
            if phraseFlag1 & 0x10:
                item += tag['ps'][0] + outStr("Data phrase short form: %s") + tag['ps'][1]
            if phraseFlag1 & 0x40:
                item += tag['ps'][0] + outStr("Data phrase short form: %s") + tag['ps'][1]


            # TODO: be careful in changing the rules, to have back compatibility! 
        if dataFlag & 0x40: # reference, related language
            #0x01 synonym ?
            #0x02 antonym ?
            pass
        if dataFlag & 0x80: # Phrase block
            flags = [
            out("Data phrase block: %s"),
            out("Data phrase block: %s"),
            out("Data phrase block: %s"),
            out("Data phrase block: %s"),
            out("Data phrase block: %s"),
            out("Data phrase block: %s"),
            out("Data phrase block: %s"),
            out("Data phrase block: %s")]
            if flags == [0x80,0x80,0xF9,0xDF,0x9D,0x00,0x0B,0x01]:
                result += "\\nphr: "
                li = 1
                ol = True
                item += tag['b1'][0]+outStr("Data phrase 1: %s") + tag['b1'][1]
                out("Data phrase block: %s")
                out("Data phrase block: %s")
                out("Data phrase block: %s")
                out("Data phrase block: %s")
                item += tag['ds'][0] + outStr("Data phrase 2: %s") + tag['ds'][1]
            if flags == [0x80,0x80,0xF9,0xDF,0x9D,0x00,0x23,0x01]:
                result += "\\nphr: "
                li = 1
                ol = True
                item += tag['b1'][0]+outStr("Data phrase 1: %s") + tag['b1'][1]
                out("Data phrase block: %s")
                out("Data phrase block: %s")
                out("Data phrase block: %s")
                out("Data phrase block: %s")
                out("Data phrase block: %s")
                item += tag['ds'][0] + outStr("Data phrase 2: %s") + tag['ds'][1]
        if ol:
            result += "\\n%d. %s" % (li, item)
        else:
            result += item

    ok = True
    while pos < len(stream):
        ok = (outInt() == 0x00) and ok

    if ok:
        result += '\n'

    return decode_tag_postprocessing(result)

################################################################
# MAIN
################################################################


f = open(FILENAME,'rb')

# DECODE HEADER OF FILE

copyright = unpack("<64s",f.read(64))[0]
a = unpack("<16L",f.read(64))

entryCount = a[4]
indexBaseCount = a[6]
indexOffsetCount = a[7]
pos1 = a[8]
indexPos = a[9]
bodyPos = a[10]
smallIndex = (a[3] == 2052)

################################################################
# TRANSLATION TABLES
################################################################

if smallIndex: # TODO: smallIndex might not correspond with encoding
   alpha = ['\x00', 'a','b','c','d','e','f','g','h','i',
       'j','k','l','m','n','o','p','q','r','s',
       't','u','v','w','x','y','z','á','ä','č',
       'ď','é', 'ě', 'í', '#AL34#', '#AL35#', 'ň', 'ó', 'ö', '#AL39#',
       'ř', 'š', 'ť', 'ú', 'ů', 'ü', 'ý', 'ž', 'ß', ' ',
       '.', ',', '-', '\'', '(', ')', '`', '"', '#AL58#', '#AL59#',
       '#UPCASE#', 'à', '#SPECIAL#', "#AL1234213"] # 4 bytes after unicode

   upcase = ['\x00', 'A','B','C','D','E','F','G','H','I',
       'J','K','L','M','N','O','P','Q','R','S',
       'T','U','V','W','X','Y','Z','Á','Ä','Č',
       'Ď','É', 'Ě', 'Í', '<', '>', 'Ň', 'Ó', '-', '#UP39#',
       'Ř', 'Š', 'Ť', 'Ú', 'Ů', 'Ü', 'Ý', 'Ž', '#UP48#', ' ',
       '#UP.#', '#UP,#', '#UP-#', '#UP\'#', '#UP(#', '#UP)#', '#UP`#', '#UP"#', '#UP58#', '#UP59#',
       '#~UPCASE#', 'À', '#UP/#'] # 4 bytes after unicode
else:
   alpha = ['\x00', 'a','b','c','d','e','f','g','h','i',
       'j','k','l','m','n','o','p','q','r','s',
       't','u','v','w','x','y','z','#AL27#','#AL28#','#AL29#',
       '#AL30#','#AL31#', ' ', '.', '<', '>', ',', ';', '-', '#AL39#',
       '#GRAVE#', '#ACUTE#', '#CIRC#', '#TILDE#', '#UML#', '#AL45#', '#DACUT#', '#CARON#', '#BREVE#', '#CEDIL#',
       '#STROKE#', '#SHARP#', 'β', '#AL53#', '#AL54#', '#AL55#', '#AL56#', '#AL57#', 's', '#SYMBOL#', # symbol 58 is used in Spanish word pillo as s (seimpre)
       '#PRON#', '#UPCASE#', '#SPECIAL#', '#UNICODE#'] # 4 bytes after unicode

   upcase = ['#UP0#','#UP1#','#UP2#','#UP3#','#UP4#','#UP5#','#UP6#','#UP7#','#UP8#','#UP9#',
       '#UP10#','#UP11#','#UP12#','#UP13#','#UP14#','#UP15#','#UP16#','#UP17#','#UP18#','#UP19#',
       '#UP20#','#UP21#','#UP22#','#UP23#','#UP24#','#UP25#','#UP26#','#UP27#','#UP28#','#UP29#',
       '#UP30#','#UP31#','A','B','C','D','E','F','G','H',
       'I','J','K','L','M','N','O','P','Q','R',
       'S','T','U','V','W','X','Y','Z','#UP58#','#UP59#',
       '#UP60#','#UP61#','#UP62#','#UP63#']

upcase_pron = ['#upr0#', '#upr1#','#upr2#','#upr3#','#upr4#','#upr5#','#upr6#','#upr7#','#upr8#','#upr9#',
    '#upr10#', '#upr11#','#upr12#','#upr13#','#upr14#','#upr15#','#upr16#','#upr17#','#upr18#','#upr19#',
    '#upr20#', '#upr21#','#upr22#','#upr23#','#upr24#','#upr25#','#upr26#','#upr27#','#upr28#','#upr29#',
    '#upr30#', '#upr31#','ɑ','#upr33#','ʧ','ð','ə','ɜ','#upr38#','æ',
    'ɪ', 'ɭ','#upr42#','ŋ','#upr44#','ɳ','ɔ','#upr47#','ɒ','ɽ',
    'ʃ', 'θ','ʊ','ʌ','#pr54#','#upr55#','#upr56#','ʒ','#upr58#','#upr59#',
    '#upr60#', '#upr61#','#upr62#','#upr63#']

symbol = ['#SY0#', '#SY1#','„','…','§','#SY5#','#SY6#','#SY7#','‘','’',
    '“', '”','#SY12#','—','#SY14#','™','#SY16#','¡','¢','£',
    '¤', '#SY21#','#SY22#','§','©','#SY25#','#SY26#','#SY27#','®','°',
    '#SY30#', '²','³','#SY33#','#SY34#','#SY35#','¹','#SY37#','#SY38#','#SY39#',
    '½', '#SY41#','¿','×','÷','#SY45#','#SY46#','#SY47#','#SY48#','#SY49#',
    '#SY50#', '#SY51#','#SY52#','#SY53#','#SY54#','#SY55#','#SY56#','#SY57#','#SY58#','#SY59#',
    '#SY60#', '#SY61#','#SY62#','#SY63#']

special = ['#SP0#', '!','"','#','$','%','&','\'','(',')',
    '*', '+','#SP12#','#SP13#','#SP14#','/','0','1','2','3',
    '4', '5','6','7','8','9',':',';','<','=',
    '>', '?','@','[','\\',']','^','_','`','{',
    '|', '}','~','#SP43#','#SP44#','#SP45#','#SP46#','#SP47#','#SP48#','#SP49#',
    '#SP50#', '#SP51#','#SP52#','#SP53#','#SP54#','#SP55#','#SP56#','#SP57#','#SP58#','#SP59#',
    '#SP60#', '#SP61#','#SP62#','#SP63#']

wordclass = ('subs:','n:','adj:','pron:','num:','v:','adv:','prep:','conj:','part:',
    'intr:','phr:','#WC12#','#WC13#','#WC14#','#WC15#','#WC16#','#WC17#','#WC18#','#WC19#',
    'm/f:','m:','f:','#WC23#','#WC24#','#WC25#','#WC26#','#WC27#','#WC28#','#WC29#',
    '#WC30#','#WC31#')


subs = {
       "#GRAVE#" : {
          'a': 'à',
          'e': 'è',
          'u': 'û'
          # '#SPECIAL#': '?' # what the hell is this one
          # 'q': '?', # what the hell is this one
          # 's': '?', # what the hell is this one
       },
       "#UML#" : {
           'o': 'ö',
           'u': 'ü',
           'a': 'ä',
           'e': 'ë',
           'i': 'ï',
           ' ': 'Ä',
           '#DACUT#': 'Ö',
           'β': 'Ü'
       },
       "#ACUTE#" : {
           'a': 'á',
           'e': 'é',
           'i': 'í',
           'n': 'ń',
           'o': 'ó',
           'u': 'ú',
           'l': 'ĺ',
           'r': 'ŕ',
           'y': 'ý',
           ' ': 'Á',
           ',': 'É',
           '#DACUT#':'Ó',
           '#AL56#': 'Ý',
           '#GRAVE#':'Í',
           '#CEDIL#': 'Ŕ',
           'β':'Ú',
           '<':'Ć'
       },
       "#CARON#" : {
           'r': 'ř',
           'c': 'č',
           's': 'š',
           'z': 'ž',
           'e': 'ě',
           'd': 'ď',
           't': 'ť',
           'a': 'å',
           'u': 'ů',
           'n': 'ň',
           'l': 'ľ',
           '<': 'Č',
           '>': 'Ď',
           '#STROKE#': 'Š',
           ' ': 'Å',
           ',': 'Ě',
           'β': 'Ů',
           '#TILDE#': 'Ľ',
           '#CEDIL#': 'Ř',
           '#SHARP#': 'Ť',
           '#AL45#': 'Ň',
           '#AL57#': 'Ž'
       },
       "#SHARP#": {
           's': 'ß',
           'o': 'œ',
           'a': 'æ',
           '#DACUT#': 'Œ'
       },
        "#TILDE#": {
           'n': 'ñ',
           'o': 'õ',
           'a': 'ã',
           'i': 'ĩ'
           # 'e': '?' # what the hell is this one
           # '#SYMBOL#': '?' # what the hell is this one
       },
       "#CIRC#": {
           'a': 'â',
           'e': 'ê',
           'o': 'ô',
           'i': 'î',
           'u': 'û',
           ' ': 'Â',
           ',': 'Ê', # used in french word survętement, but not decoded by Lingea
           '#GRAVE#': 'Î', # used in french île, but not decoded by Lingea
           '#DACUT#': 'Ô'
       },
       "#CEDIL#": {
           'c': 'ç',
           'e': 'ę',
           'a': 'ą',
           'k': 'ķ',
           'i': 'ļ',
           'n': 'ņ',
           '<': 'Ç'
           # 'j': '?' # what the hell is this one
           # '#UML#': '?' # what the hell is this one (used in word Jesús)
       },
       "#DACUT#": {
           'u': 'ű',
           'z': 'ż',
       },
       "#STROKE#": {
           'l': 'ł',
       },
       "#BREVE#": {
           'a': 'ă',
       },
       "#PRON#": {
           'el': 'ɛ',
           'ou': 'ɶ',
           'or': 'ɸ',
           '#CEDIL#c': 'ʀ',
           'hi': 'ɥ',
           'nh': 'ɲ',
           'ex': 'ɛ̃', 
           'cv': 'ɔ̃',
           'ov': 'œ̃',
           'av': 'ɑ̃'
       },
       "#UPCASE#": upcase,
       "#SYMBOL#": symbol,
       "#SPECIAL#": special,
     }

# DECODE INDEX STRUCTURE OF FILE

index = []
f.seek(indexPos)
bases = unpack("<%sL" % indexBaseCount, f.read(indexBaseCount * 4))
if smallIndex: # In small dictionaries every base is used 4-times
    bases4 = []
    for i in bases:
        bases4.extend([i,i,i,i])
    bases = bases4
for b in bases:
    offsets = unpack("<64H", f.read(64*2))
    for o in offsets:
        if len(index) < indexOffsetCount:
            #print "Index %s: %s + %s + %s * 4 = %s" % (len(index), bodyPos, b, o, toBin(bodyPos + b + o * 4))
            index.append(bodyPos + b + o * 4)

# DECODE RECORDS

if DEBUG:
    # PRINTOUT DEBUG OF FIRST <DEBUGLIMIT> WRONG RECORDS:
    for i in range(1,entryCount):
        if not DEBUGALL:
            DEBUG = False
        s = decode(getRec(i))
        if DEBUGHEADER:
            # print s.split('\t')[0]
            print s
        if DEBUGLIMIT > 0 and not s.endswith('\n'):
            DEBUG = True
            print "-"*80
            print "%s) at address %s" % (i, toBin(index[i]))
            print
            s = decode(getRec(i))
            print s
            DEBUGLIMIT -= 1
    DEBUG = True
else:
    # DECODE EACH RECORD AND PRINT IT IN FORMAT FOR stardict-editor <term>\t<definition>
    for i in range(1,entryCount):
        s = decode(getRec(i))
        if s.endswith('\n'):
            print s,
        else:
            print s
            print "!!! RECORD STRUCTURE DECODING ERROR !!!"
            print "Please run this script in DEBUG mode and repair DATA BLOCK(S) section in function decode()"
            print "If you succeed with whole dictionary send report (name of the dictionary and source code of script) to slovniky@googlegroups.com"
            break
