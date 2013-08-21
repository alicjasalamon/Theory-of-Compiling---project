#!/usr/bin/python

import copy
import sys
import re
import os
import ply.lex as lex
import ply.yacc as yacc


################################################
#       		struktury danych               #
################################################

#tutaj laduja wszystkie strukturki po sparsowaniu
lista=[]

#tutaj laduja strukturki po sprawdzeniu 
listaPoprawnych=[]

#to jest miejsce na identyfikatory - nie moga sie powtarzac
identyfikatory=set()

#plik.html - na poprawne dane
plikPoprawne = open("result.html", "w")

#plik na wiadomosci o bledach
plikBledy = open("bledy.txt", "w")

#mozliwe kombinacje pol
mapaDanych={
'@article':(
	['author', 'title', 'journal', 'year'],
	['volume', 'number', 'pages', 'month', 'note', 'key']),
'@book':(
	['author', 'title', 'publisher', 'year'],
	['volume', 'series', 'address', 'edition', 'month', 'note', 'key']),
'@inproceedings':(
	['author', 'title', 'booktitle', 'year'],
	['editor', 'volume', 'series', 'pages', 'address', 'month', 'organization', 'publisher', 'note', 'key']),
'@booklet':(
	['title'],
	['author', 'howpublished', 'address', 'month', 'year', 'note', 'key']),
'@inbook':(
	['author', 'title', 'chapter', 'publisher', 'year'],
	['editor', 'volume', 'series', 'type', 'chapter', 'pages', 'address', 'edition', 'month', 'note', 'key']),
'@incollection':(
	['author', 'title', 'booktitle', 'publisher', 'year'],
	['editor', 'volume', 'series', 'type', 'chapter', 'pages', 'address', 'edition', 'month', 'note', 'key']),
'@manual':(
	['title'],
	['author', 'organization', 'address', 'edition', 'month', 'year', 'note', 'key']),
'@mastersthesis':(
	['author', 'title', 'school', 'year'],
	['type', 'address', 'month', 'note', 'key']),
'@phdthesis':(
	['author', 'title', 'school', 'year'],
	['type', 'address', 'month', 'note', 'key']),
'@techreport':(
	['author', 'title', 'institution', 'year'],
	['editor', 'volume', 'series', 'address', 'month', 'organization', 'publisher', 'note', 'key']),
'@misc':(
	[],
	['author', 'title', 'howpublished', 'month', 'year', 'note', 'key']),
'@unpublished':(
	['author', 'title', 'note'],
	['month', 'year', 'key'])
}

################################################
#       		tokeny i gramatyka             #
################################################

tokens = (
	'RODZAJ_PUBLIKACJI',
	'WARTOSC_W_CUDZYSLOWIE',
	'WARTOSC',
)

literals = "{},="

def t_RODZAJ_PUBLIKACJI(t):
	r'@\w*'
	t.value = (t.value, t.lexer.lineno)
	return t

def t_WARTOSC_W_CUDZYSLOWIE(t):
	r'"(\n|.)*?"'
	#usun biale znaki z lewej strony
	t.value = re.sub('"\s+', '"', t.value)
	#i z prawej 
	t.value = re.sub('\s+"', '"', t.value)
	#i w srodku
	t.value = re.sub('\s+', ' ', t.value)
	t.value = (t.value, t.lexer.lineno)	
	entery =  re.findall('\n', t.value[0])
	t.lexer.lineno += len(entery)
	return t

def t_WARTOSC(t):
	r'\w+'
	t.value = (t.value, t.lexer.lineno)
	return t

t_ignore = ' \t'

def t_newline(t):
	r'\n+'
	t.lexer.lineno += len(t.value)

def t_error(t) :
	print("blad w lekserze")
	t.lexer.skip(1)

def p_error(p) :
	print("blad w parsingu- token ", p.value[0],", nr linii ", p.lineno )

def p_publications1(p):
	"""publications : publication"""

def p_publications2(p):
	"""publications : publications publication"""

def p_publication(p):
	"""publication : type '{' WARTOSC ',' fields '}'"""
	lista.append((p[1], p[3], p[5]))

def p_fields1(p):
	"""fields : field"""
	krotka = p[1]
	p[0]=	{krotka[0].lower() : krotka[1]}

def p_fields2(p):
	"""fields : fields ',' field"""
	krotka = p[3]
	mapa = p[1]
	if krotka[0].lower() not in mapa:
		mapa[krotka[0].lower()]=krotka[1]
	else:
		plikBledy.write("powtarzajaca sie nazwa pola {} w linii {}\n".format(krotka[0].lower(), krotka[1][1]))
		
	p[0]=mapa

def p_field1(p):
	"""field : WARTOSC '=' WARTOSC_W_CUDZYSLOWIE"""
	p[0]=(p[1][0].lower(),(p[3][0][1:-1],p[1][1]))

def p_field2(p):
	"""field : WARTOSC '=' WARTOSC """
	p[0]=(p[1][0].lower(),(p[3][0],p[1][1]))

def p_type(p):
	"""type : RODZAJ_PUBLIKACJI"""
	p[0]=p[1]


################################################
#       		funkcje pomocnicze             #
################################################

def wyswietl(krotka):
	plikPoprawne.write('<p>\n')
	plikPoprawne.write('<b>{}</b>\n'.format(krotka[1][0]))
	plikPoprawne.write('<i>{}</i>\n'.format(krotka[0][0][1:].lower()))
	plikPoprawne.write('<ul>\n')
	for key, value in krotka[2].items():
		plikPoprawne.write('\t<li><i>{}</i> - {}</li>\n'.format(key, value[0]))
	plikPoprawne.write('</ul>\n')
	plikPoprawne.write('</p>\n')


def wyswietl2(krotka):
	print('<{}>'.format(krotka[0][0][1:].lower()))
	print('\t<keyword>{}</keyword>'.format(krotka[1][0]))
	for key, value in krotka[2].items():
		print('\t<{}>{}</{}>'.format(key, value[0], key))
	print('</{}>'.format(krotka[0][0][1:].lower()))
	print('\n')
	
def sprawdzKrotke(krotka):

	#krotka jest nie ok
	ok=0
		
	#sprawdzamy czy obslugujemy takie pozycje bibliograficzne
	for klucz in mapaDanych:
		if klucz == krotka[0][0].lower():
			ok =1
		 
	if ok == 0:
		plikBledy.write("niepoprawny rodzaj publikacji {} w linii {}\n".format(krotka[0][0], krotka[0][1]))
	else :
		potrzebne = copy.copy(mapaDanych[krotka[0][0].lower()][0])
		dodatkowe = copy.copy(mapaDanych[krotka[0][0].lower()][1])
		
		for klucz in krotka[2]:
			if (klucz == "year") and (krotka[2][klucz][0].isdigit()==False):
				plikBledy.write("uwaga: rok {} nie jest liczba\n".format(krotka[2][klucz][0]))
							
			if klucz in potrzebne:
				potrzebne.remove(klucz)
			elif klucz in dodatkowe :
				dodatkowe.remove(klucz)
			else:
				plikBledy.write("niepoprawny typ {} w linii {}\n".format(klucz, krotka[2][klucz][1]))	
				ok= 0
		
		if len(potrzebne)!=0:
			plikBledy.write("nie podano wymaganych pol, krotka {}\n".format(krotka[0][1]))				
			ok= 0
			
	return ok

def sprawdzIdentyfikatory(krotka):
	if krotka[1][0] in identyfikatory:
		plikBledy.write("powtorzone ID- {} w linii {}\n".format(krotka[1][0], krotka[1][1]))
		return 0
	else:
		identyfikatory.add(krotka[1][0])
		return 1

def sprawdzListe():
	for krotka in lista:
		wpisz=1
		if sprawdzIdentyfikatory(krotka) != 1 or sprawdzKrotke(krotka) != 1:
			wpisz = 0	
		if wpisz == 1:
			listaPoprawnych.append(krotka)
	
	
if len(sys.argv)==1:
	print("brak argumentow, podaj nazwe pliku/folderu!")
else:
	
	plikPoprawne.write('<html>\n')
	plikPoprawne.write('<body>\n')
	plikPoprawne.write('<head> <title> spis publikacji </title> <head>')
	plikBledy.write('BLEDY:\n')
	
		
	if os.path.isdir(sys.argv[1]):
		for dirname, dirnames, filenames in os.walk(sys.argv[1]):
			for filename in filenames:
				if (filename[-4:] == ".bib"):
					file = open(os.path.join(dirname, filename), "r")
					plikPoprawne.write('\n<h2>{}/{}</h2>'.format(dirname, filename))
					plikBledy.write('\nbledy w pliku: {}/{}\n'.format(dirname, filename)) 
					lexer = lex.lex()
					parser = yacc.yacc()
					text = file.read()
					parser.parse(text, lexer=lexer)
					sprawdzListe()	
					for krotka in listaPoprawnych:
						plikPoprawne.write("\n")
						wyswietl(krotka)
					lista=[]
					listaPoprawnych=[]
					file.close()

	
	elif os.path.isfile(sys.argv[1]):
		if (sys.argv[1][-4:] == ".bib"):
			
			file = open(sys.argv[1], "r")
			plikPoprawne.write('<h2>{}</h2>'.format(sys.argv[1]))
			plikBledy.write('\nbledy w pliku: {}\n'.format(sys.argv[1]))
			lexer = lex.lex()
			parser = yacc.yacc()
			text = file.read()
			parser.parse(text, lexer=lexer)
			sprawdzListe()	
			for krotka in listaPoprawnych:
				plikPoprawne.write("\n")
				wyswietl(krotka)
			lista=[]
			listaPoprawnych=[]
			file.close()
	
	else:
		print("podaj nazwe pliku lub katalogu")
		exit()
	
	plikPoprawne.write('</body>\n')
	plikPoprawne.write('</html>')
	print("\naby zobaczyc wyniki, otworz wygenerowany plik result.html w przegladarce")
	print("aby zobaczyc ewentualne bledy, otworz wygenerowany plik bledy.txt\n")
	

