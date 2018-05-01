#!venv/bin/python
from pathlib import Path
from dbmanager import DBManager
from htmlparser import HTMLParser
from normalizer import Normalizer
from tabulate import tabulate
from collections import OrderedDict
import xml.etree.ElementTree
import signal
import time
import datetime
from nltk.corpus import wordnet


class Controller:
    directory = ""
    manager = DBManager()
    parser = HTMLParser()
    normalizer = Normalizer()

    def __init__(self):
        print("Controller init")
        self.directory = "docrepository"

    def main(self):
        print('Options: 1-setup 2-run 3-run_debug_mode 4-exit d-debug')
        while True:
            text = input("> ")
            if(text == '1'):
                self.setup()
            elif(text == '2'):
                self.displayResults(False)
            elif(text == '3'):
                self.displayResults(True)
            elif(text == '4'):
                break
            elif(text == 'd'):
                self.setupDebug()
            else:
                print("Invalid input")

    def setup(self):
        print("Set up init: ", datetime.datetime.now())
        print("Found the following files:")
        p = Path(self.directory)
        for i in p.iterdir():
            print("Working on file:", i.name)
            if i.name != ".gitkeep":
                path = Path.cwd().joinpath(self.directory +
                                           "/" + i.name)
                with path.open('r', encoding='ascii',
                               errors='replace') as file:
                    # Parser
                    filetext = self.parser.parse(file)
                    # Normalizer

                    def timeout_handler(num, stack):
                        raise Exception("File timeout")

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(120)
                    try:
                        normalized = self.normalizer.normalize(filetext)
                        # Save to DB
                        if self.manager.saveDoc(i.name) == 1:
                            for term in normalized:
                                if self.manager.saveTerm(term) == 1:
                                    relation = {'doc': i.name,
                                                'term': term}
                                    self.manager.saveRelation(relation,
                                                              normalized[term])
                        self.manager.terms.reindex()
                        self.manager.docs.reindex()
                        self.manager.relations.reindex()
                    except Exception:
                        print("Unable to parse file:", i.name)
                    finally:
                        signal.alarm(0)
        self.manager.updateIDF()
        print("Set up end: ", datetime.datetime.now())

    def setupDebug(self):
        print("Found the following files:")
        p = Path(self.directory)
        number = 0
        for i in p.iterdir():
            print("[" + str(number) + "] Working on file:", i.name)
            number += 1
            path = Path.cwd().joinpath(self.directory +
                                       "/" + i.name)
            try:
                with path.open('r', encoding='ASCII',
                               errors='replace') as file:
                    # Parser
                    start_time = time.time()
                    filetext = self.parser.parse(file)
                    print("--- %s seconds in parsing ---"
                          % (time.time() - start_time))
                    # Normalizer
                    start_time = time.time()
                    normalized = self.normalizer.normalize(filetext)
                    print("--- %s seconds in normalize ---"
                          % (time.time() - start_time))
                    # Save to DB
                    start_time = time.time()
                    if self.manager.saveDoc(i.name) == 1:
                        for term in normalized:
                            if self.manager.saveTerm(term) == 1:
                                relation = {'doc': i.name,
                                            'term': term}
                                self.manager.saveRelation(
                                    relation, normalized[term])
                    self.manager.terms.reindex()
                    self.manager.docs.reindex()
                    self.manager.relations.reindex()
                    print("--- %s seconds in saving ---"
                          % (time.time() - start_time))
                    print(str(len(normalized)) + ' terms saved.')
                    print(str(self.manager.terms.count()) + ' total terms.')
            except UnicodeDecodeError:
                print('The element is not encoded in ASCII.')
        self.manager.updateIDF()

    def computeTable(self, topicArray, result, table, method):
        count = 1
        for topic in topicArray:
            index = 'Q' + str(count)
            table[index] = []
            aux = result[topic['query']]
            for r in aux:
                table['Files'] = sorted(Path(self.directory).iterdir())
                if method == 1:
                    # Recuperar resultado de Producto escalar TF
                    table[index].append(r['scalarTF'])
                elif method == 2:
                    # Recuperar resultado de Producto escalar TF IDF
                    table[index].append(r['scalarTF_IDF'])
                elif method == 3:
                    # Recuperar resultado de Coseno TF
                    table[index].append(r['cosTF'])
                elif method == 4:
                    # Recuperar resultado de Coseno TF IDF
                    table[index].append(r['cosTF_IDF'])
            count = count + 1
        return table

    def displayResults(self, debug):
        topicArray = []
        if debug:
            print("Running...")
        root = xml.etree.ElementTree.parse('2010-topics.xml').getroot()
        for topic in root.findall('topic'):
            topicArray.append({'id': topic.get('id'), 'query':
                               topic.find('title').text})
        if debug:
            print(topicArray)
        table = OrderedDict()
        table['Files'] = []

        result = OrderedDict()

        # Compute all calculations
        for topic in topicArray:
            if debug:
                print(topic['query'])
            normalized = self.normalizer.normalize(topic['query'])
            queryArray = []
            for term in normalized:
                if debug:
                    print("This is the term: ", term)
                ss = wordnet.synsets(term)
                if not ss:
                    queryArray.append(term)
                if not (not ss):
                    if debug:
                        print(ss[0].lemma_names())
                    for x in ss[0].lemma_names():
                        #Añadir términos relevantes a la consulta
                        queryArray.append(x)        
            if debug:
                print("Extended Query>>>>>",queryArray)
            
            #result[query] = sorted(search.calcAll(normalized, self.manager.docs, self.manager.relations, self.manager.terms), key=itemgetter('doc'))
        '''
        print("RELEVANCIA: CosenoTFIDF")
        table = self.computeTable(topicArray, result, table, 4)
        print(tabulate(table, headers="keys"))
        '''

controller = Controller()
controller.main()
