#!/bin/python
# The purpose of this script is to take the *machine-readable* output of UMLS 
# MetaMap and convert it to something that looks like a sentence of UMLS CUIs, 
# if possible. Ideally there would be an option in MetaMap to do this, assuming
# it is sensible.

import re
import sys

#INTERACTIVE = True
INTERACTIVE = False
# "hacks" to fix metamap weirdness
POSTPROC = True
if POSTPROC:
    print 'WARNING: Performing dataset-specific postprocessing.'

# --- some regexes --- #
utterance_re = re.compile('^utterance\(')
phrase_re = re.compile('^phrase\(')
mappings_re = re.compile('^mappings\(')
candidates_re = re.compile('^candidates\(')
EOU_re = re.compile('^\'EOU')

# this is a file of sentences, fed into metamap
raw_data_path = ''

# --- grab in paths --- #
# this is the metamap output. YMMV
#   created by the command:
# metamap14 -q -Q 3 --word_sense_disambiguation raw_data_path metamap_output_path

# must provide an input path
assert len(sys.argv) >= 2
metamap_output_path = sys.argv[1]
# optionally provide output path
# (this is the processed data path, the output of this script)
try:
    proc_data_path = sys.argv[2]
    # do not write over the input, please
    assert not proc_data_path == metamap_output_path
except IndexError:
    # not provided
    proc_data_path = metamap_output_path + '.reform'

# --- open files --- #
metamap_output = open(metamap_output_path, 'r')
proc_data = open(proc_data_path, 'w')

# --- the first line is 'args', pop that --- #
args_line = metamap_output.readline()
# not sure what second line is but pop it too
unknown_line = metamap_output.readline()

# --- the relevant and important functions --- #
def parse_phrase(line, neg_dict={}):
    """
    Takes a phrase from machine-readable format, parses its mappings, returns
    a string of mapped terms (into CUIs, when possible).
    """
    wordmap = dict()
    # list of words in the phrase
    # (note: the phrase looks like phrase('PHRASEHERE', [sometext(... )
    phrase = re.sub('[\'\.]','',re.split(',\[[a-zA-Z]+\(', re.sub('phrase\(','', line))[0])
    # get the candidates (and most importantly, their numbers)
    candidates = metamap_output.readline()
    if candidates == '' or not candidates_re.match(candidates):
        parsed_phrase = phrase + ' '
        return parsed_phrase
    TotalCandidateCount = int(re.sub('candidates\(','',candidates).split(',')[0])
    # get the mappings
    mappings = metamap_output.readline()
    if mappings == '' or not mappings_re.match(mappings):
        parsed_phrase = phrase + ' '
        return parsed_phrase
    if TotalCandidateCount == 0:
        # there were no mappings for this phrase
        parsed_phrase = phrase + ' '
    else:
        # accounted for by other words
        delwords = []
        parsed_phrase = ''
        # split the mappings up into 'ev's
        split_mappings = mappings.split('ev(')
        outstring = ''
        for mapping in split_mappings[1:]:
            CUI = mapping.split(',')[1].strip('\'')
            try:
                words = re.split('[\[\]]',','.join(mapping.split(',')[4:]))[1].split(',')
            except IndexError:
                # ugh, mapping is messed up
                print 'WARNING: input is messed up'
                return parsed_phrase
            umls_strings = mapping.split(',')[2:4]
            # CPI is the final [] in this mapping, I think/believe
            ConceptPositionalInfo = mapping.split('[')[-1].split(']')[0]
            if ConceptPositionalInfo in neg_dict:
                # this concept has been negated!
                # make sure it's the same one...
                assert CUI in neg_dict[ConceptPositionalInfo]
                # need to make sure it's ONE of the CUIs which was negated at this location
                CUI = 'NOT_' + CUI
            if INTERACTIVE:
                outstring += '\n\tAssociation between '+ CUI + ' and ' + ', '.join(map(lambda x: '"'+x+'"',words))
                if len(words) > 1:
                    outstring += ' (subsuming ' + ' '.join(map(lambda x: '"'+x+'"', words[1:])) + ')'
                outstring += '\n\tbased on UMLS strings ' + ', '.join(umls_strings) +'\n'
            wordmap[words[0]] = CUI
            # if multiple words mapped to this CUI, remember to delete the rest
            # that is: when we consume the sentence later we will 'replace' the
            # first word in this list with the CUI, then delete the rest
            # brittleness: delwords may appear elsewhere in the sentence
            delwords += words[1:]
        # split on spaces, commas
        for word in re.split(', | ', phrase):
            try:
                # lowercase word, cause it is represented in the prolog that way
                parsed_phrase += wordmap[word.lower()] + ' '
            except KeyError:
                if word.lower() in delwords:
                    continue
                else:
                    parsed_phrase += word + ' '
    if INTERACTIVE:
        if len(wordmap) > 0:
            # yolo
            print '\nMapping phrase:',
            print phrase, '...'
            print outstring
            print 'Mapped:', phrase, '--->',
            print parsed_phrase
            print ''
            eh = raw_input('')
    return parsed_phrase

def postproc_utterance(parsed_utterance):
    """
    HACKS!
    Do some 'manual' post-processing to make up for MetaMap peculiarity.
    WARNING: dataset specific.
    """
    # _ S__ DEID --> _S__DEID
    parsed_utterance = re.sub('_ S__ DEID', '_S__DEID', parsed_utterance)
    # _ S__ C2825141 --> _S__FINDING (FINDING...)
    parsed_utterance = re.sub('_ S__ C2825141', '_S__FINDING', parsed_utterance)
    return parsed_utterance

def parse_utterance(neg_dict={}):
    """
    Suck in an utterance from the machine-readable format, parse its mapping
    and then return a string of mapped terms (into CUIs).
    May not be the same length as the input sentence.
    """
    phrases = ''
    line = metamap_output.readline()
    while not EOU_re.match(line):
        if phrase_re.match(line):
            parsed_phrase = parse_phrase(line, neg_dict)
            phrases += parsed_phrase
        elif line == '':
            # EOF I guess...
            return phrases
        elif not EOU_re.match(line):
            print'ERROR: utterance not followed by EOU line, followed by:'
            print line
            sys.exit('ERROR: missing EOU')
        line = metamap_output.readline()
    return phrases

def parse_negline(neg_line):
    """
    Parse the THIRD line of the .mmo file, where the negations are stored.
    Why does it not do this per-phrase? Mystery.
    We connect the negated-CUI to its appearance in the text using the 
    ConceptPositionalInfo which _appears_ to correspond to the PosInfo field
    which appears in the ev found in a mapping.
    The output is neg_dict which maps these ConceptPositionalInfos into the
    associated CUIs :we use this for sanity checking while parsing the mappings;
    the position should be enough to identify it, but for extra-safety we assert
    that the CUIs are matching.
    """
    assert 'neg_list([' in neg_line
    neg_dict = dict()
    # strip things out
    # (removing "neg_list(["... and ..."]).\n")
    l_stripped = neg_line[10:][:-5]
    # split into seprate 'negations'...
    # split on ( and then remove the training ", negation(" at the end, first entry is useless
    negations = map(lambda x: x.rstrip(')')[:-10] if 'negation' in x else x.rstrip(')'), l_stripped.split('('))[1:]
    # for each negation, grab its location and CUI
    for neg in negations:
        # strip the string part of the CUI: we know it's between the SECOND pair of [], and before a :
        NegatedConcept = neg.split('[')[2].split(':')[0].strip('\'')
        # now get the concept... we know it's in the THIRD set of []... and there may be several separated by ,
        ConceptPositionalInfo = neg.split('[')[3].rstrip(']')
        try:
            neg_dict[ConceptPositionalInfo].add(NegatedConcept)
        except KeyError:
            neg_dict[ConceptPositionalInfo] = set([NegatedConcept])
    return neg_dict

# --- run through the file --- #
# --- get the neglist --- #
neg_line = metamap_output.readline()
neg_dict = parse_negline(neg_line)

# the first line
n = 0
while True:
    line = metamap_output.readline()
    if not line: break
    if utterance_re.match(line):
        # we are now in an utterance!
        parsed_utterance = parse_utterance(neg_dict)
        if POSTPROC:
            # hacky post-processing
            parsed_utterance = postproc_utterance(parsed_utterance)
        print 'Parsed utterance:'
        print '\t','"'.join(line.split('"')[1:2]).strip('[]')
        print '=====>'
        print '\t',parsed_utterance
        proc_data.write(parsed_utterance+'\n')
        n += 1
    else:
        # not interested in this line
        continue

proc_data.close()
print '\nWrote', n, 'sentences to', proc_data_path
