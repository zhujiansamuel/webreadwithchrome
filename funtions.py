import string, random
import nltk
import MeCab

import unicodedata

#import CaboCha
import xmltodict
from operator import itemgetter

import pandas as pd

import _pickle as cPickle
from pathlib import Path
import spacy
import en_core_web_sm

nlp = en_core_web_sm.load()
#nlp = spacy.load('en_core_web_sm')
from gensim.scripts.glove2word2vec import glove2word2vec
from gensim.models import KeyedVectors





def generate_key(lenght):
    letter = string.ascii_letters
    return ''.join(random.choice(letter) for i in range(lenght))

#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------
class ParseDocument(object):
    def __init__(self, doc, wikilinks):
        self.doc = doc
        self.wikilinks = wikilinks  # wikipediaリンクのリスト

    def wikilink_check(self, sent):
        wikilink_validity = False
        for wikilink in self.wikilinks:
            if wikilink in sent:
                wikilink_validity = True
        return wikilink_validity

    def sentence_chunking(self, sent):
        grammar = r"""
            NP: {<DT|JJ|NN.*>+}
            NP: {<NP><RB|VBN|PP|PPTO>+}
            PP: {<IN><NP>}
            VP: {<VB.*><NP|PP|RB|CLAUSE>+$}
            CLAUSE: {<NP><VP>}
            PPTO: {<TO><NP>}
            QUIZ: {<NP><QUIZV>}
            QUIZV: {<VBZ|VBD> | <VBZ|VBD><PP>}
            """
        chunk_parser = nltk.RegexpParser(grammar, loop=2)
        sent = chunk_parser.parse(sent)
        return sent

    def doc_to_sentences(self):
        sentences = nltk.sent_tokenize(self.doc)  # 文分割
        sentences = [nltk.word_tokenize(sent) for sent in sentences if self.wikilink_check(sent)]
        sentences = [nltk.pos_tag(sent) for sent in sentences]  # タグ付け
        # チャンキング(wikilinkを持っている文を対象とする)
        sentences = [self.sentence_chunking(sent) for sent in sentences]
        return sentences

    # 日本語ドキュメントをセンテンスに分割(形態素解析・句構文解析も行う)
    def doc_to_sentences_ja(self):
        # 句構文分析の規則
        grammer = '''
            NP: {<形容詞-自立.*>*<名詞.*>+ | <記号.*>*}
            NP: {<NP>*<助詞-連体化><NP>*}
            VP: {<動詞.*>*<助動詞-*>*}
            VP: {<NP>+<VP>+ | <NP>+<動詞.*>}
            SHUKAKU: {<NP>+<助詞-格助詞-ガ> | <NP>+<助詞-格助詞-ハ> | <NP>+<助詞-係助詞>}
            MOKUTEKIKAKU: {<NP>+<助詞-格助詞-ニ> | <NP>+<助詞-格助詞-ヲ>}
            QUIZ: {<SHUKAKU>+<MOKUTEKIKAKU>*<VP>}
                  '''

        sentences = self.doc.split('。')
        mecab = MeCab.Tagger('-Ochasen')
        cp = nltk.RegexpParser(grammer, loop=2)

        # 句構文リストのセット
        cp_text_list = []
        for sentence in sentences:
            # 解析結果をリスト化
            parse_result = mecab.parse(sentence)
            parse_result = parse_result.split('\n')
            parse_result = [result.split('\t') for result in parse_result]

            # 句構文解析を行う
            cp_text = []
            for pr_node in parse_result:
                # 読みがEOSであるときの処理
                if pr_node[0] == 'EOS':
                    cp_tuple = ('EOS', '*')
                    cp_text.append(cp_tuple)
                    break
                # 解析結果の情報整理
                yomi = pr_node[0]  # 品詞の表層系
                attr = ('-').join(pr_node[3].split('-')[:2])  # 品詞情報
                # 品詞発音情報
                attr_h = pr_node[1]
                # 格助詞であれば、発音情報も取り入れる
                if attr == '助詞-格助詞':
                    attr = attr + '-' + attr_h
                if attr == '助詞-格助詞':
                    attr = attr + '-' + attr_h
                cp_tuple = (yomi, attr)
                cp_text.append(cp_tuple)
            #print(cp.parse(cp_text))
            # 各文の解析結果をリストに入れる
            cp_text_list.append(cp.parse(cp_text))
        return cp_text_list[1:]

    # センテンスリストから問題文形式とマッチする文を抽出する
    def sentence_select(self, sentlist):
        # sentence treeからQUIZチャンクタグを含むものを選択する
        quiz_stem = []
        for sent in sentlist:
            for subtree in sent.subtrees():
                if subtree.label() == 'QUIZ':
                    quiz_sent_add = [word for word, tag in sent.leaves()]
                    quiz_sent_add = " ".join(quiz_sent_add[:-1])
                    quiz_stem.append(quiz_sent_add)
        # 問題文の数が５個よりも多い場合に、リストからランダムに選択
        if len(quiz_stem) > 5:
            random.shuffle(quiz_stem)
            quiz_stem = quiz_stem[0:5]
        return quiz_stem

    # 日本語センテンスリストから問題文形式とマッチする文を抽出
    def sentence_select_ja(self, sentlist):
        # sentence treeからQUIZチャンクタグを含むものを選択する
        quiz_stem = []
        for sent in sentlist:
            if isinstance(sent, tuple):
                continue
            for subtree in sent.subtrees():
                if subtree.label() == 'QUIZ':
                    quiz_sent_add = [word for word, tag in sent.leaves()]
                    quiz_sent_add = ''.join(quiz_sent_add[:-1])
                    quiz_stem.append(quiz_sent_add)
        # 問題文の数が５個よりも多い場合に、リストからランダムに選択
        if len(quiz_stem) > 5:
            random.shuffle(quiz_stem)
            quiz_stem = quiz_stem[0:5]

        return quiz_stem

    # stemからcorrectkeyをランダムに選択
    def correct_key_select(self, stem):
        # wikilinksからstemにあるキーワードをまとめる
        keywords = []
        for wikilink in self.wikilinks:
            if wikilink == '':
                continue
            if wikilink in stem:
                keywords.append(wikilink)
        # keywordsからランダムにcorrect_keyを選択

        if len(keywords) == 0:
            correct_key = ""
            is_have = False
        elif len(keywords) == 1:
            correct_key, = keywords
            is_have = True
        else:
            correct_key = keywords[random.randint(0, len(keywords) - 1)]
            is_have = True

        return correct_key,is_have

    # stemリストからcorrect keyと空所補充問題の生成
    def stem_key_select(self, stemlist):
        stem_key_list = []
        for stem in stemlist:
            # 各stemからcorrect keyを選択
            correct_key, is_have = self.correct_key_select(stem)
            if is_have:
                # stemからcorrect_keyに対応するキーワードを空欄化
                stem = stem.replace(correct_key, "( )")
                # listに追加
                stem_key_list.append({"stem": stem, "correct_key": correct_key})
        return stem_key_list



#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------

#
# glove_file = 'data/glove.6B.300d.txt'
# tmp_file = 'data/word2vec-glove.6B.300d.txt'
#
# glove2word2vec(glove_file, tmp_file)
# model = KeyedVectors.load_word2vec_format(tmp_file)
#
# def dumpPickle(fileName, content):
#     pickleFile = open(fileName, 'wb')
#     cPickle.dump(content, pickleFile, -1)
#     pickleFile.close()
#
#
# def loadPickle(fileName):
#     file = open(fileName, 'rb')
#     content = cPickle.load(file)
#     file.close()
#     return content
#
#
# def pickleExists(fileName):
#     file = Path(fileName)
#     if file.is_file():
#         return True
#     return False
#
#
# def extractAnswers(qas, doc):
#     answers = []
#     senStart = 0
#     senId = 0
#     for sentence in doc.sents:
#         senLen = len(sentence.text)
#         for answer in qas:
#             answerStart = answer['answers'][0]['answer_start']
#             if (answerStart >= senStart and answerStart < (senStart + senLen)):
#                 answers.append({'sentenceId': senId, 'text': answer['answers'][0]['text']})
#         senStart += senLen
#         senId += 1
#     return answers
#
#
# def tokenIsAnswer(token, sentenceId, answers):
#     for i in range(len(answers)):
#         if (answers[i]['sentenceId'] == sentenceId):
#             if (answers[i]['text'] == token):
#                 return True
#     return False
#
#
# def getNEStartIndexs(doc):
#     neStarts = {}
#     for ne in doc.ents:
#         neStarts[ne.start] = ne
#     return neStarts
#
#
# def getSentenceStartIndexes(doc):
#     senStarts = []
#     for sentence in doc.sents:
#         senStarts.append(sentence[0].i)
#     return senStarts
#
#
# def getSentenceForWordPosition(wordPos, senStarts):
#     for i in range(1, len(senStarts)):
#         if (wordPos < senStarts[i]):
#             return i - 1
#
#
# def addWordsForParagrapgh(newWords, text):
#     doc = nlp(text)
#     neStarts = getNEStartIndexs(doc)
#     senStarts = getSentenceStartIndexes(doc)
#     i = 0
#     while (i < len(doc)):
#         if (i in neStarts):
#             word = neStarts[i]
#             currentSentence = getSentenceForWordPosition(word.start, senStarts)
#             wordLen = word.end - word.start
#             shape = ''
#             for wordIndex in range(word.start, word.end):
#                 shape += (' ' + doc[wordIndex].shape_)
#             newWords.append([word.text, 0, 0, currentSentence, wordLen, word.label_, None, None, None, shape])
#             i = neStarts[i].end - 1
#         else:
#             if (doc[i].is_stop == False and doc[i].is_alpha == True):
#                 word = doc[i]
#                 currentSentence = getSentenceForWordPosition(i, senStarts)
#                 wordLen = 1
#                 newWords.append(
#                     [word.text, 0, 0, currentSentence, wordLen, None, word.pos_, word.tag_, word.dep_, word.shape_])
#         i += 1
#
#
# def oneHotEncodeColumns(df):
#     columnsToEncode = ['NER', 'POS', "TAG", 'DEP']
#     for column in columnsToEncode:
#         one_hot = pd.get_dummies(df[column])
#         one_hot = one_hot.add_prefix(column + '_')
#         df = df.drop(column, axis=1)
#         df = df.join(one_hot)
#     return df
#
#
# def generateDf(text):
#     words = []
#     addWordsForParagrapgh(words, text)
#     wordColums = ['text', 'titleId', 'paragrapghId', 'sentenceId', 'wordCount', 'NER', 'POS', 'TAG', 'DEP', 'shape']
#     df = pd.DataFrame(words, columns=wordColums)
#     return df
#
#
# def prepareDf(df):
#     wordsDf = oneHotEncodeColumns(df)
#     columnsToDrop = ['text', 'titleId', 'paragrapghId', 'sentenceId', 'shape']
#     wordsDf = wordsDf.drop(columnsToDrop, axis=1)
#     predictorColumns = ['wordCount', 'NER_CARDINAL', 'NER_DATE', 'NER_EVENT', 'NER_FAC', 'NER_GPE', 'NER_LANGUAGE',
#                         'NER_LAW', 'NER_LOC', 'NER_MONEY', 'NER_NORP', 'NER_ORDINAL', 'NER_ORG', 'NER_PERCENT',
#                         'NER_PERSON', 'NER_PRODUCT', 'NER_QUANTITY', 'NER_TIME', 'NER_WORK_OF_ART', 'POS_ADJ',
#                         'POS_ADP', 'POS_ADV', 'POS_CCONJ', 'POS_DET', 'POS_INTJ', 'POS_NOUN', 'POS_NUM', 'POS_PART',
#                         'POS_PRON', 'POS_PROPN', 'POS_PUNCT', 'POS_SYM', 'POS_VERB', 'POS_X', 'TAG_''', 'TAG_-LRB-',
#                         'TAG_.', 'TAG_ADD', 'TAG_AFX', 'TAG_CC', 'TAG_CD', 'TAG_DT', 'TAG_EX', 'TAG_FW', 'TAG_IN',
#                         'TAG_JJ', 'TAG_JJR', 'TAG_JJS', 'TAG_LS', 'TAG_MD', 'TAG_NFP', 'TAG_NN', 'TAG_NNP', 'TAG_NNPS',
#                         'TAG_NNS', 'TAG_PDT', 'TAG_POS', 'TAG_PRP', 'TAG_PRP$', 'TAG_RB', 'TAG_RBR', 'TAG_RBS',
#                         'TAG_RP', 'TAG_SYM', 'TAG_TO', 'TAG_UH', 'TAG_VB', 'TAG_VBD', 'TAG_VBG', 'TAG_VBN', 'TAG_VBP',
#                         'TAG_VBZ', 'TAG_WDT', 'TAG_WP', 'TAG_WRB', 'TAG_XX', 'DEP_ROOT', 'DEP_acl', 'DEP_acomp',
#                         'DEP_advcl', 'DEP_advmod', 'DEP_agent', 'DEP_amod', 'DEP_appos', 'DEP_attr', 'DEP_aux',
#                         'DEP_auxpass', 'DEP_case', 'DEP_cc', 'DEP_ccomp', 'DEP_compound', 'DEP_conj', 'DEP_csubj',
#                         'DEP_csubjpass', 'DEP_dative', 'DEP_dep', 'DEP_det', 'DEP_dobj', 'DEP_expl', 'DEP_intj',
#                         'DEP_mark', 'DEP_meta', 'DEP_neg', 'DEP_nmod', 'DEP_npadvmod', 'DEP_nsubj', 'DEP_nsubjpass',
#                         'DEP_nummod', 'DEP_oprd', 'DEP_parataxis', 'DEP_pcomp', 'DEP_pobj', 'DEP_poss', 'DEP_preconj',
#                         'DEP_predet', 'DEP_prep', 'DEP_prt', 'DEP_punct', 'DEP_quantmod', 'DEP_relcl', 'DEP_xcomp']
#     for feature in predictorColumns:
#         if feature not in wordsDf.columns:
#             wordsDf[feature] = 0
#     return wordsDf
#
#
# def predictWords(wordsDf, df):
#     predictorPickleName = 'data/nb-predictor.pkl'
#     predictor = loadPickle(predictorPickleName)
#     y_pred = predictor.predict_proba(wordsDf)
#     labeledAnswers = []
#     for i in range(len(y_pred)):
#         labeledAnswers.append({'word': df.iloc[i]['text'], 'prob': y_pred[i][0]})
#     return labeledAnswers
#
#
# def blankAnswer(firstTokenIndex, lastTokenIndex, sentStart, sentEnd, doc):
#     leftPartStart = doc[sentStart].idx
#     leftPartEnd = doc[firstTokenIndex].idx
#     rightPartStart = doc[lastTokenIndex].idx + len(doc[lastTokenIndex])
#     rightPartEnd = doc[sentEnd - 1].idx + len(doc[sentEnd - 1])
#     question = doc.text[leftPartStart:leftPartEnd] + '_____' + doc.text[rightPartStart:rightPartEnd]
#     return question
#
#
# def addQuestions(answers, text):
#     doc = nlp(text)
#     currAnswerIndex = 0
#     qaPair = []
#     for sent in doc.sents:
#         for token in sent:
#             if currAnswerIndex >= len(answers):
#                 break
#             answerDoc = nlp(answers[currAnswerIndex]['word'])
#             answerIsFound = True
#             for j in range(len(answerDoc)):
#                 if token.i + j >= len(doc) or doc[token.i + j].text != answerDoc[j].text:
#                     answerIsFound = False
#             if answerIsFound:
#                 question = blankAnswer(token.i, token.i + len(answerDoc) - 1, sent.start, sent.end, doc)
#                 qaPair.append({'question': question, 'answer': answers[currAnswerIndex]['word'],
#                                'prob': answers[currAnswerIndex]['prob']})
#                 currAnswerIndex += 1
#     return qaPair
#
#
# def sortAnswers(qaPairs):
#     orderedQaPairs = sorted(qaPairs, key=lambda qaPair: qaPair['prob'])
#     return orderedQaPairs
#
#
# def generate_distractors(answer, count):
#     answer = str.lower(answer)
#     try:
#         closestWords = model.most_similar(positive=[answer], topn=count)
#     except:
#         return []
#     distractors = list(map(lambda x: x[0], closestWords))[0:count]
#     return distractors
#
#
# def addDistractors(qaPairs, count):
#     for qaPair in qaPairs:
#         distractors = generate_distractors(qaPair['answer'], count)
#         qaPair['distractors'] = distractors
#     return qaPairs
#
#
# def generateQuestions(text, count):
#     df = generateDf(text)
#     wordsDf = prepareDf(df)
#     labeledAnswers = predictWords(wordsDf, df)
#     qaPairs = addQuestions(labeledAnswers, text)
#     orderedQaPairs = sortAnswers(qaPairs)
#     questions = addDistractors(orderedQaPairs[:count], 4)
#     return questions
#

#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------



jpn_stop_words = ["あそこ","あっ","あの","あのかた","あの人","あり","あります","ある","あれ","い","いう","います","いる","う","うち","え","お","および","おり","おります","か","かつて","から","が","き","ここ","こちら","こと","この","これ","これら","さ","さらに","し","しかし","する","ず","せ","せる","そこ","そして","その","その他","その後","それ","それぞれ","それで","た","ただし","たち","ため","たり","だ","だっ","だれ","つ","て","で","でき","できる","です","では","でも","と","という","といった","とき","ところ","として","とともに","とも","と共に","どこ","どの","な","ない","なお","なかっ","ながら","なく","なっ","など","なに","なら","なり","なる","なん","に","において","における","について","にて","によって","により","による","に対して","に対する","に関する","の","ので","のみ","は","ば","へ","ほか","ほとんど","ほど","ます","また","または","まで","も","もの","ものの","や","よう","より","ら","られ","られる","れ","れる","を","ん","何","及び","彼","彼女","我々","特に","私","私達","貴方","貴方方"]





class Rake:
    def __init__(self):
        self.tagger = MeCab.Tagger("-Owakati")

    def remove_punctuation(self, text):
        text = unicodedata.normalize("NFKC", text)  # 全角記号をざっくり半角へ置換（でも不完全）
        # 記号を消し去るための魔法のテーブル作成
        table = str.maketrans("", "", string.punctuation + "「」、。・※" + string.digits)
        text = text.translate(table)

        return text

    def get_word_score(self, word_list):
        freq = {}
        deg = {}

        for word in word_list:
            freq[word] = (freq.get(word) or 0) + 1
            deg[word] = (deg.get(word) or 0) + len(
                word) - 1  # word length must be > 1 to be considered as a Japanese 'word'

        scores = {}
        for word in word_list:
            scores[word] = deg[word] / freq[word]

        scores = {k: v for k, v in sorted(scores.items(), key=lambda item: item[1], reverse=True)}

        return scores

    def get_keywords(self, text, limit=0):
        parsed_text = self.tagger.parse(text)
        raw_word_list = self.remove_punctuation(parsed_text).split()
        word_list = [word for word in raw_word_list if word not in jpn_stop_words]

        score_list = self.get_word_score(word_list)

        if limit == 0:
            return list(score_list.keys())
        else:
            return list(score_list.keys())[:limit]

