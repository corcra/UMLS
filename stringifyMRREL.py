#!/usr/bin/python
# Take the strings from MRCONSO and apply them to MRREL.

import re
import sys

for line in open('UMLSpaths.txt','r'):
    if '#' in line:
        continue
    if 'outfile_path' in line:
        outfile_path = line.split()[1]
    if 'MRREL_path' in line:
        MRREL_path = line.split()[1]
    if 'MRCONSO_path' in line:
        MRCONSO_path = line.split()[1]

outfile = open(outfile_path,'w')
MRREL_file = open(MRREL_path,'r')
MRCONSO_file = open(MRCONSO_path,'r')

print 'Creating dictionary of AUIs from',MRREL_path
# dictionary of AUIs... empty
AUIs=dict()
pairs=MRREL_file.readlines()
missing_AUI=0
for pair in pairs:
    splitline = pair.split('|')
    AUI1 = splitline[1]
    AUI2 = splitline[5]
    AUIs[AUI1] = ''
    AUIs[AUI2] = ''
MRREL_file.close()

print 'Populating AUIs with strings from',MRCONSO_path
# populate AUIs with their strings
i=0
for line in MRCONSO_file:
    if i%250000==0:
        sys.stdout.write('\r'+str(i))
        sys.stdout.flush()
    i+=1
    splitline = line.split('|')
    AUI = splitline[7]
    CUI = splitline[0]
    if AUI in AUIs:
        string = splitline[14]
#        cuiline = CUI+'\t'+AUI+'\t'+re.sub(' ','_',string)+'\n'
#        CUI_words.write(cuiline)
        if AUIs[AUI]=='':
            AUIs[AUI] = (CUI,string)
        else:
            print 'We already learned this AUI apparently!', AUIs[AUI]
            print 'Trying to relearn it as',(CUI,string)

print ''

print 'Reassigning pairs with values and saving to',outfile_path
# now go back over and reassign pairs with their values
for pair in pairs:
    splitpair = pair.split('|')
    AUI1 = splitpair[1]
    AUI2 = splitpair[5]
    RELA = splitpair[7]
    if len(RELA)>0:
        try:
            AUI1_string = AUIs[AUI1][1]
            AUI2_string = AUIs[AUI2][1]
            outline = splitpair[0]+':'+re.sub(' ','_',AUI1_string)+'\t'+splitpair[4]+':'+re.sub(' ','_',AUI2_string)+'\t'+RELA+'\n'
            outfile.write(outline)
        except IndexError:
            continue
