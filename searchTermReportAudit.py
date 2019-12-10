from difflib import SequenceMatcher
import random, time, os, csv, datetime, sys

# Settings
settings = {
    'inputDirectory' : 'input',
    'outputDirectory': 'output',
    'stopWords': ['aboard','about','above','across','after','against','along','amid','among','anti','around','as','at','before','behind','below','beneath','beside','besides','between','beyond','but','by','concerning','considering','despite','down','during','except','excepting','excluding','following','for','from','in','inside','into','like','minus','near','of','off','on','onto','opposite','outside','over','past','per','plus','regarding','round','save','since','than','through','to','toward','towards','under','underneath','unlike','until','up','upon','versus','via','with','within','without'],
    'searchTermHeaders': ['SearchQuery', 'Keyword', 'Bid match type'],
    'searchTermNewColumns': ['Diff Ratio', 'Clicks Weighted Diff Ratio', 'Impressions Weighted Diff Ratio','Word Count Diff', 'Dropped Words', 'Dropped Stop Word Count', 'Dropped Stop Words', 'Kw Acronym in Search Term', "Phrase Missing", "Dropped BMM Anchor Count", "Dropped BMM Anchors"]
}

# Helper functions
def getDiffRatioCeiling():
    if len(sys.argv) > 1:
        return float(sys.argv[1])
    else:
        return 1.0

def errorOccurred(specifiedError):
    print('Please address the below error before rerunning the script:')
    print(f'\t{specifiedError}')
    quit()

def directoryCheck():
    inputDirectoryExists = True if os.path.exists(settings['inputDirectory']) else False
    if not os.path.exists(settings['inputDirectory']):
        errorOccurred(f"Input directory not found. Create a directory called '{settings['inputDirectory']}' and add your Search Term Reports.")
    elif not os.path.exists(settings['outputDirectory']):
        os.mkdir(settings['outputDirectory'])
        return True

def selectSearchTermReports():
    csvsInDir = [item for item in os.listdir(settings['inputDirectory']) if item.endswith('.csv')]
    if len(csvsInDir) == 0:
        errorOccurred(f"No CSV's detected in the {settings['inputDirectory']} directory. Please add your Search Term Reports.")
    print(f'Auditing the below Search Term Reports:\n{csvsInDir}')
    return csvsInDir

def getDateTimeNow():
    dateTimeNow = datetime.datetime.now()
    return f'{dateTimeNow.strftime("%y")}{dateTimeNow.strftime("%d")}{dateTimeNow.strftime("%y")}{dateTimeNow.strftime("%H")}{dateTimeNow.strftime("%M")}{dateTimeNow.strftime("%f")}'

def prepKeyword(keywordToPrep, bidMatchType):
    if bidMatchType == 'Exact':
        return keywordToPrep.lower().replace("[","").replace("]","")
    elif bidMatchType == 'Phrase':
        return keywordToPrep.lower().replace('"',"")
    elif bidMatchType == 'Broad':
        return keywordToPrep.lower().replace("+","")
    else:
        return keywordToPrep.lower()

def getDifferenceRatio(keyword, searchTerm, bidMatchType):
    return SequenceMatcher(None, keyword, searchTerm).ratio()

def getWordCountDiff(keyword, searchTerm, bidMatchType):
    return len(keyword.split(" ")) - len(searchTerm.split(" "))

def getDroppedWords(keyword, searchTerm, bidMatchType):
    droppedWords = []
    for word in keyword.split(" "):
        if word not in searchTerm:
            if word not in droppedWords:
                droppedWords.append(word)   
    return droppedWords

def getDroppedStopWords(droppedWords):
    droppedStopWords = set(droppedWords).intersection(set(settings['stopWords']))
    return droppedStopWords
    
def findSearchTermHeader(csvReader):
    for row in csvReader:
        if all(item in row for item in settings['searchTermHeaders']):
            return row

def acronymCheck(keyword, searchTerm, bidMatchType):
    if "".join([item[0] for item in keyword.split(" ") if item]) in searchTerm.split(" "):
        return True
    else:
        return False

def phraseCheck(keyword, searchTerm):
    if keyword.replace('"','') not in searchTerm:
        return True
    else:
        return False

def bmmAnchorCheck(keyword, searchTerm):
    anchors = set([word.replace("+","") for word in keyword.split(" ") if "+" in word])
    searchTermSet = set(searchTerm.split(" "))
    droppedAnchors =[f'+{droppedAnchor}' for droppedAnchor in anchors - searchTermSet]

    if len(droppedAnchors) > 0:
        return droppedAnchors
    else:
        return 'No dropped anchors'

def auditSearchTermReports():
    diffRatioCeiling = getDiffRatioCeiling()
    searchTermReports = selectSearchTermReports()
    for searchTermReport in searchTermReports:
        with open(f"{settings['inputDirectory']}\\{searchTermReport}", 'r', errors='ignore') as csvIn:
            print(f"Auditing.. {settings['inputDirectory']}\\{searchTermReport}")
            csvReader = csv.reader(csvIn)
            with open(f"{settings['outputDirectory']}\\{searchTermReport.split('.csv')[0]} Audited {getDateTimeNow()}.csv", 'w', newline='') as csvOut:
                header = findSearchTermHeader(csvReader)
                csvWriter = csv.writer(csvOut, delimiter=',')
                csvWriter.writerow(header + settings['searchTermNewColumns'])
                for row in csvReader:
                    if row and len(row) > 1:
                        bidMatchType = row[header.index('BidMatchType')]
                        rawKeyword = row[header.index('Keyword')].lower()
                        preppedKeyword = prepKeyword(rawKeyword, bidMatchType)
                        searchTerm = row[header.index('Search term')].lower().replace(',','')
                        clicks = round(float(row[header.index('Clicks')].lower()), 4)
                        impressions = round(float(row[header.index('Impressions')].lower()), 4)
                        differenceRatio = getDifferenceRatio(rawKeyword, searchTerm, bidMatchType)

                        if differenceRatio <= diffRatioCeiling:
                            wordCountDiff = getWordCountDiff(preppedKeyword, searchTerm, bidMatchType)
                            droppedWords = getDroppedWords(preppedKeyword, searchTerm, bidMatchType)
                            droppedStopWords = getDroppedStopWords(droppedWords)
                            acronymDetected = acronymCheck(preppedKeyword, searchTerm, bidMatchType)
                            phraseMissing = phraseCheck(rawKeyword, searchTerm) if bidMatchType == 'Phrase' else 'Not Phrase Match'
                            droppedAnchors = bmmAnchorCheck(rawKeyword, searchTerm) if bidMatchType == 'Broad' else 'Not Broad Match'
                            clicksWeighted = clicks / differenceRatio if differenceRatio > 0 else clicks / 0.0001
                            impressionsWeighted = impressions / differenceRatio if differenceRatio > 0 else impressions / 0.0001



                            csvWriter.writerow(row + 
                                [
                                differenceRatio,
                                clicksWeighted,
                                impressionsWeighted, 
                                wordCountDiff, 
                                " ".join(droppedWords), 
                                len(droppedStopWords), 
                                " ".join(droppedStopWords), 
                                acronymDetected, 
                                phraseMissing, 
                                len(droppedAnchors) if droppedAnchors  and droppedAnchors != 'No dropped anchors' and droppedAnchors != 'Not Broad Match' else 'Not BMM', 
                                " ".join(droppedAnchors) if droppedAnchors and droppedAnchors != 'No dropped anchors' and droppedAnchors != 'Not Broad Match'  else 'Not BMM'
                                ])

def main():
    directoryCheck()
    auditSearchTermReports()

if __name__ == "__main__":
    # execute only if run as a script
    main()   

