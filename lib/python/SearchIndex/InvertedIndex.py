#!/usr/local/bin/python 
# $What$

__doc__='''Simple Inverted Indexer

This module provides simple tools for creating and maintaining 
inverted indexes.  An inverted index indexes a collection of
objects on words in their textual representation.

Example usage:

    d = { 
          'and'     : None,
          'or'      : None,
          'not'     : None,
          'running' : 'run',
        }

    doc = open('/usr/users/chris/doc.txt', 'r').read()
    key = '/usr/users/chris/doc.txt'

    # instantiate an Index object, passing it a dictionary
    # containing stopwords and stems
    i = InvertedIndex.Index(d)

    # index the document, doc, with key, key.
    i.index(doc, key)

    # perform a test search
    print i['blah']

      
$Id: InvertedIndex.py,v 1.14 1997/02/19 16:37:39 chris Exp $'''
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
# $Log: InvertedIndex.py,v $
# Revision 1.14  1997/02/19 16:37:39  chris
# Removed Transactional and Persistent classes
#
# Revision 1.13  1997/02/13 17:28:32  chris
# *** empty log message ***
#
# Revision 1.12  1997/02/12 18:35:21  cici
# added apply() to Transactional and Persistent addentry() methods.
#
# Revision 1.11  1997/02/12 18:11:54  cici
# *** empty log message ***
#
# Revision 1.10  1997/01/29 16:48:40  chris
# added list_class argument to Index __init__
#
# Revision 1.9  1996/12/23 21:54:10  chris
# Checked out by Chris for testing/editing.
#
# Revision 1.8  1996/12/13 13:53:11  jim
# Checked in so I could edit.
#
# Revision 1.7  1996/12/10 21:17:57  chris
# Experimenting....
#
# Revision 1.6  1996/12/09 15:50:15  jim
# Checked in so jim can hack.
#
# Revision 1.5  1996/12/03 18:15:07  chris
# Updated doc strings
#
# Revision 1.4  1996/12/03 18:11:57  chris
# Went back to returning empty ResultLists for failed searches.
#
# Revision 1.3  1996/12/03 17:44:21  chris
# Added pack() methods to Persistent and Transactional.
# Disabled autosave on Persistent.
# Failed searches now raise a KeyError rather than returning an
# empty ResultList.
#
# Revision 1.2  1996/11/18 18:50:16  chris
# Added doc strings
#
# Revision 1.1  1996/11/15 17:41:37  chris
# Initial version
#
#
# 
__version__='$Revision: 1.14 $'[11:-2]


import regex, regsub, string, SingleThreadedTransaction, copy

from types import *

class ResultList:
  '''\
  This object holds the information for a word in an inverted index.  It
  provides mapping behavior, mapping document keys to corresponding
  document information, including the frequency value.

  Union of two ResultList objects may be performed with the | operator.

  Intersection of two ResultList objects may be performed with the & operator.

  Other methods:

    Not()
    near()
    keys()
    items()
    sorted_items()
  '''

  def __init__(self, d = None):
      self._dict = d or {}


  def addentry(self, document_key, *info):
    '''\
       addentry(document_key, *info)
       add a document and related information to this ResultList'''
    self._dict[document_key] = info


  def __str__(self):
    return `self._dict`


  def __len__(self):
    return len(self._dict)


  def __getitem__(self, key):
    return self._dict[key]


  def __delitem__(self, key):
    del self._dict[key]

  
  def keys(self):
    '''\
       keys()
       get the documents in this ResultList'''
    return self._dict.keys()


  def has_key(self, key):
    return self._dict.has_key(key)


  def items(self):
    '''items()
       get a list of document key/document information pairs'''
    return self._dict.items()


  def sorted_items(self):
    '''sorted_items()

       get a 
    Sort the frequency/key pairs in the ResultList by highest to lowest
    frequency'''

    items = self._dict.items()
    items.sort(lambda x, y: -cmp(x[1][0], y[1][0]))
    return items


  def __and__(self, x):
    '''Allows intersection of two ResultList objects using the & operator.
       When ResultLists are combined in this way, frequencies are combined
       by calculating the geometric mean of each pair of corresponding 
       frequencies.'''

    result = {}

    for key in x.keys():
      try:
        result[key] = ( pow(self[key][0] * x[key][0], 0.5), None )
      except KeyError:
        pass

    return self.__class__(result)

  
  def __or__(self, x):
    '''Allows union of two ResultList objects using the | operator.
       When ResultLists are combined in this way, frequencies are
       combined by calculating the sum of each pair of corresponding 
       frequencies.'''

    result = {}

    for key in self.keys():
      result[key] = ( self[key][0], None )

    for key in x.keys():
      try:
        result[key] = (result[key][0] + x[key][0], None)
      except KeyError:
        result[key] = ( x[key][0], None )

    return self.__class__(result)


  def Not(self, index):
    '''\
       Not(index)
 
       Perform a "not" operation on a ResultList object.
       Not() returns the union of all ResultLists in the index that do
       not contain a link to a document that is found in "self".
       This method should be passed the Index object that returned the 
       ResultList instance.'''

    index = index._index_object
    res = None

    for key in index.keys():
      try:
        keys = index[key].keys()
      except KeyError:
        continue

      index_val = index[key]
      for key in keys:
        if (not self.has_key(key)):
          if (res):
            res = res | { key : index_val[key] }
          else:
            res = self.__class__({ key : index_val[key] })

    if (res):
      return res

    return self.__class__()


  def near(self, x, distance = 1):
    '''\
       near(rl, distance = 1)
  
       Returns a ResultList containing documents which contain'''
              
    result = {}

    for key in self.keys():
      try:
        value = x[key]
      except KeyError:
        continue

      positions1 = self[key][1]
      positions2 = value[1]

      for position1 in positions1:
        for position2 in positions2:

          if (position1 is None or position2 is None):
	    break

	  prox = position2 - position1
	  if ((prox > 0) and (prox <= distance)):
            rel = pow(self[key][0] * value[0], 0.5)

	    try:
              pos = result[key][1] + [ position2 ]
            except KeyError:
              pos = [ position2 ]

            result[key] = (rel, pos)
        else:
          continue

        break

    return self.__class__(result)


  def __getstate__(self):
    return self._dict


  def __setstate__(self, state):
    self._dict = state


RegexType = type(regex.compile(''))

IndexingError = 'InvertedIndex.IndexingError'

_default_stop_words = [
    'also', 'an', 'and', 'are', 'at', 'be', 'been', 'being', 'but', 'by',
    'can', 'cannot', 'did', 'do', 'doing', 'either', 'else', 'even', 'for',
    'from', 'get', 'got', 'had', 'has', 'have', 'he', 'her', 'hers', 'herself',
    'him', 'himself', 'his', 'if', 'in', 'it', 'its', 'me', 'my', 'myself',
    'no', 'not', 'of', 'only', 'or', 'our', 'ourselves', 'she', 'so', 'some',
    'than', 'that', 'the', 'their', 'them', 'themselves', 'then', 'there',
    'these', 'they', 'this', 'those', 'to', 'too', 'unless', 'until', 'us',
    'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while',
    'who', 'whoever', 'whom', 'whomever', 'whose', 'why', 'with', 'without',
    'would', 'yes', 'your', 'yours', 'yourself', 'yourselves',
    ]

default_stop_words = {}

for w in _default_stop_words: 
  default_stop_words[w] = None

for w in string.letters: 
  default_stop_words[w] = None


class Index(SingleThreadedTransaction.Persistent):
  '''\
  An inverted index.

  This class handles indexing and searching.

  An optional argument may be provided when instantiating
  an Index object.  This argument should be a dictionary
  specifying stems, synonyms, and stopwords.  The dictionary
  may also be used to initialize the index with previously
  indexed values.  Within the dictionary, stopwords should
  be keywords (string values) mapped to the Python value None;
  stems and synonyms should be keywords mapped to their
  corresponding keywords, and previously indexed values should
  map a keyword to a ResultList object.

  Indexing is performed using the index() method.

  Searching is performed using the Index object\'s mapping
  behaviour.  

  Example usage:

    d = { 
          'and'     : None,    # Stopword
          'or'      : None,    # Stopword
          'not'     : None,    # Stopword
          'running' : 'run',   # Stem
        }

    doc = open('/usr/users/chris/doc.txt', 'r').read()
    key = '/usr/users/chris/doc.txt'

    # instantiate an Index object, passing it a dictionary
    # containing stopwords and stems
    i = InvertedIndex.Index(d)

    # index the document, doc, with key, key.
    i.index(doc, key)

    # perform a test search
    print i['blah']
  '''

  list_class = ResultList

  def __init__(self, index_dictionary = None, list_class = None):
    'Create an inverted index'
    if (list_class is not None):
        self.list_class = list_class

    if (index_dictionary is None):
        index_dictionary = copy.copy(default_stop_words)

    self.set_index(index_dictionary)

 
  def set_index(self, index_dictionary = None):
    'Change the index dictionary for the index.'

    if (index_dictionary is None):
      index_dictionary = {}
    
    self._index_object = index_dictionary


  def split_words(self, s):
    'split a string into separate words'
    return regsub.split(s, '[^a-zA-Z]+')


  def index(self, src, srckey):
    '''\
    index(src, srckey)

    Update the index by indexing the words in src to the key, srckey

    The source object, src, will be converted to a string and the
    words in the string will be used as indexes to retrieve the objects 
    key, srckey.  For simple objects, the srckey may be the object itself,
    or it may be a key into some other data structure, such as a table.
    '''

    import math

    List = self.list_class
    index = self._index_object

    src = regsub.gsub('-[ \t]*\n[ \t]*', '', str(src)) # de-hyphenate
    src = filter(None,self.split_words(src))

    if (len(src) < 2):
      raise IndexingError, 'cannot index document with fewer than two keywords'

    nwords = math.log(len(src))

    d = {}
    for i in range(len(src)):
      s = src[i]
      s = string.lower(s)
      stopword_flag = 0

      while (not stopword_flag):
        try:
          index_val = index[s]
        except KeyError:
          break

        if (index_val is None):
	  stopword_flag = 1
	elif (type(index_val) != StringType):
          break
        else:
          s = index_val
      else:  # s is a stopword
        continue

      try:
        d[s].append(i)
      except KeyError:
        d[s] = [ i ]

    for s in d.keys():
      freq = int(10000 * (len(d[s]) / nwords))
      try:
        index[s].addentry(srckey, freq, d[s])
      except:
        index[s] = List({srckey : (freq, d[s])})


  def __getitem__(self, key):
    '''
    Get the ResultList objects for the inverted key, key.

    The key may be a regular expression, in which case a regular
    expression match is done.

    The key may be a string, in which case an case-insensitive
    match is done.
    '''

    index = self._index_object 
    List = self.list_class

    if (type(key) == RegexType):
      dict = {}
      for k in index.keys():
        if (key.search(k) >= 0):
          try:
            while (type(index[k]) == StringType):
              k = index[k]
          except KeyError:
            continue

          if (index[k] is None):
            continue

          dict[index[k]] = 1

      Lists = dict.keys()

      if (not len(Lists)):
        return List()

      return reduce(lambda x, y: x | y, Lists)

    key = string.lower(key)

    while (type(key) == StringType):
      try:
        key = index[key]
      except KeyError:
        return List()

    if (key is None):
      return List()

    return key


  def keys(self):
    return self._index_object.keys()


  def __len__(self):
    return len(self._index_object)

  
  def remove_document(self, doc_key, s = None):
    if (s is None):
      for key in self.keys():
        try:
          del self[key][doc_key]
        except:
          continue


  def get_stopwords(self):
    index = self._index_object

    stopwords = []
    for word in index.keys():
      if (index[word] is None):
        stopwords.append(word)

    return stopwords

        
  def get_synonyms(self):
    index = self._index_object

    synonyms = {}    
    for word in index.keys():
      if (type(index[word]) == StringType):
        synonyms[word] = index[word]

    return synonyms


  def get_document_keys(self):
    d = {}
    for key in self.keys():
      try:
        doc_keys = self[key].keys()
      except:
        continue

      for doc_key in doc_keys:
        d[doc_key] = 1

    return d.keys()

  
  def __getstate__(self):
    return None


  def __setstate__(self, state):
    pass


  def __getinitargs__(self):
    return (self._index_object,)


class PersistentResultList(ResultList, SingleThreadedTransaction.Persistent):

  def addentry(self, key, *info):
    '''Add a frequency/key pair to this object'''

    apply(ResultList.addentry, (self, key) + info)
    self.__changed__(1)





