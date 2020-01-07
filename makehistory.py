from bs4 import BeautifulSoup
import requests
import re
import os
import json
from git import Repo
from git import Actor
from xmlhelper import ParseXMLIdentification, GenerateMdFile
from datetime import datetime, timezone

gitconfig = dict()
with open('gitconfig.json') as f:
	gitconfig = json.load(f)

repo = Repo('docs/')

gitAuthor = Actor(gitconfig['gituser'], gitconfig['gitemail'])
gitCommitter = Actor(gitconfig['gituser'], gitconfig['gitemail'])
noonTime = datetime.strptime('1200','%H%M').time()
"""
Build the list of docs to go through.
"""

def getLookup():
	with open("lookup.xml") as fp:
		data = BeautifulSoup(fp, 'xml')
		return data.Database
	return []

docs = dict()
with open('docs.json') as f:
	docs = json.load(f)
# olPointers = dict() # {'[id]': '[ChapterNumber/AlphaNumber]'}
# metadata = getLookup()
# acts = metadata.find_all('Statute')
# regs = metadata.find_all('Regulation')
# for act in acts:
# 	id = act.attrs['id']
# 	identifier = act.ChapterNumber.string
# 	officialNum = act.OfficialNumber.string
# 	title = act.ShortTitle.string
# 	language = act.Language.string
# 	lastUpdated = act.LastConsolidationDate.string
# 	olLink = act.attrs['olid'] if 'olid' in act.attrs else -1
	# olPointers[id] = identifier

# 	regulationsUsing = []
# 	if act.find('Relationships'):
# 		relations = act.Relationships
# 		for relation in relations.children:
# 			regulationsUsing.append(relation.attrs['rid'])

# 	insertDict = dict()
# 	insertDict['type'] = "act"
# 	insertDict['name'] = title
# 	insertDict['code'] = identifier
# 	insertDict['officialNumber'] = officialNum
# 	insertDict['id'] = id
# 	insertDict['olid'] = olLink
# 	insertDict['regulationsUsing'] = regulationsUsing
# 	insertDict['lastUpdated'] = int(lastUpdated)

# 	if identifier not in docs:
# 		docs[identifier] = dict()
# 	docs[identifier][language] = insertDict

# for reg in regs:
# 	id = reg.attrs['id']
# 	identifier = reg.AlphaNumber.string
# 	title = ''
# 	if reg.ShortTitle.string != None:
# 		title = reg.ShortTitle.string
# 	elif reg.ReversedShortTitle.string != None:
# 		title = reg.ReversedShortTitle.string
# 	language = reg.Language.string
# 	lastUpdated = reg.LastConsolidationDate.string
# 	olLink = reg.attrs['olid'] if 'olid' in reg.attrs else -1
	# olPointers[id] = identifier

# 	insertDict = dict()
# 	insertDict['type'] = "regulation"
# 	insertDict['name'] = title
# 	insertDict['code'] = identifier
# 	insertDict['id'] = id
# 	insertDict['olid'] = olLink
# 	insertDict['lastUpdated'] = int(lastUpdated)

# 	if identifier not in docs:
# 		docs[identifier] = dict()
# 	docs[identifier][language] = insertDict


# for key, item in docs.items():
# 	if 'en' in item and 'fr' not in item:
# 		if item['en']['olid'] != -1:
# 			item['en']['olLink'] = olPointers[item['en']['olid']]
# 			docs[key] = item
# 		else: print("Missing French version for " + item['en']['code'] + '!')
	
# 	if 'fr' in item and 'en' not in item:
# 		if item['fr']['olid'] != -1:
# 			item['fr']['olLink'] = olPointers[item['fr']['olid']]
# 			docs[key] = item
# 		else: print("Missing English version for " + item['fr']['code'] + '!')


print("Finished building metadata")

"""
Now start making Markdown files, while also using the metadata in the XMLs
to create the file structure
"""

rootpath = "./PITXML/PITXML/"
lastUpdatedDates = dict()
strings = dict()
with open('strings.json') as f:
	strings = json.load(f)

for doc in docs.keys():
	for lang in docs[doc].keys():
		pathtype = ''
		code = docs[doc][lang]['code']
		code = code.replace(' ', '_')
		code = code.replace('/', '-')
		actType = docs[doc][lang]['type']
		if actType == 'act':
			if lang == 'en': pathtype = 'acts/'
			elif lang == 'fr': pathtype = 'lois/'
		elif actType == 'regulation':
			if lang == 'en': pathtype = 'regulations/'
			elif lang == 'fr': pathtype = 'reglements/'

		dirs = sorted(os.listdir(rootpath + pathtype + code))
		for date in dirs:
			soup = None
			with open(os.path.join(rootpath, pathtype, code, date, code + '.xml')) as xmlfp:
				print("Generating markdown for law " + code + " at " + date + " ("+lang+")")
				soup = BeautifulSoup(xmlfp, features='lxml')
			if soup is None:
				print("Soup is null!")
				continue

			outfilepathNoPrefix = os.path.join(lang, strings[actType+'s'][lang])
			outfilepath = os.path.join('docs', outfilepathNoPrefix)
			if actType == 'act':
				statute = soup.statute
				identification = ParseXMLIdentification(statute, lang, outfilepathNoPrefix, docs[doc][lang]['code'], docs[doc][lang]['code'])
				docs[doc][lang]['filelink'] = identification['filepath']
				GenerateMdFile(statute, identification, os.path.join('docs', identification['filepath']), docs, doc, lang)

				print("-> Finished generating markdown. Committing changes to Git.")
				gitTimestamp = datetime.combine(datetime.strptime(str(date), '%Y%m%d').date(), noonTime)
				os.environ["GIT_AUTHOR_DATE"] = str(gitTimestamp)
				os.environ["GIT_COMMITTER_DATE"] = str(gitTimestamp)
				repo.index.add([os.path.join(identification['filepath'])])
				if identification['isNew']:
					repo.index.commit(strings['commits_act_new'][lang]+doc, author=gitAuthor, committer=gitCommitter)
				else: repo.index.commit(strings['commits_act_update'][lang]+doc, author=gitAuthor, committer=gitCommitter)

			elif actType == 'regulation':
				regulation = soup.regulation
				identification = ParseXMLIdentification(regulation, lang, outfilepathNoPrefix, docs[doc][lang]['code'], docs[doc][lang]['olLink'])
				docs[doc][lang]['filelink'] = identification['filepath']
				GenerateMdFile(regulation, identification, os.path.join('docs', identification['filepath']), docs, doc, lang)
				
				print("-> Finished generating markdown. Committing changes to Git.")
				gitTimestamp = datetime.combine(datetime.strptime(str(date), '%Y%m%d').date(), noonTime)
				os.environ["GIT_AUTHOR_DATE"] = str(gitTimestamp)
				os.environ["GIT_COMMITTER_DATE"] = str(gitTimestamp)
				repo.index.add([os.path.join(identification['filepath'])])
				if identification['isNew'] == True:
					repo.index.commit(strings['commits_reg_new'][lang]+doc, author=gitAuthor, committer=gitCommitter)
				else: repo.index.commit(strings['commits_reg_update'][lang]+doc, author=gitAuthor, committer=gitCommitter)

			print("-> Finished!")

# with open('docs.json', 'w') as docsOut:
# 	json.dump(docs, docsOut)
