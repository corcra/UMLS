#!/usr/bin/python
# Take the strings from MRCONSO and apply them to MRREL.

import re
import sys

max_ngram = 100 # a reasonably high upper bound (e.g. if no max_ngram is given, no filtering should be done)
bad_RELAS = {'mapped_to','sort_version_of','permuted_term_of','has_sort_version','has_permuted_term','see','entry_version_of','has_entry_version','see_from'} # don't ask

for line in open('UMLSpaths.txt','r'):
    if '#' in line:
        continue
    if 'outfile_path' in line:
        outfile_path = line.split()[1]
    if 'MRREL_path' in line:
        MRREL_path = line.split()[1]
    if 'MRCONSO_path' in line:
        MRCONSO_path = line.split()[1]
    if 'max_ngram' in line:
        max_ngram = int(line.split()[1])

outfile = open(outfile_path,'w')
MRREL_file = open(MRREL_path,'r')
MRCONSO_file = open(MRCONSO_path,'r')

print 'Creating dictionary of AUIs from',MRREL_path
pairs=MRREL_file.readlines()
# dictionary of AUIs... empty
AUIs=dict()
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
        if AUIs[AUI]=='':
            AUIs[AUI] = (CUI,string)
        else:
            print 'We already learned this AUI apparently!', AUIs[AUI]
            print 'Trying to relearn it as',(CUI,string)

print ''

print 'Reassigning pairs with values and saving to',outfile_path
# now go back over and reassign pairs with their values
pruned = 0
kept = 0
print 'Note: pruning pairs which contain ngrams longer than',max_ngram
for pair in pairs:
    splitpair = pair.split('|')
    AUI1 = splitpair[1]
    AUI2 = splitpair[5]
    RELA = splitpair[7]
    if len(RELA)>0 and not RELA in bad_RELAS:
        try:
            AUI1_string = AUIs[AUI1][1]
            AUI2_string = AUIs[AUI2][1]
            if (AUI1_string.count('_')-1)<= max_ngram and (AUI2_string.count('_')-1) <= max_ngram:
                outline = splitpair[0]+':'+re.sub(' ','_',AUI1_string)+'\t'+splitpair[4]+':'+re.sub(' ','_',AUI2_string)+'\t'+RELA+'\n'
                outfile.write(outline)
                kept +=1
            else:
                pruned +=1
        except IndexError:
            continue

print pruned,'examples were pruned.'
print kept,'examples were kept.'
