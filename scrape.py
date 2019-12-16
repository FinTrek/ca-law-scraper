from bs4 import BeautifulSoup

with open("A-1.xml") as fp:
	soup = BeautifulSoup(fp, 'xml')


print(soup.Statute)

