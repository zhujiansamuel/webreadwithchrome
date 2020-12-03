import string, random
import nltk
import MeCab
import random

import CaboCha
import xmltodict
from operator import itemgetter

import pandas as pd
from IPython.display import Markdown, display, clear_output
import _pickle as cPickle
from pathlib import Path
import spacy

nlp = spacy.load('en_core_web_sm')
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
        mecab = MeCab.Tagger('-Ochasen -d /Users/samuelzhu/mecab/mecab-ipadic')
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








    # # correct_keyからdistracterを選択
    # def get_distracters(self, stem_key_list):
    #     # 問題文、正解、不正解の辞書リスト
    #     quiz_distracter = []
    #     # 各問題ごとに処理を行う(for)
    #     for stem_key in stem_key_list:
    #         # correct_keyのwikiページにとび、属するカテゴリを取得
    #         categories = get_category(stem_key["correct_key"])
    #         # カテゴリの数が３つよりも多い時、リストからランダムに３つ選択
    #         categories = categories[0:3]
    #         # print("<category>")
    #         # print(categories)
    #         # print("--------------------------------------------")
    #
    #         # 各カテゴリから最大3つのトピックを取得する
    #         topics = []
    #         for category in categories:
    #             topics.append(get_topic(category))
    #         topics = sum(topics, [])  # リストをflattenにする
    #         random.shuffle(topics)  # リストをランダムソート
    #         # トピックリストの数が少ないかどうかを検証
    #         if len(topics) < 3:
    #             continue
    #         # トピックのリストからランダムに３つのdistracterを取得する
    #         distracters = topics[:3]
    #         choice = [("correct_key", stem_key["correct_key"]),
    #                   ("distracter_0", distracters[0]),
    #                   ("distracter_1", distracters[1]),
    #                   ("distracter_2", distracters[2])]
    #         random.shuffle(choice)
    #         quiz_distracter.append({
    #             "stem": stem_key["stem"],
    #             # "correct_key" : stem_key["correct_key"],
    #             # "distracters" : distracters
    #             "choice": choice
    #         })
    #     return quiz_distracter
    #
    # # correct_keyからdistracterを選択
    # def get_distracters_ja(self, stem_key_list):
    #     # 問題文、正解、不正解の辞書リスト
    #     quiz_distracter = []
    #     # 各問題ごとに処理を行う(for)
    #     for stem_key in stem_key_list:
    #         # correct_keyのwikiページにとび、属するカテゴリを取得
    #         categories = get_category_ja(stem_key["correct_key"])
    #         # カテゴリの数が３つよりも多い時、リストからランダムに３つ選択
    #         if len(categories) > 3:
    #             random.shuffle(categories)
    #             categories = categories[0:3]
    #         print("<category>")
    #         print(categories)
    #         print("--------------------------------------------")
    #
    #         # 各カテゴリから最大3つのトピックを取得する
    #         topics = []
    #         for category in categories:
    #             topics.append(get_topic_ja(category))
    #         topics = sum(topics, [])  # リストをflattenにする
    #         random.shuffle(topics)  # リストをランダムソート
    #         # トピックリストの数が少ないかどうかを検証
    #         if len(topics) < 3:
    #             continue
    #         # トピックのリストからランダムに３つのdistracterを取得する
    #         distracters = topics[:3]
    #         choice = [("correct_key", stem_key["correct_key"]),
    #                   ("distracter_0", distracters[0]),
    #                   ("distracter_1", distracters[1]),
    #                   ("distracter_2", distracters[2])]
    #         random.shuffle(choice)
    #         quiz_distracter.append({
    #             "stem": stem_key["stem"],
    #             # "correct_key" : stem_key["correct_key"],
    #             # "distracters" : distracters
    #             "choice": choice
    #         })
    #
    #     return quiz_distracter
    #
    # # 問題文の表示
    # def quiz_display(self, quiz_distracter):
    #     # get_distractersで仕様が変更されているため、ここも変える必要あり
    #     for dic in quiz_distracter:
    #         print("--Question--")
    #         print(dic["stem"])
    #         for k, choice in dic["choice"]:
    #             print("%s: %s" % (k, choice))
    #         print("")
    #     return
    #
    #


#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------
class QAGeneration:
    def __init__(self):
        # 初期化
        self.parsed_sentence = None
        # extract from node_list
        self.dependencies = list()
        self.chunkid2text = dict()
        self.cabocha_parser = CaboCha.Parser("-n1")
        # self.jumanpp = Juman()
        # self.spacy_parser = spacy.load('ja_ginza_nopn')
        # list for chunks [{"deps":[chunk_link_id_list], "word":[token_name_list], "tag":[token_type_list]}]

    def _set_head_form(self, node_map):

        for chunk_id, node in node_map.items():
            tags = node["tag"]
            num_morphs = len(tags)
            # extract bhead (主辞) and bform (語形) from a chunk
            bhead = -1
            bform = -1
            for i in range(num_morphs - 1, -1, -1):
                if tags[i][0] == u"記号":
                    continue
                else:
                    if bform == -1: bform = i
                    if not (tags[i][0] == u"助詞"
                            or (tags[i][0] == u"動詞" and tags[i][1] == u"非自立")
                            or tags[i][0] == "助動詞"):
                        if bhead == -1: bhead = i

            node['bhead'] = bhead
            node['bform'] = bform

            node_map[chunk_id] = node

        return node_map

    def parse(self, doc):
        tree = self.cabocha_parser.parse(doc)
        xmlstr = tree.toString(CaboCha.FORMAT_XML)
        try:
            xml_dict = xmltodict.parse(xmlstr)
            return xml_dict, True
        except:
            return {}, False

    def _is_yogen(self, node):
        bhead_tag = node['tag'][node['bhead']]
        bform_tag = node['tag'][node['bform']]

        if bhead_tag[0] == u"動詞":
            return True, u"動詞"
        elif bhead_tag[0] == u"形容詞":
            return True, "u形容詞"
        elif bhead_tag[1] == u"形容動詞語幹":
            return True, u"形容詞"
        elif bhead_tag[0] == u"名詞" and bform_tag[0] == u"助動詞":
            return True, u"名詞_助動詞"
        else:
            return False, u""

    def _is_case(self, node):
        # 用言の直前の形態素が格かどうかを判定する
        # 格である場合は、格の直前の形態素の意味を解析する（time（7時に）かplace（公園で遊ぶ）かagent（私が動詞）か）
        bhead_tag = node['tag'][node['bhead']]
        bform_tag = node['tag'][node['bform']]
        bform_surface = bform_tag[-1]
        if (bform_tag[0] == u"助詞" and bform_tag[1] == u"格助詞"
                and (bform_surface in set([u"ガ", u"ヲ", u"ニ", u"ト", u"デ", u"カラ", u"ヨリ", u"ヘ", u"マデ"]))):

            if bhead_tag[1] == u"代名詞" \
                    or (bhead_tag[0] == u"名詞" and bhead_tag[1] == u"接尾"):
                # 代名詞かさん
                return True, "agent"
            elif bform_surface == u"ニ" and \
                    (node['ne'][node['bhead']] == u"B-DATE" or \
                     (bhead_tag[1] == u"接尾" and bhead_tag[-1] == u"ジ")):
                #  「９時に」の場合、時は時間の固有名詞として認識されないようなので、featureに「ジ」があれば時間として扱う
                # time
                return True, "time"
            elif bform_surface == u"デ" and \
                    (node['ne'][node['bhead']] == u"B-LOCATION" or bhead_tag[0] == u"名詞"):
                # place
                return True, "place"
            else:
                return True, bform_surface
        elif bhead_tag[0] == u"名詞" and bform_tag[0:2] == [u"名詞", u"接尾"]:
            return True, u"名詞接尾"
        else:
            return False, u""

    def _extract_case_frame(self, node_map):
        # 深層格解析
        for chunk_id, node in node_map.items():

            is_yogen, yogen = self._is_yogen(node)
            if is_yogen:
                for case_cand in [node_map[child_id] for child_id in node['deps']]:
                    is_case, case = self._is_case(case_cand)
                    if is_case:
                        # 格（ガ格、ヲ格、ニ格、ト格、デ格、カラ格、ヨリ格、ヘ格、マデ格、無格）＋用言（動詞、形容詞、名詞＋判定詞）形式の文節に意味役割を生成
                        # 全組み合わせに変換対応は難しいが、固定でいくつか対応します。
                        # ex. が綺麗（ガ格＋形容詞）→how is

                        meaning_label = ""

                        if case == u"ガ" and yogen == u"形容詞":
                            # 属性を持つ対象	<aobject>花</aobject>が<pred>きれい</pred>
                            meaning_label = "aobject"
                        elif case == u"agent" or case == u"time" or case == u"place":
                            meaning_label = case
                        else:
                            pass

                        # print("meaning_label", meaning_label)

                        case_cand["meaning_label"] = meaning_label
        return node_map

    def _extract_dependencies(self, jsonfile):
        print(jsonfile)
        # 解析結果(json)から係り受け情報を抽出

        chunkid2text = dict()  # (chunk_id: joined_tokens)

        # map of chunks
        node_map = {}
        for chunk in jsonfile["sentence"]["chunk"]:
            if chunk == "@id" or chunk == "@link" \
                    or chunk == "@rel" or chunk == "@score" \
                    or chunk == "@head" or chunk == "@func" or chunk == "tok":
                continue

            chunk_id = int(chunk["@id"])

            if isinstance(chunk["tok"], list):
                # #textが取れない場合があるので、取れるtokenのみからlistを作る
                tokens = [token["#text"] for token in chunk["tok"] if "#text" in token]
                tokens_feature = [token["@feature"] for token in chunk["tok"]]
                # named entity
                tokens_ne = [token["@ne"] for token in chunk["tok"]]
            else:
                if "#text" not in chunk["tok"]:
                    continue
                tokens = [chunk["tok"]["#text"]]
                tokens_feature = [chunk["tok"]["@feature"]]
                tokens_ne = [chunk["tok"]["@ne"]]
            joined_tokens = "".join(tokens)
            chunkid2text[chunk_id] = joined_tokens
            link_id = int(chunk["@link"])

            words = tokens
            tags = [feature.split(",") for feature in tokens_feature]
            nes = tokens_ne

            if chunk_id in node_map:
                deps = node_map[chunk_id]["deps"]
                node_map[chunk_id] = {"word": words, "tag": tags, "ne": nes, "deps": deps, "meaning_label": ""}
            else:
                node_map[chunk_id] = {"word": words, "tag": tags, "ne": nes, "deps": [], "meaning_label": ""}

            # 親chunkがある場合、親chunkのdeps配列にこのchunk_idを追加する
            parent_id = link_id

            if parent_id in node_map:
                parent_node = node_map[parent_id]
                parent_node["deps"].append(chunk_id)
            elif parent_id == -1:
                pass
            else:
                deps = [chunk_id]
                node_map[parent_id] = {"deps": deps}

        return chunkid2text, node_map



    def _TorF_id_in_subtree_root_id(self, id, subtree_root_id):
        checklist = [item for item in self.dependencies if item[0] == subtree_root_id]
        if id in [item[1] for item in checklist]:
            return True
        else:
            for p, c, _ in checklist:
                if c in [item[0] for item in self.dependencies]:
                    return self._TorF_id_in_subtree_root_id(id, c)
            return False



    def _get_subtree_texts(self, subtree_root_id):
        parent_ids = [item[0] for item in self.dependencies]
        if subtree_root_id not in parent_ids:
            return self.chunkid2text[subtree_root_id]
        else:
            text = ''
            for item in self.dependencies:
                if item[0] != subtree_root_id: continue
                text += self._get_subtree_texts(item[1])
            text += self.chunkid2text[subtree_root_id]
            return text



    def _merge_dependencies_and_case_meaning(self, node_map):
        # node_mapをflatなlistに変換する
        dependencies = list()  # [chunk_id, child_chunk_id, child_chunk_label]
        for chunk_id, node in node_map.items():
            for child_chunk_id in node["deps"]:
                child_chunk_label = node_map[child_chunk_id]["meaning_label"]
                dependencies.append([chunk_id, child_chunk_id, child_chunk_label])

        # dependenciesをchunk_id順でソートします。(同じchunk_idの行をまとめます)
        dependencies.sort(key=itemgetter(0))
        return dependencies




    def generate_QA(self, doc):
        # 質問を生成する
        qas = list()
        for sentence in doc.split("。"):
            if sentence == "" or sentence is None or sentence == "\n":
                continue
            self.parsed_sentence, is_succeed = self.parse(sentence)

            if not is_succeed:
                continue
            # 係り受け解析
            self.chunkid2text, node_map = self._extract_dependencies(self.parsed_sentence)
            node_map = self._set_head_form(node_map)

            # 深層格解析（文節に意味ラベルを付与する）
            node_map = self._extract_case_frame(node_map)
            self.dependencies = self._merge_dependencies_and_case_meaning(node_map)
            qas += self._agent2what_QA()
            qas += self._aobject_ha2what_QA()
            qas += self._time2when_QA()
            qas += self._place2where_QA()
        return qas



    def _agent2what_QA(self):
        question_and_answers = list()
        target_dependencies = [item for item in self.dependencies if item[2] == 'agent']
        for item in target_dependencies:
            target_id = item[1]
            q = ''
            a = ''
            for i in self.chunkid2text.keys():
                # for i in range(len(self.chunkid2text)):
                if i == target_id:
                    q += '誰が、'
                    a = self._get_subtree_texts(i)
                elif self._TorF_id_in_subtree_root_id(i, target_id):
                    continue
                else:
                    q += self.chunkid2text[i]
            q += 'か？'
            q = q.replace('。', '')
            question_and_answers.append([q, a])
        return question_and_answers



    def _aobject_ha2what_QA(self):
        question_and_answers = list()
        target_dependencies = [item for item in self.dependencies if item[2] == 'aobject' \
                               and self.chunkid2text[item[1]][-1] == 'が']
        for item in target_dependencies:
            target_id = item[1]
            q = ''
            for i in self.chunkid2text.keys():
                # for i in range(len(self.chunkid2text)):
                if i == target_id:
                    q += '何が、'
                    a = self._get_subtree_texts(i)
                elif self._TorF_id_in_subtree_root_id(i, target_id):
                    continue
                else:
                    q += self.chunkid2text[i]
            q += 'か？'
            q = q.replace('。', '')
            question_and_answers.append([q, a])
        return question_and_answers



    def _time2when_QA(self):
        question_and_answers = list()
        target_dependencies = [item for item in self.dependencies if item[2] == 'time']
        for item in target_dependencies:
            target_id = item[1]
            q = ''
            for i in self.chunkid2text.keys():
                # for i in range(len(self.chunkid2text)):
                if i == target_id:
                    q += 'いつ、'
                    a = self._get_subtree_texts(i)
                elif self._TorF_id_in_subtree_root_id(i, target_id):
                    continue
                else:
                    q += self.chunkid2text[i]
            q += 'か？'
            q = q.replace('。', '')
            question_and_answers.append([q, a])
        return question_and_answers



    def _place2where_QA(self):
        question_and_answers = list()
        target_dependencies = [item for item in self.dependencies if item[2] == 'place' \
                               and self.chunkid2text[item[1]][-1] == 'で']
        for item in target_dependencies:
            target_id = item[1]
            q = ''
            for i in self.chunkid2text.keys():
                # for i in range(len(self.chunkid2text)):
                if i == target_id:
                    q += '何処で'
                    a = self._get_subtree_texts(i)
                elif self._TorF_id_in_subtree_root_id(i, target_id):
                    continue
                else:
                    q += self.chunkid2text[i]
            q += 'か？'
            q = q.replace('。', '')
            question_and_answers.append([q, a])
        return question_and_answers




#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------
glove_file = 'data/glove.6B.300d.txt'
tmp_file = 'data/word2vec-glove.6B.300d.txt'

glove2word2vec(glove_file, tmp_file)
model = KeyedVectors.load_word2vec_format(tmp_file)

def dumpPickle(fileName, content):
    pickleFile = open(fileName, 'wb')
    cPickle.dump(content, pickleFile, -1)
    pickleFile.close()


def loadPickle(fileName):
    file = open(fileName, 'rb')
    content = cPickle.load(file)
    file.close()
    return content


def pickleExists(fileName):
    file = Path(fileName)
    if file.is_file():
        return True
    return False


def extractAnswers(qas, doc):
    answers = []
    senStart = 0
    senId = 0
    for sentence in doc.sents:
        senLen = len(sentence.text)
        for answer in qas:
            answerStart = answer['answers'][0]['answer_start']
            if (answerStart >= senStart and answerStart < (senStart + senLen)):
                answers.append({'sentenceId': senId, 'text': answer['answers'][0]['text']})
        senStart += senLen
        senId += 1
    return answers


def tokenIsAnswer(token, sentenceId, answers):
    for i in range(len(answers)):
        if (answers[i]['sentenceId'] == sentenceId):
            if (answers[i]['text'] == token):
                return True
    return False


def getNEStartIndexs(doc):
    neStarts = {}
    for ne in doc.ents:
        neStarts[ne.start] = ne
    return neStarts


def getSentenceStartIndexes(doc):
    senStarts = []
    for sentence in doc.sents:
        senStarts.append(sentence[0].i)
    return senStarts


def getSentenceForWordPosition(wordPos, senStarts):
    for i in range(1, len(senStarts)):
        if (wordPos < senStarts[i]):
            return i - 1


def addWordsForParagrapgh(newWords, text):
    doc = nlp(text)
    neStarts = getNEStartIndexs(doc)
    senStarts = getSentenceStartIndexes(doc)
    i = 0
    while (i < len(doc)):
        if (i in neStarts):
            word = neStarts[i]
            currentSentence = getSentenceForWordPosition(word.start, senStarts)
            wordLen = word.end - word.start
            shape = ''
            for wordIndex in range(word.start, word.end):
                shape += (' ' + doc[wordIndex].shape_)
            newWords.append([word.text, 0, 0, currentSentence, wordLen, word.label_, None, None, None, shape])
            i = neStarts[i].end - 1
        else:
            if (doc[i].is_stop == False and doc[i].is_alpha == True):
                word = doc[i]
                currentSentence = getSentenceForWordPosition(i, senStarts)
                wordLen = 1
                newWords.append(
                    [word.text, 0, 0, currentSentence, wordLen, None, word.pos_, word.tag_, word.dep_, word.shape_])
        i += 1


def oneHotEncodeColumns(df):
    columnsToEncode = ['NER', 'POS', "TAG", 'DEP']
    for column in columnsToEncode:
        one_hot = pd.get_dummies(df[column])
        one_hot = one_hot.add_prefix(column + '_')
        df = df.drop(column, axis=1)
        df = df.join(one_hot)
    return df


def generateDf(text):
    words = []
    addWordsForParagrapgh(words, text)
    wordColums = ['text', 'titleId', 'paragrapghId', 'sentenceId', 'wordCount', 'NER', 'POS', 'TAG', 'DEP', 'shape']
    df = pd.DataFrame(words, columns=wordColums)
    return df


def prepareDf(df):
    wordsDf = oneHotEncodeColumns(df)
    columnsToDrop = ['text', 'titleId', 'paragrapghId', 'sentenceId', 'shape']
    wordsDf = wordsDf.drop(columnsToDrop, axis=1)
    predictorColumns = ['wordCount', 'NER_CARDINAL', 'NER_DATE', 'NER_EVENT', 'NER_FAC', 'NER_GPE', 'NER_LANGUAGE',
                        'NER_LAW', 'NER_LOC', 'NER_MONEY', 'NER_NORP', 'NER_ORDINAL', 'NER_ORG', 'NER_PERCENT',
                        'NER_PERSON', 'NER_PRODUCT', 'NER_QUANTITY', 'NER_TIME', 'NER_WORK_OF_ART', 'POS_ADJ',
                        'POS_ADP', 'POS_ADV', 'POS_CCONJ', 'POS_DET', 'POS_INTJ', 'POS_NOUN', 'POS_NUM', 'POS_PART',
                        'POS_PRON', 'POS_PROPN', 'POS_PUNCT', 'POS_SYM', 'POS_VERB', 'POS_X', 'TAG_''', 'TAG_-LRB-',
                        'TAG_.', 'TAG_ADD', 'TAG_AFX', 'TAG_CC', 'TAG_CD', 'TAG_DT', 'TAG_EX', 'TAG_FW', 'TAG_IN',
                        'TAG_JJ', 'TAG_JJR', 'TAG_JJS', 'TAG_LS', 'TAG_MD', 'TAG_NFP', 'TAG_NN', 'TAG_NNP', 'TAG_NNPS',
                        'TAG_NNS', 'TAG_PDT', 'TAG_POS', 'TAG_PRP', 'TAG_PRP$', 'TAG_RB', 'TAG_RBR', 'TAG_RBS',
                        'TAG_RP', 'TAG_SYM', 'TAG_TO', 'TAG_UH', 'TAG_VB', 'TAG_VBD', 'TAG_VBG', 'TAG_VBN', 'TAG_VBP',
                        'TAG_VBZ', 'TAG_WDT', 'TAG_WP', 'TAG_WRB', 'TAG_XX', 'DEP_ROOT', 'DEP_acl', 'DEP_acomp',
                        'DEP_advcl', 'DEP_advmod', 'DEP_agent', 'DEP_amod', 'DEP_appos', 'DEP_attr', 'DEP_aux',
                        'DEP_auxpass', 'DEP_case', 'DEP_cc', 'DEP_ccomp', 'DEP_compound', 'DEP_conj', 'DEP_csubj',
                        'DEP_csubjpass', 'DEP_dative', 'DEP_dep', 'DEP_det', 'DEP_dobj', 'DEP_expl', 'DEP_intj',
                        'DEP_mark', 'DEP_meta', 'DEP_neg', 'DEP_nmod', 'DEP_npadvmod', 'DEP_nsubj', 'DEP_nsubjpass',
                        'DEP_nummod', 'DEP_oprd', 'DEP_parataxis', 'DEP_pcomp', 'DEP_pobj', 'DEP_poss', 'DEP_preconj',
                        'DEP_predet', 'DEP_prep', 'DEP_prt', 'DEP_punct', 'DEP_quantmod', 'DEP_relcl', 'DEP_xcomp']
    for feature in predictorColumns:
        if feature not in wordsDf.columns:
            wordsDf[feature] = 0
    return wordsDf


def predictWords(wordsDf, df):
    predictorPickleName = 'data/nb-predictor.pkl'
    predictor = loadPickle(predictorPickleName)
    y_pred = predictor.predict_proba(wordsDf)
    labeledAnswers = []
    for i in range(len(y_pred)):
        labeledAnswers.append({'word': df.iloc[i]['text'], 'prob': y_pred[i][0]})
    return labeledAnswers


def blankAnswer(firstTokenIndex, lastTokenIndex, sentStart, sentEnd, doc):
    leftPartStart = doc[sentStart].idx
    leftPartEnd = doc[firstTokenIndex].idx
    rightPartStart = doc[lastTokenIndex].idx + len(doc[lastTokenIndex])
    rightPartEnd = doc[sentEnd - 1].idx + len(doc[sentEnd - 1])
    question = doc.text[leftPartStart:leftPartEnd] + '_____' + doc.text[rightPartStart:rightPartEnd]
    return question


def addQuestions(answers, text):
    doc = nlp(text)
    currAnswerIndex = 0
    qaPair = []
    for sent in doc.sents:
        for token in sent:
            if currAnswerIndex >= len(answers):
                break
            answerDoc = nlp(answers[currAnswerIndex]['word'])
            answerIsFound = True
            for j in range(len(answerDoc)):
                if token.i + j >= len(doc) or doc[token.i + j].text != answerDoc[j].text:
                    answerIsFound = False
            if answerIsFound:
                question = blankAnswer(token.i, token.i + len(answerDoc) - 1, sent.start, sent.end, doc)
                qaPair.append({'question': question, 'answer': answers[currAnswerIndex]['word'],
                               'prob': answers[currAnswerIndex]['prob']})
                currAnswerIndex += 1
    return qaPair


def sortAnswers(qaPairs):
    orderedQaPairs = sorted(qaPairs, key=lambda qaPair: qaPair['prob'])
    return orderedQaPairs


def generate_distractors(answer, count):
    answer = str.lower(answer)



    try:
        closestWords = model.most_similar(positive=[answer], topn=count)
    except:
        return []
    distractors = list(map(lambda x: x[0], closestWords))[0:count]
    return distractors


def addDistractors(qaPairs, count):
    for qaPair in qaPairs:
        distractors = generate_distractors(qaPair['answer'], count)
        qaPair['distractors'] = distractors
    return qaPairs


def generateQuestions(text, count):
    df = generateDf(text)
    wordsDf = prepareDf(df)
    labeledAnswers = predictWords(wordsDf, df)
    qaPairs = addQuestions(labeledAnswers, text)
    orderedQaPairs = sortAnswers(qaPairs)
    questions = addDistractors(orderedQaPairs[:count], 4)
    return questions