#-*- coding: utf-8 -*-
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1,str_value
from pdfminer.utils import PDFDocEncoding

def getMetadataPDF():
    if doc and doc.catalog and 'Metadata' in doc.catalog:
    	return resolve1(doc.catalog['Metadata']).get_data()
    else: return None


def getFormFields(form):
	if (form==None or not 'Fields' in form) : return None

class PDF(object):
	pdfDoc = None
	pageCount = -1
	_unknownTitle = 0;
	
	def __init__(self, pdfFilename):
		fp = open(pdfFilename, 'rb')
		parser = PDFParser(fp)
		self.pdfDoc = PDFDocument(parser)

	def getMetadataPDF(self):
	    if self.pdfDoc and self.pdfDoc.catalog and 'Metadata' in self.pdfDoc.catalog:
	    	return resolve1(self.pdfDoc.catalog['Metadata']).get_data()
	    else: return None

	def getPagesNum(self):
		if self.pdfDoc and self.pdfDoc.catalog and 'Pages' in self.pdfDoc.catalog:
			self.pageCount = int(resolve1(self.pdfDoc.catalog['Pages'])['Count']);
		else: 
			self.pageCount = -1;
		return self.pageCount

	def __decode_text(self,s):
		if s.startswith(b'\xfe\xff'):
			return s[2:].decode('utf-16be', 'ignore')
		else:
			s = s.decode(encoding='UTF-8')
			return ''.join(PDFDocEncoding[ord(str(c))] for c in s)


	def __getPages(self):
		return PDFPage.create_pages(self.pdfDoc);


	def __decodeAnnots(self, annots):
		self._unknownTitle = 0;	
		for index,a in enumerate(annots):

			if type(a).__name__ != 'PDFObjRef': continue;
			a = resolve1(a);

			if ('Compression' in a):
				if (a['Compression']==12): a=str(a).encode("x/1244");
				elif (a['Compression']==17): a=str(a).encode("x/1211");
				elif (a['Compression']==10): a=str(a).encode("x/101");
		
			#print resolve1(a)
			transformedAnnot = self.__analyseAnnot( a );
			if (transformedAnnot != None): 
				annots[index] = transformedAnnot;
				annots[index]['id'] = index+1;
			else: del annots[index];

			
			
			#print resolve1(annots[index]);
			#print " ";

	def __analyseAnnot(self, annot):
		
		_title = None;
		_type = None;
		idParent = None;
		suppAttr = {};

		if ('FT' in annot): 
			_type = annot['FT'].name
		else: 
			_type = "unknown";
			if ('Parent' in annot):
				idParent = int(''.join([str(s) for s in str(annot['Parent']) if s.isdigit()]))
				_parent = resolve1(annot['Parent']);
				if ('FT' in _parent): _type = _parent['FT'].name;
				if ('T' in _parent): _title = _parent['T'].decode(encoding='UTF-8');#decode_text( _parent['T'] );

		if ('T' in annot): _title = annot['T'].decode(encoding='UTF-8')
		elif _title==None: 
			self._unknownTitle+=1
			_title = "unknown title " + str(self._unknownTitle);

		if (_type=='Btn'):
		 	if(idParent!=None):
		 		_type="radio";
		 		suppAttr['group'] = idParent;
		 	elif ('AS' in annot):
		 		_type="checkbox";
		 	else:
		 		_type="button";
		
		if (_type=='Tx'):
			_type = "text"
			if ('Q' in annot):
				Q = int(annot['Q'])
				if (Q==1):  suppAttr['align'] = 'center'
				elif (Q==2): suppAttr['align'] = 'right'	

		if ('AA' in annot):
			AA = annot['AA']
			if ('F' in AA):
				format = resolve1(annot['AA']['F']);
				if ('JS' in format):
					if ('AFNumber_Format(' in format['JS']):
						suppAttr['format'] = 'numberonly';
						suppAttr['decimal'] = int(format['JS'][16: format['JS'].index(',')])
			
			# @TODO : gérer des validations numérique (from 5 to 10 ? max/min etc.)
			#if (AA.has_key('V')):
				#print resolve1(annot['AA']['V']); # {'JS': 'AFRange_Validate(true, 5, true, 10);'}

		if (_type=='Ch' and ('Opt' in annot) ):
			_type='multichoice';
			suppAttr['choices'] = [ self.__decode_text(o) for o in annot['Opt']];

		if ('MaxLen' in annot): 
			suppAttr['maxchar'] = int(annot['MaxLen']);

		copySuppAttr = suppAttr.copy();
		r = { 'type': _type, 'title': _title, 'rectangle': annot['Rect'] }
		r.update(copySuppAttr);

		if (r['type']=='unknown'): return None;
		else: return r


	def getAllAnnots(self):
		annots = []
		pages = self.__getPages();
		for p in pages:
			if (p.annots): annots += resolve1(p.annots);
		
		#annots = annots[0:10] #[ annots[5] ]
		self.__decodeAnnots(annots)
		return annots;

