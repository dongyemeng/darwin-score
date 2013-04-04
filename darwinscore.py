# coding: utf-8

import re
import pprint
import string
from datetime import datetime
#import chardet

def tokenize(text):
	# Tokenize text input
	tokens = text.split()

	text_index = 0
	token_list = []
	for token in tokens:
		token_start = text_index
		token_end = text_index + len(token) - 1
		token_span = (token_start, token_end)
		token_list.append({'token':token, 'token_start':token_start, 'token_end':token_end})
		text_index = token_end + 1 # increment for space separator between tokens
		text_index = text_index + 1 # increment to next token
	return token_list

def load_dictionary(path):
	dictFile = open(path, 'r')
	dictionary=[]
	for line in dictFile:
		for word in line.split():
			dictionary.append(word.lower().strip())
	return dictionary

punct = '“”‘’' + string.punctuation # Add more punctuation to existing Python punct
startTime = datetime.now()
print 'Loading inputs.'

inputFileList = []
inputFileListPath = open('inputs-test.txt', 'r')
for line in inputFileListPath:
	inputFileList.append(line.strip())

# TODO use select pattern files from https://github.com/jbest/regex-repo as input
patterns = [
	{'regex':'(\w+)\W+(\d?\d)\W+(\d\d\d\d)','type':'date','short_name':'MonDDYYYY'},
	{'regex':'[-+]?([0-9]*\.[0-9]+|[0-9]+)','type':'number','short_name':'number'}
	]

wordsENFilePath = 'dicts/en_words.txt'
wordsESFilePath = 'dicts/es_words.txt'
familyFilePath = 'dicts/families.txt'
genusFilePath = 'dicts/genera.txt'
abbrevENFilePath = 'dicts/en_abbr.txt'
abbrevESFilePath = 'dicts/es_abbr.txt'
gazetteerFilePath = 'dicts/gazetteer.txt'
personNamesFilePath = 'dicts/person_names.txt'
specificEpithetFilePath = 'dicts/specific_epithets.txt'
org_abbrev_file_path = 'dicts/org_abbr.txt'

# Load dictionaries and other authority files
dictionaries = []
print 'Loading dictionaries.'
dictionaries.append((load_dictionary(wordsENFilePath),'EN'))
dictionaries.append((load_dictionary(wordsESFilePath),'ES'))
dictionaries.append((load_dictionary(abbrevENFilePath),'EN-abbreviation'))
dictionaries.append((load_dictionary(abbrevESFilePath),'ES-abbreviation'))
dictionaries.append((load_dictionary(gazetteerFilePath),'gazetteer'))
dictionaries.append((load_dictionary(personNamesFilePath),'person name'))
dictionaries.append((load_dictionary(familyFilePath),'family'))
dictionaries.append((load_dictionary(genusFilePath),'genus'))
dictionaries.append((load_dictionary(specificEpithetFilePath),'species'))
dictionaries.append((load_dictionary(org_abbrev_file_path),'species'))

unknowns = []
matched_dates = []
inputs = 0 #Number of file inputs
total_token_count = 0
total_char_count = 0
total_words_matched = 0
total_chars_in_words = 0
total_chars_in_patterns = 0
total_unique_chars_in_patterns = 0

print 'Scoring inputs...'
for filePath in inputFileList:
	# TODO Use chardet to determine encoding of each file
	"""
	# see http://stackoverflow.com/questions/3323770/character-detection-in-a-text-file-in-python-using-the-universal-encoding-detect
	rawdata = inputTextFile.read()
	print rawdata
	cdresult = chardet.detect(rawdata)
	charenc = cdresult['encoding']  
	text = rawdata.decode(charenc)
	print charenc
	print text
	"""
	inputs += 1

	# token stats initialized
	token_count = 0
	input_char_count = 0
	input_words_found = 0
	input_words_found_chars = 0
	input_patterns_matched_chars = 0
	input_unique_patterns_matched_chars = 0

	# Load input text from external file
	inputTextFile = open(filePath, 'r')

	text = inputTextFile.read()
	token_list = tokenize(text)
	#pprint.pprint(token_list)
	joined_text = u''
	for token in token_list:
		# Join tokens with space between each
		# This provides a normalized, predictable string to search for patterns
		# Found patterns can be traced back to constituient tokens
		# TODO Figure out how to correctly decode all strings without using replace
		joined_text = joined_text + token['token'].decode('utf-8', 'replace') + u' '

		matched = False
		for dictionary in dictionaries:
			#  Strip leading and trailing punctuation and whitespace
			t = token['token'].lower().strip(punct + string.whitespace)
			if t in dictionary[0]:
				#TODO Allow to add multiple dictionaries?
				token['in_dict'] = dictionary[1]
				matched = True
		if not matched:
			unknowns.append(token['token'])

	for pattern in patterns:
		#print pattern['regex']
		patternObj = re.compile(pattern['regex'])
		matches = patternObj.finditer(joined_text)
		for match in matches:	
			match_start = match.span()[0]
			match_end = match.span()[1] - 1
			# Storing matched dates just for testing and verification
			if pattern['type'] == 'date':
				matched_dates.append(match.group(0))
			for token in token_list:
				if token['token_start'] >= match_start and token['token_end'] <= match_end:
					#TODO Allow to add multiple patterns?
					token['in_pattern'] = pattern['short_name']

	#pprint.pprint(token_list)

	# Generate report
	for token in token_list:
		#TODO Add word count for pattern matches.
		token_count += 1
		total_token_count += 1
		#print 'token chars:', len(token['token']), token['token']
		token_char_count = len(token['token'])
		input_char_count += token_char_count
		total_char_count += token_char_count
		if 'in_dict' in token:
			#print token['token'], token['in_dict']
			input_words_found += 1
			total_words_matched += 1
			total_chars_in_words += token_char_count
			# FIX Special characters are inflating character count
			# ex: len('República') = 10 vs len('Republica') = 9
			# Need to encode as unicode?
			"""
			token_raw = token['token']
			token_unicode = token_raw.encode(charenc, 'ignore')
			print token_raw, token_unicode
			"""
			input_words_found_chars += len(token['token'])
		if 'in_pattern' in token:
			if 'in_dict' not in token:
				# Only count matching chars that were not counted as matching words
				input_unique_patterns_matched_chars += 1
				total_unique_chars_in_patterns +=1
			input_patterns_matched_chars += token_char_count
			total_chars_in_patterns += token_char_count
	combined_matched_chars = input_words_found_chars + input_unique_patterns_matched_chars
	print '--- summmary ---'
	print 'input file path:', filePath
	print 'token_count:', token_count
	print 'input_words_found:', input_words_found
	print 'input_words_found_chars:', input_words_found_chars
	print 'input_char_count:', input_char_count
	print 'input_patterns_matched_chars:', input_patterns_matched_chars
	print 'input_unique_patterns_matched_chars:', input_unique_patterns_matched_chars
	print '--- score ---'
	#print 'combined_matched_chars', combined_matched_chars
	print 'combined char score', combined_matched_chars / float(input_char_count)

total_word_score = total_words_matched / float(total_token_count)
total_char_word_score = total_chars_in_words / float(total_char_count)

total_char_pattern_score = total_chars_in_patterns / float(total_char_count)
total_combined_char_score = (total_chars_in_words + total_unique_chars_in_patterns) / float(total_char_count)
#totalMatchedCharCount = input_words_found_chars + input_patterns_matched_chars
#dsTotalCharacterScore = totalMatchedCharCount / float(input_char_count)
endTime = datetime.now()
print '--- SUMMARY - all inputs ---'
print 'inputs:', inputs
print 'total_token_count', total_token_count
print 'total_char_count', total_char_count
print 'total_words_matched', total_words_matched
print 'total_chars_in_words', total_chars_in_words
print 'total_chars_in_patterns', total_chars_in_patterns
print 'total_unique_chars_in_patterns', total_unique_chars_in_patterns
print 'total_chars_matched', total_unique_chars_in_patterns + total_chars_in_words
print 'Time elapsed:', endTime - startTime
print '--- SCORES - all inputs ---'
print 'total_word_score', total_word_score
print 'total_char_word_score', total_char_word_score
print 'total_combined_char_score', total_combined_char_score

# Some output for watching results and testing:

"""
for date in matched_dates:
	print date

for word in unknowns:
	if not word.isdigit():
		print word
"""