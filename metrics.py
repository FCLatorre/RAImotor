#!venv/bin/python
import multiprocessing
from functools import partial
from operator import itemgetter
from math import log2


class Metrics:
    trelFile = ''

    def __init__(self):
        # GLOBAL VARIABLES
        self.trelFile = '2010.union.trel'
    '''
        Cut Recall 5, 10
        This metric will check how many of the
        docs are relevant from the total of documents
    '''
    '''
        Name: cutRecall
        In: array with the file names of the documents returned
            ¡¡¡ SORTED BY NAME !!!
        Out: returns a string showing the cut Recall
        Function: given an array of filenames, it will check the
                relevance of the files and then will return an dictionary
                showing the cut Recall 5, 10
    '''

    # auxiliar function so cutRecall can use multiple processes
    def checkRelevance(self, file, queryID):
        trel = open(self.trelFile, 'r')
        for line in trel:
            if file in line and queryID in line:
                return str(file), int(line.split()[3])
        return str(file), 0

    def cutRecall(self, files, queryID):
        # checks the relevance of the Files
        queryID = str(queryID)
        pool = multiprocessing.Pool()
        relevance = [
            pool.map(partial(self.checkRelevance, queryID=queryID), files)]
        # saves the Recall, which is relevantFiles / retrieved
        Recall5 = 0.0   # first 5 files
        Recall10 = 0.0  # first 10 files
        count = 0
        for (doc, rel) in sorted(relevance[0]):
            if rel >= 1 and count < 5:
                Recall5 = Recall5 + 0.2
            if rel >= 1 and count < 10:
                Recall10 = Recall10 + 0.1
            count += 1
        Recall = {'recall5': Recall5, 'recall10': Recall10}
        return Recall

    '''
        Cut Precision 5, 10
        This metric will check how many of the
        docs are relevant from the total of documents
        retrieved
    '''
    '''
        Name: cutPrecision
        In: array with the file names of the documents returned
            ¡¡¡ SORTED BY NAME !!!
        Out: returns a string showing the cut precision
        Function: given an array of filenames, it will check the
                relevance of the files and then will return a dictionary
                showing the cut precision 5, 10
    '''

    def cutPrecision(self, files, queryID):
        fileNumber = len(files)
        queryID = str(queryID)
        # checks the relevance of the Files
        pool = multiprocessing.Pool()
        relevance = [
            pool.map(partial(self.checkRelevance, queryID=queryID), files)]
        # saves the precision, which is relevantFiles / retrieved
        precision5 = 0.0   # first 5 files
        precision10 = 0.0  # first 10 files
        count = 0
        for (doc, rel) in sorted(relevance[0]):
            if rel >= 1 and count < 5:
                try:
                    precision5 = precision5 + (1 / fileNumber)
                except ZeroDivisionError:
                    precision5 = 0
            if rel >= 1 and count < 10:
                try:
                    precision10 = precision10 + (1 / fileNumber)
                except ZeroDivisionError:
                    precision10 = 0
            count += 1
        precision = {'precision5': precision5, 'precision10': precision10}
        return precision

    '''
        F-Value = 2 * (precision*recall / (precision + recall)))
    '''
    '''
        Name: FMeasure
        In: {precision5, precision10}, {recall5, recall10} it requires
            two dicts with the values
        Out: returns a dict with the FMeasure values for 5, 10
        Function: given the precision and recall cuts, it will calculate
                the FMeasure (witten above) for 5 and 10
    '''

    def FMeasure(self, precision, recall):
        fvalue5 = 0.0
        fvalue10 = 0.0
        try:
            fvalue5 = 2 * (precision['precision5'] * recall['recall5'] /
                           (precision['precision5'] + recall['recall5']))
        except ZeroDivisionError:
            fvalue5 = 0
        try:
            fvalue10 = 2 * (precision['precision10'] * recall['recall10'] /
                            (precision['precision10'] + recall['recall10']))
        except ZeroDivisionError:
            fvalue10 = 0
        return {'fvalue5': fvalue5, 'fvalue10': fvalue10}

    '''
        Reciprocal Rank 1: search the first relevant file in the trel file
        and compares it with the order in wich files have been retrieved
    '''

    '''
       Name: checkRank
       In: queryID, relevance
       Out: returns the first file (string) with the given relevance or
            greater
       Function: given a query ID and a relevance, searchs the first
                file and returns it
   '''

    def checkRank(self, queryID, rel):
        trel = open(self.trelFile, 'r')
        for line in trel:
            if queryID in line and int(line.split()[3]) >= rel:
                return str(line.split()[2])

    '''
        Name: RRank1
        In: files retrieved, queryID
        Out: returns a dict with the RRank1 (float value)
        Function: given a set of retrieved files and it's query ID, it will
                return the Reciprocal Rank (see above)
    '''

    def RRank1(self, files, queryID):
        relFile = self.checkRank(queryID, 1)
        position = 1
        for file in files:
            if file == relFile:
                rrank = 1 / position
                return {'rrank1': rrank}
            position += 1
        rrank = 1 / position
        return {'rrank1': rrank}

    '''
        Name: RRank1
        In: files retrieved, queryID
        Out: returns a dict with the RRank1 (float value)
        Function: given a set of retrieved files and it's query ID, it will
                return the Reciprocal Rank (see above)
    '''

    def RRank2(self, files, queryID):
        relFile = self.checkRank(queryID, 2)
        position = 1
        for file in files:
            if file == relFile:
                rrank = 1 / position
                return {'rrank2': rrank}
            position += 1
        rrank = 1 / position
        return {'rrank2': rrank}

    '''
        Average Precision: will add all the relevance between the
        retrieved files and then will divide it by the number of
        total relevant files in the query
    '''

    '''
       Name: APrecision
       In: files, queryID
       Out: returns the a dict with the Average Precision (float)
       Function: given a query ID and a set of files, calcs the Average
                Precision (with a maximum of 100 files) and then returns
                it
    '''

    def APrecision(self, files, queryID):
        # checks the relevance of the Files
        queryID = str(queryID)
        pool = multiprocessing.Pool()
        relevance = [
            pool.map(partial(self.checkRelevance, queryID=queryID), files)]
        totalRel = 0
        totalRelFiles = 0
        for (file, rel) in relevance[0][:99]:
            if rel >= 1:
                totalRelFiles += 1
                totalRel += rel
        try:
            aprecision = totalRel / totalRelFiles
        except ZeroDivisionError:
            aprecision = 0
        return {'aprecision': aprecision}

    '''
       Name: nDCG
       In: files, queryID, nFiles
       Out: returns the a dict with the DCG at nFiles
       Function: given a query ID and a set of files, calcs the Normalized
                Discounted Cumulated Gain and then returns it
    '''

    def nDCG(self, files, queryID, nFiles):
        # checks the relevance of the Files
        queryID = str(queryID)
        pool = multiprocessing.Pool()
        relevance = [
            pool.map(partial(self.checkRelevance, queryID=queryID), files)][0]
        # saves the relevance for the nFiles in a list
        G = [rel for (doc, rel) in relevance[:(nFiles - 1)]]
        CG = []
        # saves the relevance for the nFiles SORTED from greater
        # to lower in a list
        Gi = [rel for (doc, rel) in sorted(
            relevance[:(nFiles - 1)], key=itemgetter(1), reverse=True)]
        CGi = []
        # calculates the DCG, DCGideal and nDCG (nDCG = DCG/DCGi)
        DCG = []
        DCGi = []
        nDCG = []
        for index, item in enumerate(G):
            # Calcs CG and CGi
            if index == 0:
                CG.append(item)
                CGi.append(Gi[index])
            else:
                CGValue = CG[index - 1] + item
                CGiValue = CGi[index - 1] + Gi[index]
                CG.append(CGValue)
                CGi.append(CGiValue)
            # calcs DCG and DCGi
            if index < 2:
                DCG.append(CG[index])
                DCGi.append(CGi[index])
            else:
                DCGValue = DCG[index - 1] + G[index] / log2(index)
                DCGiValue = DCGi[index - 1] + Gi[index] / log2(index)
                DCG.append(DCGValue)
                DCGi.append(DCGiValue)
            # calcs the nDCG
            try:
                nDCGValue = DCG[index] / DCGi[index]
                nDCG.append(nDCGValue)
            except ZeroDivisionError:
                nDCG.append(0)
        # set the name of the dict
        name = 'nDCG' + str(nFiles)
        return {name: nDCG}
