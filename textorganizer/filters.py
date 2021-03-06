import re
from lucene import *

## Here is the code for the EnglishPossessiveFilter in Java.

# 29public final class EnglishPossessiveFilter extends TokenFilter {
# 30  private final CharTermAttribute termAtt = addAttribute(CharTermAttribute.class);
# 31
# 32  public EnglishPossessiveFilter(TokenStream input) {
# 33    super(input);
# 34  }
# 35
# 36  @Override
# 37  public boolean incrementToken() throws IOException {
# 38    if (!input.incrementToken()) {
# 39      return false;
# 40    }
# 41    
# 42    final char[] buffer = termAtt.buffer();
# 43    final int bufferLength = termAtt.length();
# 44    
# 45    if (bufferLength >= 2 &&
# 46        buffer[bufferLength-2] == '\'' &&
# 47        (buffer[bufferLength-1] == 's' || buffer[bufferLength-1] == 'S'))
# 48      termAtt.setLength(bufferLength - 2); // Strip last 2 characters off
# 49
# 50    return true;
# 51  }
# 52}

class EnglishPossessiveFilterHC(PythonTokenFilter):

    def __init__(self, tokenStream):

        super(EnglishPossessiveFilterHC, self).__init__(tokenStream)

        self.input = tokenStream

    def next(self):

        for token in self.input:
            mytoken = token.termText()
            m = re.search("'[sS]$",mytoken)
            if m:
                token.setTermBuffer(mytoken[0:m.start()])
                return token
            else:
                return token

        return None

            
class PositionalStopFilter(PythonTokenFilter):

    def __init__(self, tokenStream, stopWords):

        super(PositionalStopFilter, self).__init__(tokenStream)

        self.input = tokenStream
        self.stopWords = stopWords

    def next(self):

        increment = 0

        for token in self.input:
            if not token.termText() in self.stopWords:
                token.setPositionIncrement(token.getPositionIncrement() +
                                           increment)
                return token

            increment += 1

        return None



class NumericFilter(PythonTokenFilter):
    '''
    NumericFilter is a TokenFilter that removes any tokens
    containing numbers.
    '''

    def __init__(self, in_stream):
        PythonTokenFilter.__init__(self, in_stream)
        term = self.term = self.addAttribute(TermAttribute.class_)
        # Get tokens.
        tokens = []
        while in_stream.incrementToken():
            tokens.append(term.term())
        # Filter tokens.
        self.tokens = self.filter(tokens)
        # Setup iterator.
        self.iter = iter(self.tokens)

    def filter(self, tokens):
        final = []
        for token in tokens:
            if not re.search('\d',token):
                final.append(token)
                continue
        return final
        
    def incrementToken(self):
        try:
            self.term.setTermBuffer(next(self.iter))
        except StopIteration:
            return False
        return True

class PunctuationFilter(PythonTokenFilter):
    '''
    PunctuationFilter is a TokenFilter that removes punctuation and
    anything following an apostrophe.
    '''
    
    def __init__(self, in_stream):
        PythonTokenFilter.__init__(self, in_stream)
        term = self.term = self.addAttribute(TermAttribute.class_)
        # Get tokens.
        tokens = []
        while in_stream.incrementToken():
            tokens.append(term.term())
        # Filter tokens.
        self.tokens = self.filter(tokens)
        # Setup iterator.
        self.iter = iter(self.tokens)

    def filter(self, tokens):
        final = []
        for token in tokens:
            token = re.split("[']",token)[0]
            for t in re.split('[^\w]',token):
                final.append(t)
                continue
        return final
        
    def incrementToken(self):
        try:
            self.term.setTermBuffer(next(self.iter))
        except StopIteration:
            return False
        return True

class PhraseFilter(PythonTokenFilter):
    '''
    PhraseFilter is a TokenFilter that adds in phrases (as tokens) that match
    user-defined phrases.  You can then use these tokens when exporting a TDM.
    '''
    TOKEN_TYPE_SYNONYM = "SYNONYM"
    TOKEN_TYPE_PHRASE = "PHRASE"

    def __init__(self, inStream,allPhrases):
        super(PhraseFilter, self).__init__(inStream)

        self.synonymStack = []
        self.termAttr = self.addAttribute(TermAttribute.class_)
        self.save = inStream.cloneAttributes()
        self.inStream = inStream

        revSplitPhrases = []
        for p in allPhrases:
            psplit = p.split()
            psplit.reverse()
            revSplitPhrases.append(psplit)

        self.allPhrases = revSplitPhrases
        self.lag1 = ""
        self.lag2 = ""
        self.phraseStack = []

    def incrementToken(self):

        if len(self.phraseStack) > 0:
            syn = self.phraseStack.pop()
            self.restoreState(syn)
            return True

        if not self.inStream.incrementToken():
            return False
        
        for phrase in self.allPhrases:
            addPhrase = False
            lag0 = self.termAttr.term()
            # print "checking: ", self.termAttr.term()
            # print phrase
            if len(phrase)==2:
                if self.lag1==phrase[1] and lag0==phrase[0]:
                    addPhrase = True
            if len(phrase)==3:
                if self.lag2==phrase[2] and self.lag1==phrase[1] and lag0==phrase[0]:
                    addPhrase = True
            if addPhrase:
                rPhrase = phrase
                rPhrase.reverse()
                self.addPhrase(" ".join(rPhrase))

        self.lag2 = self.lag1
        self.lag1 = self.termAttr.term()
        
        # print "lag1: ", self.lag1
        # print "lag2: ", self.lag2

        return True

    def addPhrase(self,arg):

        # print "adding phrase", arg
        current = self.captureState()

        self.save.restoreState(current)
        AnalyzerUtils.setTerm(self.save, arg)
        AnalyzerUtils.setType(self.save, self.TOKEN_TYPE_PHRASE)
        AnalyzerUtils.setPositionIncrement(self.save, 0)
        self.phraseStack.append(self.save.captureState())

        
