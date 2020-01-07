from bs4 import BeautifulSoup
import os
import re
import json
import errno

strings = dict()
with open('strings.json') as f:
	strings = json.load(f)

def safeopen(path):
	if not os.path.exists(os.path.dirname(path)):
		try: os.makedirs(os.path.dirname(path))
		except OSError as exc:
			if exc.errno != errno.EEXIST: raise
	return open(path, 'w')


def ParseXMLIdentification(soup, lang, basepath, code, olcode):
	metadata = soup.identification
	identification = dict()
	identification['lang'] = lang

	if soup.name == 'statute':
		if metadata.chapter.consolidatednumber.attrs['official'] == 'yes':
			chapterNumber = metadata.chapter.consolidatednumber.text
			startletter = chapterNumber[0]
			identification['filepath'] = os.path.join(basepath, strings['rsc'][lang], startletter, chapterNumber+'.md')
			olLang = ''
			if lang == 'en':
				identification['shortCode'] = strings['rsc_acronym'][lang] + " 1985, " + strings['chapter_prefix'][lang] + " " + chapterNumber
				olLang = 'fr'
			elif lang == 'fr':
				identification['shortCode'] = strings['rsc_acronym'][lang] + " (1985), " + strings['chapter_prefix'][lang] + " " + chapterNumber
				olLang = 'en'
			identification['olfilepath'] = os.path.join(olLang, strings['acts'][olLang], strings['rsc'][olLang], startletter, chapterNumber+'.md')
		elif metadata.chapter.consolidatednumber.attrs['official'] == 'no':
			statuteNumber = metadata.chapter.annualstatuteid
			identification['shortCode'] = strings['sc_acronym'][lang] + " " + statuteNumber.yyyy.text + ", " + strings['chapter_prefix'][lang]+' '+statuteNumber.annualstatutenumber.text
			identification['filepath'] = os.path.join(basepath, strings['sc'][lang], statuteNumber.yyyy.text, strings['chapter_prefix'][lang]+' '+statuteNumber.annualstatutenumber.text+'.md')
			olLang = ''
			if lang == 'en': olLang = 'fr'
			elif lang == 'fr': olLang = 'en'
			identification['olfilepath'] = os.path.join(olLang, strings['acts'][olLang], strings['sc'][olLang], statuteNumber.yyyy.text, strings['chapter_prefix'][olLang]+' '+statuteNumber.annualstatutenumber.text+'.md')
	elif soup.name == 'regulation':
		# code = soup.instrumentnumber.text
		regType = ""
		if code.startswith('C.R.C.'): regType = 'crc'
		elif code.startswith('SI'): regType = 'si'
		elif code.startswith('TR'): regType = 'si'
		elif code.startswith('SOR'): regType = 'sor'
		elif code.startswith('DORS'): regType = 'sor'
		identification['shortCode'] = code
		if code.find('/') != -1:
			identification['filepath'] = os.path.join(basepath, strings[regType][lang], code[code.index('/')+1:].replace('-', '/') + ".md")
			olLang = ''
			if lang == 'en': olLang = 'fr'
			elif lang == 'fr': olLang = 'en'
			identification['olfilepath'] = os.path.join(olLang, strings['regulations'][olLang], strings[regType][olLang], code[code.index('/')+1:].replace('-', '/') + ".md")
		else:
			if regType == 'crc':
				m = re.search(r'\d+$', code)
				crcChapNum = int(m.group())
				crcRangeLow = int((crcChapNum-1)/100) * 100 + 1
				subdirName = str(crcRangeLow) + "-" + str(crcRangeLow+99)
				identification['filepath'] = os.path.join(basepath, strings[regType][lang], subdirName, code + ".md")
				olLang = ''
				if lang == 'en': olLang = 'fr'
				elif lang == 'fr': olLang = 'en'
				identification['olfilepath'] = os.path.join(olLang, strings['regulations'][olLang], strings[regType][olLang], subdirName, olcode + ".md")
			else: identification['filepath'] = os.path.join(basepath, strings[regType][lang], code + ".md")

	if metadata.longtitle != None:
		identification['longtitle'] = metadata.longtitle.text
		identification['mainName'] = 'longtitle'

	if metadata.shorttitle != None:
		identification['shorttitle'] = metadata.shorttitle.text
		if 'status' in metadata.shorttitle.attrs:
			if metadata.shorttitle.attrs['status'] == 'official':
				identification['mainName'] = 'shorttitle'

	if os.path.isfile(os.path.join('docs', identification['filepath'])):
		identification['isNew'] = False
	else: identification['isNew'] = True

	if 'mainName' not in identification:
		if 'longtitle' not in identification and 'shorttitle' in identification:
			identification['mainName'] = 'shorttitle'
		elif 'shorttitle' not in identification and 'longtitle' in identification:
			identification['mainName'] = 'longtitle'

	supplimentaryData = dict()
	if metadata.billnumber != None:
		supplimentaryData['createdFromBill'] = metadata.billnumber.text

	if metadata.billhistory != None:
		_assent = metadata.billhistory.find('stages', {'stage': 'assented-to'})
		if _assent != None:
			assent = _assent.next
			supplimentaryData['assent'] = dict()
			supplimentaryData['assent']['year'] = assent.yyyy.text
			supplimentaryData['assent']['month'] = assent.mm.text
			supplimentaryData['assent']['day'] = assent.dd.text

	if metadata.parliament != None:
		supplimentaryData['createdParliamentNumber'] = metadata.parliament.number.text
		supplimentaryData['createdParliamentSession'] = metadata.parliament.session.text

	if metadata.registrationdate != None:
		registration = metadata.registrationdate
		supplimentaryData['registration'] = dict()
		supplimentaryData['registration']['year'] = registration.date.yyyy.text
		supplimentaryData['registration']['month'] = registration.date.mm.text
		supplimentaryData['registration']['day'] = registration.date.dd.text
	
	if metadata.enablingauthority != None:
		supplimentaryData['authorities'] = metadata.enablingauthority

	# if metadata.readernote != None:
	# supplimentaryData['notes'] = []
	notelist = metadata.find_all('note')
	for note in notelist:
		notestr = ""
		for part in note.contents:
			if part.name == "emphasis":
				if part.attrs['style'] == 'italic':
					# notestr = notestr + "*" + part.text + "*"
					notestr = notestr + part.text
			else: notestr = notestr + str(part)
		if 'notes' not in supplimentaryData: supplimentaryData['notes'] = []
		supplimentaryData['notes'].append(notestr)



	identification['suppliments'] = supplimentaryData

	return identification

def makeMdLink(text, path):
	return "[" + text + "](" + path.replace(' ', '%20') + ")"

def getOppositeLanguageCode(lang):
	if lang == 'en': return 'fr'
	elif lang == 'fr': return 'en'
	else: print("What is " + lang + "?")
	return ""

def getProperNumberFromSymbolFreeSymbol(code):
	if code.startswith('C.R.C.'): return code.replace('_', ' ')
	elif code.startswith('SI'):
		lcode = list(code)
		lcode[2] = '/'
		return ''.join(lcode)
	elif code.startswith('TR'):
		lcode = list(code)
		lcode[2] = '/'
		return ''.join(lcode)
	elif code.startswith('SOR'):
		lcode = list(code)
		lcode[3] = '/'
		return ''.join(lcode)
	elif code.startswith('DORS'):
		lcode = list(code)
		lcode[4] = '/'
		return ''.join(lcode)
	else: return code

def renderXRefExternal(fp, section, docs, docKey, lang, indentLevel):
	if 'reference-type' in section.attrs:
		if section.attrs['reference-type'] != 'other':
			if section.text.upper() != docs[docKey][lang]['name'].upper():
				if 'link' in section.attrs:
					convertedCode = getProperNumberFromSymbolFreeSymbol(section.attrs['link'])
					if convertedCode in docs:
						if lang in docs[convertedCode]:
							if 'filelink' in docs[convertedCode][lang]:
								fp.write(makeMdLink(section.text, '/'+docs[convertedCode][lang]['filelink']))
							else:
								print("-> Unable to create XRefExternal link for [" + convertedCode + "]: No filelink in docs")
								fp.write(section.text)
						elif getOppositeLanguageCode(lang) in docs[convertedCode]:
							olLang = getOppositeLanguageCode(lang)
							if 'filelink' in docs[convertedCode][olLang]:
								fp.write(makeMdLink(section.text, '/'+docs[convertedCode][olLang]['filelink']))
							else:
								print("-> Unable to create XRefExternal link for [" + convertedCode + "]("+olLang+"): No filelink in docs")
								fp.write(section.text)
					else:
						print("-> Unable to create XRefExternal link: ["+convertedCode+"] does not exist in docs.")
						fp.write(section.text)
				else: # Search for the reference, if available
					for law in docs:
						if lang in docs[law]:
							if docs[law][lang]['name'].upper() == section.text.upper():
								if 'filelink' in docs[law][lang]:
									fp.write(makeMdLink(section.text, '/'+docs[law][lang]['filelink']))
									return
								else:
									print("-> Unable to create XRefExternal link for [" + law + "]")
									fp.write(section.text)
									return
					print("-> Unable to create XRefExternal link: ["+section.text+"] does not exist in docs.")
					fp.write(section.text)
			else:
				fp.write(section.text) # No need to make recursive links
		else:
			if 'link' in section.attrs:
				if section.attrs['link'] == 'gazette':
					fp.write(makeMdLink(section.text, 'http://www.gazette.gc.ca/'))
				else:
					print("-> Unknown XRefExternal link alias: " + section.attrs['link'])
					fp.write(section.text)
			else: fp.write(section.text)
	else: fp.write(section.text)

def renderInlineFootnote(fp, section, docs, docKey, lang, indentLevel):
	fp.write("<sup>")
	if 'idref' in section.attrs:
		fp.write("<a href='#"+section.attrs['idref']+"'>")
	fp.write("["+section.text+"]")
	if 'idref' in section.attrs:
		fp.write("</a>")
	fp.write("</sup>")
	for subsection in section.children:
		if subsection.name != None:
			print("-> Encountered unhandled subsection type in FootnoteRef: " + subsection.name)
			fp.write(subsection.text)

def renderSignatureBlock(fp, section, docs, docKey, lang, indentLevel):
	fp.write("\r\n<p>")
	for subsection in section.children:
		if subsection.name == 'signaturename':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'signaturetitle':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'signatureline':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in SignatureBlock: " + subsection.name)
			fp.write(subsection.text)
		fp.write("<br />")
	fp.write("</p>")

def renderImageGroup(fp, section, docs, docKey, lang, indentLevel):
	if section.alternatetext != None:
		fp.write('\r\n')
		fp.write("> Image: " + section.alternatetext.text)
		fp.write('\r\n')
	else:
		fp.write('\r\n> ')
		fp.write(strings['image_no_alt'][lang])
		fp.write('\r\n')

def renderProvision(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'label':
			renderLabel(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'marginalnote':
			renderMarginalNote(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n')
		elif subsection.name == 'provision':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'tablegroup':
			renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'group':
	 		renderGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provisionheading':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'oath':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'signatureblock':
			renderSignatureBlock(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'imagegroup':
			renderImageGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'bilingualgroup':
			renderBilingualGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'amendedcontent':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'readascontent':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'groupheading':
			fp.write("\r\n")
			subsection.attrs['level'] = 2
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'list':
			renderList(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'section':
			fp.write("\r\n")
			renderSection(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'note':
			fp.write("\r\n> ")
			fp.write(subsection.text)
		elif subsection.name == 'definition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulaparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'group1-part':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'group2-division':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'group3-subdivision':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'group4':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'quotedtext':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'amendedtext':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'schedule':
			fp.write("\r\n")
			renderSchedule(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'pagebreak':
			fp.write("\r\n\r\n\r\n")
			fp.write("--------------------------")
			fp.write("\r\n\r\n")
		elif subsection.name == 'formgroup':
			renderFormGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'note':
			fp.write("\r\n> ")
			fp.write(subsection.text)
		elif subsection.name == 'subsection':
			fp.write('\r\n')
			renderSubsection(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'readastext':
			renderReadAsText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'sectionpiece':
			fp.write("\r\n")
			renderSection(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'repealed':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Provision: " + subsection.name)
			fp.write(subsection.text)

def renderDefinition(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'paragraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'marginalnote':
			renderMarginalNote(fp, subsection, docs, docKey, lang, indentLevel, ignoreDefinedTerms=True)
		elif subsection.name == 'continueddefinition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'readastext':
			renderReadAsText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'formuladefinition':
			renderFormulaDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'subparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'note':
			fp.write("\r\n> ")
			fp.write(subsection.text)
		elif subsection.name == 'formulaparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'definition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Definition: " + subsection.name)
			fp.write(subsection.text)

def renderLeader(fp, section, docs, docKey, lang, indentLevel):
	if section.text != '':
		print("-> Non-empty Leader tag: " + section.text)
		fp.write(section.text)
	else:
		if 'leader' in section.attrs:
			if section.attrs['leader'] == 'dot':
				fp.write('____________')
			elif section.attrs['leader'] == 'none':
				fp.write('&nbsp;&nbsp;&nbsp;&nbsp;')
			elif section.attrs['leader'] == 'solid':
				fp.write('_________________________')
			elif section.attrs['leader'] == 'dash':
				fp.write('----------------')
			else:
				print("-> Unknown attributes in Leader: " + str(section.attrs))
				fp.write(section.text)
		else: fp.write('&nbsp;&nbsp;&nbsp;&nbsp;')

def renderText(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name != None:
			if subsection.name == 'xrefexternal':
				renderXRefExternal(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'footnoteref':
				renderInlineFootnote(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'emphasis':
				if 'style' in subsection.attrs:
					if subsection.attrs['style'] == 'italic':
						fp.write('*')
						fp.write(subsection.text)
						fp.write('*')
					elif subsection.attrs['style'] == 'smallcaps':
						fp.write(subsection.text.upper())
					elif subsection.attrs['style'] == 'bold':
						fp.write('**')
						fp.write(subsection.text)
						fp.write('**')
					elif subsection.attrs['style'] == 'underline':
						fp.write(subsection.text)
					elif subsection.attrs['style'] == 'overbar':
						fp.write(subsection.text)
					elif subsection.attrs['style'] == 'regular':
						fp.write(subsection.text)
					else:
						print("-> Encountered unhandled emphasis type in Text: " + subsection.attrs['style'])
						fp.write(subsection.text)
				else:
					fp.write(subsection.text)
			elif subsection.name == 'sup':
				fp.write("<sup>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</sup>")
			elif subsection.name == 'sub':
				fp.write("<sub>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</sub>")
			elif subsection.name == 'language':
				if subsection.attrs['xml:lang'] != lang:
					fp.write("*")
					renderText(fp, subsection, docs, docKey, lang, indentLevel)
					fp.write("*")
				else:
					renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'definedtermen':
				fp.write("*")
				if lang == 'en': fp.write("**")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("*")
				if lang == 'en': fp.write("**")
			elif subsection.name == 'definitionenonly':
				fp.write("*")
				if lang == 'en': fp.write("**")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("*")
				if lang == 'en': fp.write("**")
			elif subsection.name == 'definedtermfr':
				fp.write("*")
				if lang == 'fr': fp.write("**")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("*")
				if lang == 'fr': fp.write("**")
			elif subsection.name == 'definitionfronly':
				fp.write("*")
				if lang == 'fr': fp.write("**")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("*")
				if lang == 'fr': fp.write("**")
			elif subsection.name == 'repealed':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'bilingualgroup':
				renderBilingualGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'xrefinternal':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'definitionref':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'sectionpiece':
				fp.write("\r\n")
				renderSection(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("\r\n")
			elif subsection.name == 'section':
				fp.write("\r\n")
				renderSection(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("\r\n")
			elif subsection.name == 'subsection':
				fp.write('\r\n')
				renderSubsection(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'heading':
				fp.write("\r\n")
				renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("\r\n")
			elif subsection.name == 'text':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'longtitle':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'provision':
				renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write('\r\n\r\n')
			elif subsection.name == 'leaderrightjustified': continue
			elif subsection.name == 'leader':
				renderLeader(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'formblank':
				fp.write("\r\n")
				fp.write("____________________")
				fp.write("\r\n")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'oath':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'group':
				renderGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'originatingref':
				fp.write("\r\n**")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("**")
			elif subsection.name == 'tablegroup':
				renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'schedule':
				fp.write("\r\n")
				renderSchedule(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("\r\n")
			elif subsection.name == 'historicalnote':
				renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'readastext':
				renderReadAsText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'billinternal':
				fp.write("\r\n")
				renderBillInternal(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("\r\n")
			elif subsection.name == 'imagegroup':
				renderImageGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'historicalnotesubitem':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'signatureblock':
				renderSignatureBlock(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'linebreak':
				fp.write("\r\n<br />\r\n")
			elif subsection.name == 'fraction':
				fp.write("(")
				renderText(fp, subsection.numerator, docs, docKey, lang, indentLevel)
				fp.write(") ÷ (")
				renderText(fp, subsection.denominator, docs, docKey, lang, indentLevel)
				fp.write(")")
			elif subsection.name == 'msup':
				fp.write("(")
				renderText(fp, subsection.base, docs, docKey, lang, indentLevel)
				fp.write(")<sup>")
				renderText(fp, subsection.superscript, docs, docKey, lang, indentLevel)
				fp.write("</sup>")
			elif subsection.name == 'msub':
				renderText(fp, subsection.base, docs, docKey, lang, indentLevel)
				fp.write("<sub>")
				renderText(fp, subsection.subscript, docs, docKey, lang, indentLevel)
				fp.write("</sub>")
			elif subsection.name == 'list':
				renderList(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'ins':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'definition':
				fp.write("\r\n\r\n")
				renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'group1-part':
				fp.write('\r\n\r\n')
				renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write('\r\n\r\n')
			elif subsection.name == 'group2-division':
				fp.write('\r\n\r\n')
				renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write('\r\n\r\n')
			elif subsection.name == 'group3-subdivision':
				fp.write('\r\n\r\n')
				renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write('\r\n\r\n')
			elif subsection.name == 'del':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'formula':
				fp.write("\r\n```\r\n")
				renderFormula(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("\r\n```\r\n")
			elif subsection.name == 'formulagroup':
				renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'formuladefinition':
				renderFormulaDefinition(fp, subsection, docs, docKey, lang, indentLevel)
			else:
				print("-> Encountered unhandled subsection type in Text: " + subsection.name)
				fp.write(subsection.text)
		else: 
			if subsection.parent.name == 'titletext':
				fp.write(subsection.replace('\r', '').replace('\n', ''))
			else:
				fp.write(subsection)

def renderLabel(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name != None:
			if subsection.name == 'footnoteref':
				renderInlineFootnote(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'emphasis':
				if 'style' in subsection.attrs:
					if subsection.attrs['style'] == 'italic':
						fp.write('*')
						fp.write(subsection.text)
						fp.write('*')
					elif subsection.attrs['style'] == 'smallcaps':
						fp.write(subsection.text.upper())
					elif subsection.attrs['style'] == 'bold':
						fp.write('**')
						fp.write(subsection.text)
						fp.write('**')
					elif subsection.attrs['style'] == 'underline':
						fp.write(subsection.text)
					elif subsection.attrs['style'] == 'overbar':
						fp.write(subsection.text)
					elif subsection.attrs['style'] == 'regular':
						fp.write(subsection.text)
					else:
						print("-> Encountered unhandled emphasis type in Label: " + subsection.attrs['style'])
						fp.write(subsection.text)
				else:
					fp.write(subsection.text)
			elif subsection.name == 'language':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'sup':
				fp.write("<sup>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</sup>")
			elif subsection.name == 'sub':
				fp.write("<sub>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</sub>")
			elif subsection.name == 'xrefinternal':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'label':
				renderLabel(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'leader':
				renderLeader(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'ins':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			else:
				print("-> Encountered unhandled subsection type in Label: " + subsection.name)
				fp.write(subsection.text)
		else:
			fp.write("**")
			fp.write(subsection)
			fp.write("** ")

def renderFootnoteArea(fp, section, docs, docKey, lang, indentLevel):
	fp.write("\r\n\r\n")
	# fp.write("\r\n\r\n<p>")
	for subsection in section.children:
		if subsection.name == 'label':
			if 'id' in section.attrs:
				fp.write("<a name='" + section.attrs['id'] + "'><sup>")
			else: fp.write("<sup>")
			fp.write(subsection.text)
			if 'id' in section.attrs:
				fp.write("</sup></a>: ")
			else: fp.write("</sup>: ")
		elif subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("<br />")
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			fp.write("\r\n\r\n")
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n\r\n")
		elif subsection.name == 'definition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'list':
			renderList(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Footnote: " + subsection.name)
			fp.write(subsection.text)
	# fp.write("</p>\r\n")

def renderHistoricalNote(fp, section, docs, docKey, lang, indentLevel):
	printedArrow = False
	for subsection in section.children:
		if subsection.name != None:
			if subsection.name == 'historicalnotesubitem':
				if not printedArrow:
					fp.write("\r\n> ")
					printedArrow = True
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'sup':
				fp.write("<sup>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</sup>")
			elif subsection.name == 'xrefexternal':
				renderXRefExternal(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'language':
				if subsection.attrs['xml:lang'] != lang:
					fp.write("*")
					renderText(fp, subsection, docs, docKey, lang, indentLevel)
					fp.write("*")
				else:
					renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'emphasis':
				if 'style' in subsection.attrs:
					if subsection.attrs['style'] == 'italic':
						fp.write('*')
						fp.write(subsection.text)
						fp.write('*')
					elif subsection.attrs['style'] == 'smallcaps':
						fp.write(subsection.text.upper())
					elif subsection.attrs['style'] == 'bold':
						fp.write('**')
						fp.write(subsection.text)
						fp.write('**')
					elif subsection.attrs['style'] == 'underline':
						fp.write(subsection.text)
					elif subsection.attrs['style'] == 'overbar':
						fp.write(subsection.text)
					elif subsection.attrs['style'] == 'regular':
						fp.write(subsection.text)
					else:
						print("-> Encountered unhandled emphasis type in HistoricalNote: " + subsection.attrs['style'])
						fp.write(subsection.text)
				else:
					fp.write(subsection.text)
			elif subsection.name == 'repealed':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			else:
				print("-> Encountered unhandled subsection type in HistoricalNote: " + subsection.name)
				fp.write(subsection.text)
		else:
			if not printedArrow:
				fp.write("\r\n> ")
				printedArrow = True
			fp.write(subsection)
	fp.write("\r\n")

def renderMarginalNote(fp, section, docs, docKey, lang, indentLevel, ignoreDefinedTerms=False):
	if not ignoreDefinedTerms:
		fp.write("\r\n**")
	# else: fp.write("AAAAAAAAAAAAAAAAAAAAA")
	for subsection in section.children:
		if subsection.name != None:
			if subsection.name == 'definedtermen':
				if not ignoreDefinedTerms:
					renderText(fp, subsection, docs, docKey, lang, indentLevel)
				else: continue
			elif subsection.name == 'definedtermfr':
				if not ignoreDefinedTerms:
					renderText(fp, subsection, docs, docKey, lang, indentLevel)
				else: continue
			elif subsection.name == 'emphasis':
				if 'style' in subsection.attrs:
					if subsection.attrs['style'] == 'italic':
						fp.write('*')
						fp.write(subsection.text)
						fp.write('*')
					elif subsection.attrs['style'] == 'smallcaps':
						fp.write(subsection.text.upper())
					elif subsection.attrs['style'] == 'bold':
						fp.write('**')
						fp.write(subsection.text)
						fp.write('**')
					elif subsection.attrs['style'] == 'underline':
						fp.write(subsection.text)
					elif subsection.attrs['style'] == 'overbar':
						fp.write(subsection.text)
					elif subsection.attrs['style'] == 'regular':
						fp.write(subsection.text)
					else:
						print("-> Encountered unhandled emphasis type in MarginalNote: " + subsection.attrs['style'])
						fp.write(subsection.text)
				else:
					fp.write(subsection.text)
			elif subsection.name == 'language':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'xrefexternal':
				renderXRefExternal(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'xrefinternal':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'definitionref':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'definitionenonly':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'definitionfronly':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'historicalnote':
				renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'sup':
				fp.write("<sup>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</sup>")
			elif subsection.name == 'sub':
				fp.write("<sub>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</sub>")
			elif subsection.name == 'provisionheading':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'footnoteref':
				renderInlineFootnote(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'del':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'linebreak':
				fp.write("\r\n<br />\r\n")
			else:
				print("-> Encountered unhandled subsection type in MarginalNote: " + subsection.name)
				fp.write(subsection.text)
		else:
			fp.write(subsection)
	if not ignoreDefinedTerms:
		fp.write("**\r\n")
	# else: fp.write("AAAAAAAAAAAAAAAAAAAAA")

def renderParagraph(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'label':
			fp.write("\r\n")
			for i in range(indentLevel):
				fp.write("\t")
			fp.write("- ")
			renderLabel(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'subparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'continuedsubparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'continuedparagraph':
			fp.write('\r\n')
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'clause':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'continuedclause':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'subclause':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'continuedsubclause':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'subsubclause':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'readastext':
			renderReadAsText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'marginalnote':
			renderMarginalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulaparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'continuedformulaparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'tablegroup':
			renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'amendedtext':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formuladefinition':
			renderFormulaDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'imagegroup':
			renderImageGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'mathmlblock':
			renderMathMlContents(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'note':
			fp.write("\r\n> ")
			fp.write(subsection.text)
		elif subsection.name == 'quotedtext':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'formgroup':
			renderFormGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'definition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'list':
			renderList(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'oath':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Paragraph: " + subsection.name)
			fp.write(subsection.text)

def renderScheduleFormHeading(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'label':
			fp.write('\r\n### ')
			renderLabel(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'originatingref':
			fp.write("\r\n**")
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("**")
		elif subsection.name == 'titletext':
			fp.write('\r\n## ')
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'repealed':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in ScheduleFormHeading: " + subsection.name)
			fp.write(subsection.text)

def renderTableGroup(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'caption':
			fp.write('\r\n#### ')
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'table':
			fp.write("\r\n<table>")
			for table in subsection.children:
				if table.name == 'tgroup':
					for tpart in table.children:
						if tpart.name == 'colspec': continue
						elif tpart.name == 'thead':
							for thead in tpart.children:
								if thead.name == 'row':
									fp.write("\r\n<tr>")
									for row in thead.children:
										if row.name == 'entry':
											fp.write("\r\n<th>")
											renderText(fp, row, docs, docKey, lang, indentLevel)
											fp.write("</th>")
										else:
											print("-> Encountered unhandled subsection type in TableGroup/table/tgroup/thead/row: " + row.name)
											fp.write(row.text)
									fp.write("\r\n</tr>")
								else:
									print("-> Encountered unhandled subsection type in TableGroup/table/tgroup/thead: " + thead.name)
									fp.write(thead.text)
						elif tpart.name == 'tbody':
							for tbody in tpart.children:
								if tbody.name == 'row':
									fp.write("\r\n<tr>")
									for row in tbody.children:
										if row.name == 'entry':
											fp.write("\r\n<td>")
											renderText(fp, row, docs, docKey, lang, indentLevel)
											fp.write("</td>")
										else:
											print("-> Encountered unhandled subsection type in TableGroup/table/tgroup/tbody/row: " + row.name)
											fp.write(row.text)
									fp.write("\r\n</tr>")
								else:
									print("-> Encountered unhandled subsection type in TableGroup/table/tgroup/tbody: " + tbody.name)
									fp.write(tbody.text)
						else:
							print("-> Encountered unhandled subsection type in TableGroup/table/tgroup: " + tpart.name)
							fp.write(tpart.text)
				elif table.name == 'title':
					fp.write("\r\n<h4>")
					renderText(fp, table, docs, docKey, lang, indentLevel)
					fp.write("</h4>")
				else:
					print("-> Encountered unhandled subsection type in TableGroup/table: " + table.name)
					fp.write(table.text)
			fp.write("\r\n</table>\r\n")

		else:
			print("-> Encountered unhandled subsection type in TableGroup: " + subsection.name)
			fp.write(subsection.text)

def renderRegulationPiece(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'section':
			fp.write("\r\n")
			renderSection(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'group1-part':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'relatedornotinforce':
			renderRelatedOrNotInForce(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'group2-division':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'group3-subdivision':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'group4':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'schedule':
			fp.write("\r\n")
			renderSchedule(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		else:
			print("-> Encountered unhandled subsection type in RegulationPiece: " + subsection.name)
			fp.write(subsection.text)

def renderBilingualGroup(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'titletext':
			fp.write('\r\n##### ')
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'bilingualitemen':
			if lang == 'en':
				fp.write("\r\n\r\n")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			else:
				fp.write("<br />- <i>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</i>")
		elif subsection.name == 'bilingualitemfr':
			if lang == 'fr':
				fp.write("\r\n\r\n")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			else:
				fp.write("<br />- <i>")
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("</i>")
		else:
			print("-> Encountered unhandled subsection type in BilingualGroup: " + subsection.name)
			fp.write(subsection.text)

def renderRelatedOrNotInForce(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'section':
			fp.write("\r\n")
			renderSection(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		else:
			print("-> Encountered unhandled subsection type in RelatedOrNotInForce: " + subsection.name)
			fp.write(subsection.text)

def renderBillPiece(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'relatedornotinforce':
			renderRelatedOrNotInForce(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'section':
			fp.write("\r\n")
			renderSection(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'group1-part':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		else:
			print("-> Encountered unhandled subsection type in BillPiece: " + subsection.name)
			fp.write(subsection.text)

def renderItem(fp, section, docs, docKey, lang, indentLevel):
	fp.write("\r\n")
	for i in range(indentLevel):
		fp.write("\t")
	fp.write("- ")
	for subsection in section.children:
		if subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'label':
			renderLabel(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'item':
			renderItem(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'list':
			renderList(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Item: " + subsection.name)
			fp.write(subsection.text)

def renderList(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'item':
			renderItem(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in List: " + subsection.name)
			fp.write(subsection.text)

def renderGroup(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'provision':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
			# for provisionitem in subsection.children:
			# 	if provisionitem.name == 'text':
			# 		fp.write("\r\n")
			# 		for i in range(indentLevel):
			# 			fp.write("\t")
			# 		fp.write("- ")
			# 		renderText(fp, provisionitem, docs, docKey, lang, indentLevel)
			# 	elif provisionitem.name == 'group':
			# 		renderGroup(fp, provisionitem, docs, docKey, lang, indentLevel)
			# 	elif provisionitem.name == 'label':
			# 		fp.write('\r\n\r\n')
			# 		renderLabel(fp, provisionitem, docs, docKey, lang, indentLevel)
			# 	elif provisionitem.name == 'provision':
			# 		fp.write('\r\n\r\n')
			# 		renderProvision(fp, provisionitem, docs, docKey, lang, indentLevel)
			# 		fp.write('\r\n\r\n')
			# 	elif provisionitem.name == 'tablegroup':
			# 		renderTableGroup(fp, provisionitem, docs, docKey, lang, indentLevel)
			# 	elif provisionitem.name == 'footnote':
			# 		renderFootnoteArea(fp, provisionitem, docs, docKey, lang, indentLevel)
			# 	elif provisionitem.name == 'provisionheading':
			# 		renderText(fp, provisionitem, docs, docKey, lang, indentLevel)
			# 	else:
			# 		print("-> Encountered unhandled subsection type in Group/Provision: " + provisionitem.name)
			# 		fp.write(provisionitem.text)
		elif subsection.name == 'groupheading':
			fp.write("\r\n")
			subsection.attrs['level'] = 2
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'group':
			renderGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'definition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Group: " + subsection.name)
			fp.write(subsection.text)

def renderFormGroup(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'scheduleformheading':
			renderScheduleFormHeading(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			fp.write("\r\n")
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'signatureblock':
			renderSignatureBlock(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'tablegroup':
			renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in FormGroup: " + subsection.name)
			fp.write(subsection.text)

def renderDocumentInternal(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'group':
			renderGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			fp.write("\r\n")
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'groupheading':
			fp.write("\r\n")
			subsection.attrs['level'] = 2
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'schedule':
			fp.write("\r\n")
			renderSchedule(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		else:
			print("-> Encountered unhandled subsection type in DocumentInternal: " + subsection.name)
			fp.write(subsection.text)


def renderSchedule(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'scheduleformheading':
			renderScheduleFormHeading(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'tablegroup':
			renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'regulationpiece':
			renderRegulationPiece(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			fp.write("\r\n")
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n\r\n")
		elif subsection.name == 'bilingualgroup':
			renderBilingualGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'billpiece':
			renderBillPiece(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'list':
			renderList(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'documentinternal':
			renderDocumentInternal(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'schedule':
			fp.write("\r\n")
			renderSchedule(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formgroup':
			renderFormGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'repealed':
			fp.write("\r\n")
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'note':
			fp.write("\r\n> ")
			fp.write(subsection.text)
		elif subsection.name == 'oath':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'runninghead':
			continue
		elif subsection.name == 'imagegroup':
			renderImageGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'readastext':
			renderReadAsText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'signatureblock':
			renderSignatureBlock(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'pagebreak':
			fp.write("\r\n\r\n\r\n")
			fp.write("--------------------------")
			fp.write("\r\n\r\n")
		elif subsection.name == 'conventionagreementtreaty':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'amendedtext':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Schedule: " + subsection.name)
			fp.write(subsection.text)

def renderHeading(fp, section, docs, docKey, lang, indentLevel):
	printedArrow = False
	for subsection in section.children:
		if subsection.name == 'titletext':
			fp.write('\r\n#')
			if 'level' in section.attrs:
				for i in range(int(section.attrs['level'])):
					fp.write('#')
			else: fp.write('#')
			fp.write(' ')
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'note':
			if not printedArrow:
				fp.write("\r\n> ")
				printedArrow = True
			fp.write(subsection.text)
		elif subsection.name == 'label':
			fp.write('\r\n')
			renderLabel(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'marginalnote':
			renderMarginalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'originatingref':
			fp.write("\r\n**")
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("**")
		elif subsection.name == 'separator':
			fp.write('\r\n----------------\r\n')
		else:
			print("-> Encountered unhandled subsection type in Heading: " + subsection.name)
			fp.write(subsection.text)
	if printedArrow: fp.write("\r\n")

def renderReadAsText(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'section':
			fp.write('\r\n')
			renderSection(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n')
		elif subsection.name == 'sectionpiece':
			fp.write("\r\n")
			renderSection(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'subsection':
			fp.write('\r\n')
			renderSubsection(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in ReadAsText: " + subsection.name)
			fp.write(subsection.text)

def renderMathMlContents(fp, section, docs, docKey, lang, indentLevel):
	fp.write('\r\n```')
	fp.write(strings['mathml_substitute'][lang])
	fp.write('```\r\n\r\n')

def renderFormula(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'formulatext':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'imagegroup':
			renderImageGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'mathml':
			renderMathMlContents(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Formula: " + subsection.name)
			fp.write(subsection.text)

def renderFormulaDefinition(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'formulaterm':
			fp.write("\r\n- ")
			renderLabel(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulaparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'continuedformulaparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			fp.write("\r\n")
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'tablegroup':
			renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in FormulaDefinition: " + subsection.name)
			fp.write(subsection.text)

def renderFormulaGroup(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'formula':
			fp.write("\r\n```\r\n")
			renderFormula(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n```\r\n")
		elif subsection.name == 'formulaconnector':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formuladefinition':
			renderFormulaDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulaparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			fp.write("\r\n")
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'alternatetext':
			fp.write('\r\n\r\n(')
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write(')\r\n')
		else:
			print("-> Encountered unhandled subsection type in FormulaGroup: " + subsection.name)
			fp.write(subsection.text)

def renderSubsection(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'label':
			fp.write("\r\n")
			for i in range(indentLevel):
				fp.write("\t")
			fp.write("- ")
			renderLabel(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'text':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'paragraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'marginalnote':
			renderMarginalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'continuedsectionsubsection':
			fp.write('\r\n')
			renderSubsection(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'definition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'readastext':
			renderReadAsText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'note':
			fp.write("\r\n> ")
			fp.write(subsection.text)
		elif subsection.name == 'oath':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'amendedtext':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formuladefinition':
			renderFormulaDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'tablegroup':
			renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'imagegroup':
			renderImageGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'quotedtext':
			fp.write('\r\n\r\n')
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'list':
			renderList(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formulaparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formgroup':
			renderFormGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'signatureblock':
			renderSignatureBlock(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Subsection: " + subsection.name)
			fp.write(subsection.text)

def renderSection(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name != None:
			if subsection.name == 'text':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'label':
				renderLabel(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'paragraph':
				renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'definition':
				fp.write("\r\n\r\n")
				renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'subsection':
				fp.write('\r\n')
				renderSubsection(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'continuedsectionsubsection':
				fp.write('\r\n')
				renderSubsection(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'historicalnote':
				renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'marginalnote':
				renderMarginalNote(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write('\r\n')
			elif subsection.name == 'amendedtext':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'heading':
				fp.write("\r\n")
				renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write("\r\n")
			elif subsection.name == 'footnote':
				renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'provision':
				renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write('\r\n\r\n')
			elif subsection.name == 'note':
				fp.write("\r\n> ")
				fp.write(subsection.text)
			elif subsection.name == 'readastext':
				renderReadAsText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'continuedparagraph':
				fp.write('\r\n')
				renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'subparagraph':
				renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
			elif subsection.name == 'formulagroup':
				renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'oath':
				renderText(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'continueddefinition':
				fp.write("\r\n\r\n")
				renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'tablegroup':
				renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'formuladefinition':
				renderFormulaDefinition(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'clause':
				renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
			elif subsection.name == 'formgroup':
				renderFormGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'commentblock': continue
			elif subsection.name == 'list':
				renderList(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'imagegroup':
				renderImageGroup(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'quotedtext':
				fp.write('\r\n\r\n')
				renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
				fp.write('\r\n\r\n')
			elif subsection.name == 'continuedsubclause':
				renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
			elif subsection.name == 'bilingualgroup':
				renderBilingualGroup(fp, subsection, docs, docKey, lang, indentLevel)
			else:
				print("-> Encountered unhandled subsection type in Section: " + subsection.name)
				fp.write(subsection.text)
		else:
			if subsection[-1] == '?': continue
			else: print("Why is plain there plain text here?!: "+subsection)
	fp.write("\r\n")

def renderPreamble(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'provision':
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Preamble: " + subsection.name)
			fp.write(subsection.text)

def renderEnacts(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'provision':
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		else:
			print("-> Encountered unhandled subsection type in Enacts: " + subsection.name)
			fp.write(subsection.text)

def renderIntroduction(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'preamble':
			fp.write("\r\n")
			renderPreamble(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'enacts':
			fp.write("\r\n")
			renderEnacts(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		else:
			print("-> Encountered unhandled subsection type in Introduction: " + subsection.name)
			fp.write(subsection.text)


def renderBillInternal(fp, section, docs, docKey, lang, indentLevel):
	for subsection in section.children:
		if subsection.name == 'body':
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'longtitle':
			fp.write('\r\n\r\n')
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'section':
			fp.write("\r\n")
			renderSection(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'label':
			renderLabel(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'paragraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'definition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'subsection':
			fp.write('\r\n')
			renderSubsection(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'continuedsectionsubsection':
			fp.write('\r\n')
			renderSubsection(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'historicalnote':
			renderHistoricalNote(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'marginalnote':
			renderMarginalNote(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n')
		elif subsection.name == 'amendedtext':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'heading':
			fp.write("\r\n")
			renderHeading(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write("\r\n")
		elif subsection.name == 'footnote':
			renderFootnoteArea(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'provision':
			renderProvision(fp, subsection, docs, docKey, lang, indentLevel)
			fp.write('\r\n\r\n')
		elif subsection.name == 'note':
			fp.write("\r\n> ")
			fp.write(subsection.text)
		elif subsection.name == 'readastext':
			renderReadAsText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'continuedparagraph':
			fp.write('\r\n')
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'subparagraph':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
		elif subsection.name == 'formulagroup':
			renderFormulaGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'oath':
			renderText(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'continueddefinition':
			fp.write("\r\n\r\n")
			renderDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'tablegroup':
			renderTableGroup(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'formuladefinition':
			renderFormulaDefinition(fp, subsection, docs, docKey, lang, indentLevel)
		elif subsection.name == 'clause':
			renderParagraph(fp, subsection, docs, docKey, lang, indentLevel+1)
		else:
			print("-> Encountered unhandled subsection type in BillInternal: " + subsection.name)
			fp.write(subsection.text)

def GenerateMdFile(soup, identification, filepath, docs, docKey, lang):
	with safeopen(filepath) as outfile:
		print("-> Writing to "+filepath)

		suppliments = identification['suppliments']

		# Header stuff
		outfile.write('> ' + makeMdLink(strings['switch_language_link'][lang], '/'+identification['olfilepath']))
		outfile.write("\r\n\r\n")
		outfile.write('# ' + identification[identification['mainName']])
		outfile.write("\r\n\r\n")
		outfile.write('**' + identification['shortCode'] + "**")
		outfile.write("\r\n\r\n")

		if 'authorities' in suppliments:
			outfile.write(strings['enabling_authorities'][lang])
			for auth in suppliments['authorities']:
				if auth.name == 'xrefexternal':
					outfile.write("\r\n- ")
					renderXRefExternal(outfile, auth, docs, docKey, lang, 0)
				elif auth.name == 'otherauthority':
					outfile.write("\r\n- ")
					renderText(outfile, auth, docs, docKey, lang, 0)
				else:
					print("-> Unknown type for enabling authority: " + auth.name)
					outfile.write(auth.text)
				outfile.write("\r\n")
		outfile.write("\r\n")

		if 'assent' in suppliments:
			outfile.write(strings['assent_date_label'][lang])
			outfile.write(suppliments['assent']['day'])
			outfile.write(" ")
			outfile.write(strings['months'][suppliments['assent']['month']][lang])
			outfile.write(" ")
			outfile.write(suppliments['assent']['year'])
			outfile.write("\r\n\r\n")

		if 'registration' in suppliments:
			outfile.write(strings['registration_date_label'][lang])
			outfile.write(suppliments['registration']['day'])
			outfile.write(" ")
			outfile.write(strings['months'][suppliments['registration']['month']][lang])
			outfile.write(" ")
			outfile.write(suppliments['registration']['year'])
			outfile.write("\r\n\r\n")

		if 'notes' in suppliments:
			outfile.write('```\r\n')
			for n in suppliments['notes']:
				outfile.write(n)
				outfile.write('\r\n')
			outfile.write('```\r\n')

		outfile.write("----------")
		outfile.write("\r\n\r\n")

		indentLevel = 0
		for section in soup.children:
			if section.name == 'identification': continue
			elif section.name == 'order': 
				for subsection in section.children:
					if subsection.name == 'provision':
						renderProvision(outfile, subsection, docs, docKey, lang, indentLevel)
						outfile.write('\r\n\r\n')
					elif subsection.name == 'footnote':
						renderFootnoteArea(outfile, subsection, docs, docKey, lang, indentLevel)
					elif subsection.name == 'historicalnote':
						renderHistoricalNote(outfile, subsection, docs, docKey, lang, indentLevel)
					else:
						print("-> Encountered unhandled subsection type in Order: " + subsection.name)
			elif section.name == 'heading':
				outfile.write("\r\n")
				renderHeading(outfile, section, docs, docKey, lang, indentLevel)
				outfile.write("\r\n")
			elif section.name == 'section':
				outfile.write("\r\n")
				renderSection(outfile, section, docs, docKey, lang, indentLevel)
				outfile.write("\r\n")
			elif section.name == 'repealed':
				outfile.write("\r\n")
				outfile.write(section.text)
				outfile.write("\r\n")
			elif section.name == 'schedule':
				outfile.write("\r\n")
				renderSchedule(outfile, section, docs, docKey, lang, indentLevel)
				outfile.write("\r\n")
			elif section.name == 'introduction':
				outfile.write("\r\n")
				renderIntroduction(outfile, section, docs, docKey, lang, indentLevel)
				outfile.write("\r\n")
			elif section.name == 'reserved':
				outfile.write("\r\n")
				renderText(outfile, section, docs, docKey, lang, indentLevel)
				outfile.write("\r\n")
			else:
				print("-> Encountered unhandled section type: " + section.name)
				outfile.write(section.text)
			outfile.write("\r\n")
	return []