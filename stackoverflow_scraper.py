import requests
from bs4 import BeautifulSoup
import json
from flask import Flask, request
from datetime import datetime
import math
import os
import time
import backoff

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, factor=2)
def requestTheRequest(url):
    
    theResponse = requests.get(url, verify=False)
    
    if theResponse.status_code == 429:
        raise requests.exceptions.RequestException('Rate limit')
    theResponse.raise_for_status()
    return theResponse

app = Flask(__name__)

@app.route('/')
def index():
    return "Computer Science 343 Web Development Project 1 - stackoverflow_scraper.py", 200

@app.route('/collectives/')
def returnCollectives():
    
    filter = request.args.get('filter', default='default')
    site = request.args.get('site', default=None)
    order = request.args.get('order', default='desc')
    page = request.args.get('page', default=1)
    pageSize = request.args.get('pagesize', default=30)
    
    hasMore = False
    if site == None or site != 'stackoverflow':
        return {
            'error_id':400,
            'error_message':'site is required',
            'error_name':'bad_parameter'
        }, 400
    if filter == 'none':
        return {
            
        }, 200
    
    searchQuestionsByIDList = searchCollectives()
    orderBool = None
    if order == 'desc':
        orderBool = True
    elif order == 'asc':
        orderBool = False
    else:
        return {
            'error_id':400,
            'error_message':'order',
            'error_name':'bad_parameter'
        }, 400
    
    searchQuestionsByIDList.sort(key=lambda x: x['name'], reverse=orderBool)
    try:
        pageSize = int(pageSize)
    except Exception as e:
        return {
            'error_id':400,
            'error_message':'pagesize',
            'error_name':'bad_parameter'
        }, 400
    try:
        page = int(page)
    except Exception as e:
        return {
            'error_id':400,
            'error_message':'page',
            'error_name':'bad_parameter'
        }, 400
    if pageSize > 100 or pageSize < 0:
        return {
            'error_id':400,
            'error_message':'pagesize',
            'error_name':'bad_parameter'
        }, 400
    if page > 25 or page < 0:
        return {
            'error_id':400,
            'error_message':'page',
            'error_name':'bad_parameter'
        }, 400
    
    if len(searchQuestionsByIDList) > pageSize:
        checkIfPageOutOfBounds = math.ceil(len(searchQuestionsByIDList)/pageSize)
        if page > checkIfPageOutOfBounds:
            return {
                'items':[],
                'has_more':hasMore
            }, 200
        startPos = (page - 1) * pageSize
        endPos = (page * pageSize)
        if page == checkIfPageOutOfBounds:
            endPos = len(searchQuestionsByIDList)
        tempList = []
        while startPos < endPos:
            tempList.append(searchQuestionsByIDList[startPos])
            startPos = startPos + 1
        searchQuestionsByIDList.clear()
        searchQuestionsByIDList = tempList
    elif len(searchQuestionsByIDList) <= pageSize and page > 1:
        searchQuestionsByIDList.clear()
    
    if len(searchQuestionsByIDList) < 9:
        hasMore = True
    
    if filter == 'total':
        return len(searchQuestionsByIDList), 200
    returnDict = {
        'items':searchQuestionsByIDList,
        'has_more':hasMore
    }
    print(json.dumps(returnDict, indent=2))
    return returnDict, 200
    

@app.route('/questions/')
def returnQuestions():
    
    order = request.args.get('order', default='desc')
    sort = request.args.get('sort', default='activity')
    filter = request.args.get('filter', default='default')
    page = request.args.get('page', default=1)
    pageSize = request.args.get('pagesize', default=30)
    max = request.args.get('max', default=None)
    min = request.args.get('min', default=None)
    tagged = request.args.get('tagged', default=None)
    site = request.args.get('site', default=None)
    if site == None or site != 'stackoverflow':
        return {
            'error_id':400,
            'error_message':'site is required',
            'error_name':'bad_parameter'
        }, 400
    hasMore = False
    if filter == 'none':
        return {
            
        }, 200
    
    baseURL = 'https://stackoverflow.com/questions'
    inputURL = baseURL
    
    if tagged != None:
        if ';' in tagged:
            taggedList = tagged.split(';')
            if len(taggedList) > 5:
                return {
                    'error_id':400,
                    'error_message':'tagged',
                    'error_name':'bad_parameter'
                }, 400
            inputURL += '/tagged/'
            for tag in taggedList:
                inputURL += tag + ' '
            inputURL = inputURL[:-1]
        else:
            inputURL += '/tagged/' + tagged
    
    inputURL += '?'
    if sort == 'activity':
        sort = 'last_activity_date'
        inputURL += 'tab=active'
    elif sort == 'votes':
        sort = 'score'
        inputURL += 'tab=votes'
    elif sort == 'creation':
        sort = 'creation_date'
        inputURL += 'tab=Newest'
    elif sort == 'hot':
        inputURL += 'tab=hot'
    elif sort == 'week':
        inputURL += 'tab=week'
    elif sort == 'month':
        inputURL += 'tab=month'
    else:
        return {
            'error_id':400,
            'error_message':'sort',
            'error_name':'bad_parameter'
        }, 400
    if order != 'desc' and order != 'asc':
        return {
            'error_id':400,
            'error_message':'order',
            'error_name':'bad_parameter'
        }, 400
        
    try:
        pageSize = int(pageSize)
    except Exception as e:
        return {
            'error_id':400,
            'error_message':'pagesize',
            'error_name':'bad_parameter'
        }, 400
    try:
        page = int(page)
    except Exception as e:
        return {
            'error_id':400,
            'error_message':'page',
            'error_name':'bad_parameter'
        }, 400
    if pageSize > 100 or pageSize < 0:
        return {
            'error_id':400,
            'error_message':'pagesize',
            'error_name':'bad_parameter'
        }, 400
    if page > 25 or page < 0:
        return {
            'error_id':400,
            'error_message':'page',
            'error_name':'bad_parameter'
        }, 400
        
    if min != None:
        try:
            min = int(min)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
    if max != None:
        try:
            max = int(max)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
    
    searchQuestionsList = searchQuestions(inputURL, order, page, pageSize, sort, min, max)
    
    returnDict = {
        'items':searchQuestionsList,
        'has_more':True
    }
        
    return returnDict, 200

@app.route('/questions/<question_id>/')
def returnQuestionId(question_id):
    
    order = request.args.get('order', default='desc')
    sort = request.args.get('sort', default='activity')
    filter = request.args.get('filter', default='default')
    fromDate = request.args.get('fromdate', default=None)
    toDate = request.args.get('todate', default=None)
    page = request.args.get('page', default=1)
    pageSize = request.args.get('pagesize', default=30)
    max = request.args.get('max', default=None)
    min = request.args.get('min', default=None)
    site = request.args.get('site', default=None)
    if site == None or site != 'stackoverflow':
        return {
            'error_id':400,
            'error_message':'site is required',
            'error_name':'bad_parameter'
        }, 400
    hasMore = False
    
    if filter == 'none':
        return {
            
        }, 200
    
    if ';' in question_id:
        idsList = question_id.split(';')
        if len(idsList) > 100:
            return {
                'error_id':400,
                'error_message':'ids',
                'error_name':'bad_parameter'
            }, 400
        
        searchQuestionsByIDList = []
        for id in idsList:
            searchQuestionsByIDList.append(searchQuestionsByID(id))
        if sort == 'activity':
            sort = 'last_activity_date'
        elif sort == 'votes':
            sort = 'score'
        elif sort == 'creation':
            sort = 'creation_date'
        else:
            return {
                'error_id':400,
                'error_message':'sort',
                'error_name':'bad_parameter'
            }, 400
        orderBool = None
        if order == 'desc':
            orderBool = True
        elif order == 'asc':
            orderBool = False
        else:
            return {
                'error_id':400,
                'error_message':'order',
                'error_name':'bad_parameter'
            }, 400
        
        searchQuestionsByIDList.sort(key=lambda x: x[sort], reverse=orderBool)
        
        if fromDate != None:
            try:
                fromDate2 = int(fromDate)
                if 0 <= fromDate2 <= 2**31-1:
                    i = 0
                    while i < len(idsList)/2:
                        for dict in searchQuestionsByIDList:
                            if dict['creation_date'] < fromDate2:
                                searchQuestionsByIDList.remove(dict)
                        i = i + 1
                    
                else:
                    return {
                        'error_id':400,
                        'error_message':'fromdate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'fromdate',
                    'error_name':'bad_parameter'
                }, 400
        
        if toDate != None:
            try:
                toDate2 = int(toDate)
                if 0 <= toDate2 <= 2**31-1:
                    i = 0
                    while i < len(idsList)/2:
                        for dict in searchQuestionsByIDList:
                            if dict['creation_date'] >= toDate2:
                                searchQuestionsByIDList.remove(dict)
                        i = i + 1
                else:
                    return {
                        'error_id':400,
                        'error_message':'todate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'todate',
                    'error_name':'bad_parameter'
                }, 400
        
        if sort == 'last_activity_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['last_activity_date'] < min2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['last_activity_date'] >= max2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'creation_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['creation_date'] < min2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['creation_date'] >= max2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'score':
            if min != None:
                try:
                    min2 = int(min)
                    searchQuestionsByIDList = [list for list in searchQuestionsByIDList if list['score'] >= min2]
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    searchQuestionsByIDList = [list for list in searchQuestionsByIDList if list['score'] <= max2]
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
            
        try:
            pageSize = int(pageSize)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        try:
            page = int(page)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        if pageSize > 100 or pageSize < 0:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        if page > 25 or page < 0:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        
        if len(searchQuestionsByIDList) > pageSize:
            checkIfPageOutOfBounds = math.ceil(len(searchQuestionsByIDList)/pageSize)
            if page > checkIfPageOutOfBounds:
                return {
                    'items':[],
                    'has_more':hasMore
                }, 200
            startPos = (page - 1) * pageSize
            endPos = (page * pageSize)
            if page == checkIfPageOutOfBounds:
                endPos = len(searchQuestionsByIDList)
            tempList = []
            while startPos < endPos:
                tempList.append(searchQuestionsByIDList[startPos])
                startPos = startPos + 1
            searchQuestionsByIDList.clear()
            searchQuestionsByIDList = tempList
        elif len(searchQuestionsByIDList) <= pageSize and page > 1:
            searchQuestionsByIDList.clear()
        
        if filter == 'total':
            return len(searchQuestionsByIDList), 200
        returnDict = {
            'items':searchQuestionsByIDList,
            'has_more':hasMore
        }
        print(json.dumps(returnDict, indent=2))
        return returnDict, 200
    else:
        
        searchQuestionsByIDDict = searchQuestionsByID(question_id)
        if sort == 'activity':
            sort = 'last_activity_date'
        elif sort == 'votes':
            sort = 'score'
        elif sort == 'creation':
            sort = 'creation_date'
        else:
            return {
                'error_id':400,
                'error_message':'sort',
                'error_name':'bad_parameter'
            }, 400
        orderBool = None
        if order == 'desc':
            orderBool = True
        elif order == 'asc':
            orderBool = False
        else:
            return {
                'error_id':400,
                'error_message':'order',
                'error_name':'bad_parameter'
            }, 400
            
        if fromDate != None:
            try:
                fromDate2 = int(fromDate)
                if 0 <= fromDate2 <= 2**31-1:
                    if searchQuestionsByIDDict['creation_date'] < fromDate2:
                        return {
                            'items':[],
                            'has_more':hasMore
                        }, 200
                    
                else:
                    return {
                        'error_id':400,
                        'error_message':'fromdate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'fromdate',
                    'error_name':'bad_parameter'
                }, 400
        
        if toDate != None:
            try:
                toDate2 = int(toDate)
                if 0 <= toDate2 <= 2**31-1:
                    if searchQuestionsByIDDict['creation_date'] >= toDate2:
                        return {
                            'items':[],
                            'has_more':hasMore
                        }, 200
                else:
                    return {
                        'error_id':400,
                        'error_message':'todate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'todate',
                    'error_name':'bad_parameter'
                }, 400
        
        if sort == 'last_activity_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        if searchQuestionsByIDDict['last_activity_date'] < min2:
                            return {
                                'items':[],
                                'has_more':hasMore
                            }, 200
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        if searchQuestionsByIDDict['last_activity_date'] >= max2:
                            return {
                                'items':[],
                                'has_more':hasMore
                            }, 200
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'creation_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        if searchQuestionsByIDDict['creation_date'] < min2:
                            return {
                                'items':[],
                                'has_more':hasMore
                            }, 200
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        if searchQuestionsByIDDict['creation_date'] >= max2:
                            return {
                                'items':[],
                                'has_more':hasMore
                            }, 200
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'score':
            if min != None:
                try:
                    min2 = int(min)
                    if searchQuestionsByIDDict['score'] <= min2:
                        return {
                            'items':[],
                            'has_more':hasMore
                        }, 200
                except Exception as e:
                    print(e)
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if searchQuestionsByIDDict['score'] >= max2:
                        return {
                            'items':[],
                            'has_more':hasMore
                        }, 200
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
            
        try:
            pageSize = int(pageSize)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        try:
            page = int(page)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        if pageSize > 100 or pageSize < 0:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        if page > 25 or page < 0:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        
        if page > 1:
            return {
                'items':[],
                'has_more':hasMore
            }, 200
        
        if filter == 'total':
            return len(searchQuestionsByIDList), 200
        returnDict = {
            'items':searchQuestionsByIDDict,
            'has_more':hasMore
        }
            
        return returnDict, 200
    
@app.route('/answers/<answer_id>/')
def returnAnswerId(answer_id):
    
    order = request.args.get('order', default='desc')
    sort = request.args.get('sort', default='activity')
    filter = request.args.get('filter', default='default')
    fromDate = request.args.get('fromdate', default=None)
    toDate = request.args.get('todate', default=None)
    page = request.args.get('page', default=1)
    pageSize = request.args.get('pagesize', default=30)
    max = request.args.get('max', default=None)
    min = request.args.get('min', default=None)
    site = request.args.get('site', default=None)
    if site == None or site != 'stackoverflow':
        return {
            'error_id':400,
            'error_message':'site is required',
            'error_name':'bad_parameter'
        }, 400
    hasMore = False
    
    if filter == 'none':
        return {
            
        }, 200
    
    if ';' in answer_id:
        idsList = answer_id.split(';')
        if len(idsList) > 100:
            return {
                'error_id':400,
                'error_message':'ids',
                'error_name':'bad_parameter'
            }, 400
        
        searchQuestionsByIDList = []
        for id in idsList:
            searchQuestionsByIDList.append(searchAnswerByID(id))
        if sort == 'activity':
            sort = 'last_activity_date'
        elif sort == 'votes':
            sort = 'score'
        elif sort == 'creation':
            sort = 'creation_date'
        else:
            return {
                'error_id':400,
                'error_message':'sort',
                'error_name':'bad_parameter'
            }, 400
        orderBool = None
        if order == 'desc':
            orderBool = True
        elif order == 'asc':
            orderBool = False
        else:
            return {
                'error_id':400,
                'error_message':'order',
                'error_name':'bad_parameter'
            }, 400
        
        searchQuestionsByIDList.sort(key=lambda x: x[sort], reverse=orderBool)
        
        if fromDate != None:
            try:
                fromDate2 = int(fromDate)
                if 0 <= fromDate2 <= 2**31-1:
                    i = 0
                    while i < len(idsList)/2:
                        for dict in searchQuestionsByIDList:
                            if dict['creation_date'] < fromDate2:
                                searchQuestionsByIDList.remove(dict)
                        i = i + 1
                    
                else:
                    return {
                        'error_id':400,
                        'error_message':'fromdate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'fromdate',
                    'error_name':'bad_parameter'
                }, 400
        
        if toDate != None:
            try:
                toDate2 = int(toDate)
                if 0 <= toDate2 <= 2**31-1:
                    i = 0
                    while i < len(idsList)/2:
                        for dict in searchQuestionsByIDList:
                            if dict['creation_date'] >= toDate2:
                                searchQuestionsByIDList.remove(dict)
                        i = i + 1
                else:
                    return {
                        'error_id':400,
                        'error_message':'todate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'todate',
                    'error_name':'bad_parameter'
                }, 400
        
        if sort == 'last_activity_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['last_activity_date'] < min2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['last_activity_date'] >= max2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'creation_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['creation_date'] < min2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['creation_date'] >= max2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'score':
            if min != None:
                try:
                    min2 = int(min)
                    searchQuestionsByIDList = [list for list in searchQuestionsByIDList if list['score'] >= min2]
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    searchQuestionsByIDList = [list for list in searchQuestionsByIDList if list['score'] <= max2]
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
            
        try:
            pageSize = int(pageSize)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        try:
            page = int(page)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        if pageSize > 100 or pageSize < 0:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        if page > 25 or page < 0:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        
        if len(searchQuestionsByIDList) > pageSize:
            checkIfPageOutOfBounds = math.ceil(len(searchQuestionsByIDList)/pageSize)
            if page > checkIfPageOutOfBounds:
                return {
                    'items':[],
                    'has_more':hasMore
                }, 200
            startPos = (page - 1) * pageSize
            endPos = (page * pageSize)
            if page == checkIfPageOutOfBounds:
                endPos = len(searchQuestionsByIDList)
            tempList = []
            while startPos < endPos:
                tempList.append(searchQuestionsByIDList[startPos])
                startPos = startPos + 1
            searchQuestionsByIDList.clear()
            searchQuestionsByIDList = tempList
        elif len(searchQuestionsByIDList) <= pageSize and page > 1:
            searchQuestionsByIDList.clear()
        
        if filter == 'total':
            return len(searchQuestionsByIDList), 200
        returnDict = {
            'items':searchQuestionsByIDList,
            'has_more':hasMore
        }
        print(json.dumps(returnDict, indent=2))
        return returnDict, 200
    else:
        
        searchQuestionsByIDDict = searchAnswerByID(answer_id)
        if sort == 'activity':
            sort = 'last_activity_date'
        elif sort == 'votes':
            sort = 'score'
        elif sort == 'creation':
            sort = 'creation_date'
        else:
            return {
                'error_id':400,
                'error_message':'sort',
                'error_name':'bad_parameter'
            }, 400
        orderBool = None
        if order == 'desc':
            orderBool = True
        elif order == 'asc':
            orderBool = False
        else:
            return {
                'error_id':400,
                'error_message':'order',
                'error_name':'bad_parameter'
            }, 400
            
        if fromDate != None:
            try:
                fromDate2 = int(fromDate)
                if 0 <= fromDate2 <= 2**31-1:
                    if searchQuestionsByIDDict['creation_date'] < fromDate2:
                        return {
                            'items':[],
                            'has_more':hasMore
                        }, 200
                    
                else:
                    return {
                        'error_id':400,
                        'error_message':'fromdate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'fromdate',
                    'error_name':'bad_parameter'
                }, 400
        
        if toDate != None:
            try:
                toDate2 = int(toDate)
                if 0 <= toDate2 <= 2**31-1:
                    if searchQuestionsByIDDict['creation_date'] >= toDate2:
                        return {
                            'items':[],
                            'has_more':hasMore
                        }, 200
                else:
                    return {
                        'error_id':400,
                        'error_message':'todate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'todate',
                    'error_name':'bad_parameter'
                }, 400
        
        if sort == 'last_activity_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        if searchQuestionsByIDDict['last_activity_date'] < min2:
                            return {
                                'items':[],
                                'has_more':hasMore
                            }, 200
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        if searchQuestionsByIDDict['last_activity_date'] >= max2:
                            return {
                                'items':[],
                                'has_more':hasMore
                            }, 200
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'creation_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        if searchQuestionsByIDDict['creation_date'] < min2:
                            return {
                                'items':[],
                                'has_more':hasMore
                            }, 200
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        if searchQuestionsByIDDict['creation_date'] >= max2:
                            return {
                                'items':[],
                                'has_more':hasMore
                            }, 200
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'score':
            if min != None:
                try:
                    min2 = int(min)
                    if searchQuestionsByIDDict['score'] <= min2:
                        return {
                            'items':[],
                            'has_more':hasMore
                        }, 200
                except Exception as e:
                    print(e)
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if searchQuestionsByIDDict['score'] >= max2:
                        return {
                            'items':[],
                            'has_more':hasMore
                        }, 200
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
            
        try:
            pageSize = int(pageSize)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        try:
            page = int(page)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        if pageSize > 100 or pageSize < 0:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        if page > 25 or page < 0:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        
        if page > 1:
            return {
                'items':[],
                'has_more':hasMore
            }, 200
        
        if filter == 'total':
            return len(searchQuestionsByIDList), 200
        returnDict = {
            'items':searchQuestionsByIDDict,
            'has_more':hasMore
        }
            
        return returnDict, 200

@app.route('/questions/<question_id>/answers/')
def returnQuestionIdAnswers(question_id):
    
    order = request.args.get('order', default='desc')
    sort = request.args.get('sort', default='activity')
    filter = request.args.get('filter', default='default')
    fromDate = request.args.get('fromdate', default=None)
    toDate = request.args.get('todate', default=None)
    page = request.args.get('page', default=1)
    pageSize = request.args.get('pagesize', default=30)
    max = request.args.get('max', default=None)
    min = request.args.get('min', default=None)
    site = request.args.get('site', default=None)
    if site == None or site != 'stackoverflow':
        return {
            'error_id':400,
            'error_message':'site is required',
            'error_name':'bad_parameter'
        }, 400
    hasMore = False
    if filter == 'none':
        return {
            
        }, 200
    
    if ';' in question_id:
        idsList = question_id.split(';')
        if len(idsList) > 100:
            return {
                'error_id':400,
                'error_message':'ids',
                'error_name':'bad_parameter'
            }, 400
        
        searchQuestionsByIDList = []
        for id in idsList:
            searchQuestionsByIDList.append(searchQuestionsByIDAnswers(id))
        tempList1 = []
        for list in searchQuestionsByIDList:
            for dict in list:
                tempList1.append(dict)
        searchQuestionsByIDList.clear()
        searchQuestionsByIDList = tempList1
        
        if sort == 'activity':
            sort = 'last_activity_date'
        elif sort == 'votes':
            sort = 'score'
        elif sort == 'creation':
            sort = 'creation_date'
        else:
            return {
                'error_id':400,
                'error_message':'sort',
                'error_name':'bad_parameter'
            }, 400
        orderBool = None
        if order == 'desc':
            orderBool = True
        elif order == 'asc':
            orderBool = False
        else:
            return {
                'error_id':400,
                'error_message':'order',
                'error_name':'bad_parameter'
            }, 400
        
        searchQuestionsByIDList.sort(key=lambda x: x[sort], reverse=orderBool)
        
        if fromDate != None:
            try:
                fromDate2 = int(fromDate)
                if 0 <= fromDate2 <= 2**31-1:
                    i = 0
                    while i < len(idsList)/2:
                        for dict in searchQuestionsByIDList:
                            if dict['creation_date'] < fromDate2:
                                searchQuestionsByIDList.remove(dict)
                        i = i + 1
                    
                else:
                    return {
                        'error_id':400,
                        'error_message':'fromdate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'fromdate',
                    'error_name':'bad_parameter'
                }, 400
        
        if toDate != None:
            try:
                toDate2 = int(toDate)
                if 0 <= toDate2 <= 2**31-1:
                    i = 0
                    while i < len(idsList)/2:
                        for dict in searchQuestionsByIDList:
                            if dict['creation_date'] >= toDate2:
                                searchQuestionsByIDList.remove(dict)
                        i = i + 1
                else:
                    return {
                        'error_id':400,
                        'error_message':'todate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'todate',
                    'error_name':'bad_parameter'
                }, 400
        
        if sort == 'last_activity_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['last_activity_date'] < min2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['last_activity_date'] >= max2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'creation_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['creation_date'] < min2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['creation_date'] >= max2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'score':
            
            if min != None:
                try:
                    min2 = int(min)
                    searchQuestionsByIDList = [list for list in searchQuestionsByIDList if list['score'] >= min2]
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    searchQuestionsByIDList = [list for list in searchQuestionsByIDList if list['score'] <= max2]
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
            
        try:
            pageSize = int(pageSize)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        try:
            page = int(page)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        if pageSize > 100 or pageSize < 0:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        if page > 25 or page < 0:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        
        if len(searchQuestionsByIDList) > pageSize:
            checkIfPageOutOfBounds = math.ceil(len(searchQuestionsByIDList)/pageSize)
            if page > checkIfPageOutOfBounds:
                return {
                    'items':[],
                    'has_more':hasMore
                }, 200
            startPos = (page - 1) * pageSize
            endPos = (page * pageSize)
            if page == checkIfPageOutOfBounds:
                endPos = len(searchQuestionsByIDList)
            tempList = []
            while startPos < endPos:
                tempList.append(searchQuestionsByIDList[startPos])
                startPos = startPos + 1
            searchQuestionsByIDList.clear()
            searchQuestionsByIDList = tempList
        elif len(searchQuestionsByIDList) <= pageSize and page > 1:
            searchQuestionsByIDList.clear()
        
        if filter == 'total':
            return len(searchQuestionsByIDList), 200
        returnDict = {
            'items':searchQuestionsByIDList,
            'has_more':hasMore
        }
        print(json.dumps(returnDict, indent=2))
        return returnDict, 200
    else:
        
        searchQuestionsByIDList = searchQuestionsByIDAnswers(question_id)
        if sort == 'activity':
            sort = 'last_activity_date'
        elif sort == 'votes':
            sort = 'score'
        elif sort == 'creation':
            sort = 'creation_date'
        else:
            return {
                'error_id':400,
                'error_message':'sort',
                'error_name':'bad_parameter'
            }, 400
        orderBool = None
        if order == 'desc':
            orderBool = True
        elif order == 'asc':
            orderBool = False
        else:
            return {
                'error_id':400,
                'error_message':'order',
                'error_name':'bad_parameter'
            }, 400
        
        searchQuestionsByIDList.sort(key=lambda x: x[sort], reverse=orderBool)
        
        if fromDate != None:
            try:
                fromDate2 = int(fromDate)
                if 0 <= fromDate2 <= 2**31-1:
                    i = 0
                    while i < len(idsList)/2:
                        for dict in searchQuestionsByIDList:
                            if dict['creation_date'] < fromDate2:
                                searchQuestionsByIDList.remove(dict)
                        i = i + 1
                    
                else:
                    return {
                        'error_id':400,
                        'error_message':'fromdate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'fromdate',
                    'error_name':'bad_parameter'
                }, 400
        
        if toDate != None:
            try:
                toDate2 = int(toDate)
                if 0 <= toDate2 <= 2**31-1:
                    i = 0
                    while i < len(idsList)/2:
                        for dict in searchQuestionsByIDList:
                            if dict['creation_date'] >= toDate2:
                                searchQuestionsByIDList.remove(dict)
                        i = i + 1
                else:
                    return {
                        'error_id':400,
                        'error_message':'todate',
                        'error_name':'bad_parameter'
                    }, 400
            except Exception as e:
                return {
                    'error_id':400,
                    'error_message':'todate',
                    'error_name':'bad_parameter'
                }, 400
        
        if sort == 'last_activity_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['last_activity_date'] < min2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['last_activity_date'] >= max2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'creation_date':
            if min != None:
                try:
                    min2 = int(min)
                    if 0 <= min2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['creation_date'] < min2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'min',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    if 0 <= max2 <= 2**31-1:
                        i = 0
                        while i < len(idsList)/2:
                            for dict in searchQuestionsByIDList:
                                if dict['creation_date'] >= max2:
                                    searchQuestionsByIDList.remove(dict)
                            i = i + 1
                    else:
                        return {
                            'error_id':400,
                            'error_message':'max',
                            'error_name':'bad_parameter'
                        }, 400
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
                    
        if sort == 'score':
            
            if min != None:
                try:
                    min2 = int(min)
                    searchQuestionsByIDList = [list for list in searchQuestionsByIDList if list['score'] >= min2]
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'min',
                        'error_name':'bad_parameter'
                    }, 400
            
            if max != None:
                try:
                    max2 = int(max)
                    searchQuestionsByIDList = [list for list in searchQuestionsByIDList if list['score'] <= max2]
                except Exception as e:
                    return {
                        'error_id':400,
                        'error_message':'max',
                        'error_name':'bad_parameter'
                    }, 400
            
        try:
            pageSize = int(pageSize)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        try:
            page = int(page)
        except Exception as e:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        if pageSize > 100 or pageSize < 0:
            return {
                'error_id':400,
                'error_message':'pagesize',
                'error_name':'bad_parameter'
            }, 400
        if page > 25 or page < 0:
            return {
                'error_id':400,
                'error_message':'page',
                'error_name':'bad_parameter'
            }, 400
        
        if len(searchQuestionsByIDList) > pageSize:
            checkIfPageOutOfBounds = math.ceil(len(searchQuestionsByIDList)/pageSize)
            if page > checkIfPageOutOfBounds:
                return {
                    'items':[],
                    'has_more':hasMore
                }, 200
            startPos = (page - 1) * pageSize
            endPos = (page * pageSize)
            if page == checkIfPageOutOfBounds:
                endPos = len(searchQuestionsByIDList)
            tempList = []
            while startPos < endPos:
                tempList.append(searchQuestionsByIDList[startPos])
                startPos = startPos + 1
            searchQuestionsByIDList.clear()
            searchQuestionsByIDList = tempList
        elif len(searchQuestionsByIDList) <= pageSize and page > 1:
            searchQuestionsByIDList.clear()
        
        if filter == 'total':
            return len(searchQuestionsByIDList), 200
        returnDict = {
            'items':searchQuestionsByIDList,
            'has_more':hasMore
        }
        print(json.dumps(returnDict, indent=2))
        return returnDict, 200


def searchCollectives():
    
    collectivesURL = 'https://stackoverflow.com/collectives-all'
    collectivesResponse = requestTheRequest(collectivesURL)
    collectivesSoup = BeautifulSoup(collectivesResponse.text, 'html.parser')
    
    collectivesList = []
    collectivesDict = {}
    
    linksAndNames = collectivesSoup.find_all('div', class_='flex--item fl1')
    x = 0
    for ln in linksAndNames:
        if x == 0:
            x = x + 1
        else:
            collectivesDict = {}
            singleTag = ln.find('a', class_='js-gps-track')
            name = singleTag.text.strip()
            link = singleTag.get('href')
            dataGPSTrack = singleTag.get('data-gps-track')
            slugSplitting = dataGPSTrack.split('subcommunity_slug:')[1]
            subcommunitySlug = slugSplitting.split(',')[0].strip()
            
            collectivesDict['name'] = name
            collectivesDict['link'] = "https://stackoverflow.com" + link
            collectivesDict['slug'] = subcommunitySlug
            
            x = x + 1
            TagsURL = 'https://stackoverflow.com' + link + '?tab=tags'
            TagsResponse = requestTheRequest(TagsURL)
            TagsSoup = BeautifulSoup(TagsResponse.text, 'html.parser')
            
            tagTexts = []
            isNext = TagsSoup.find_all('a', 's-pagination--item js-pagination-item')
            
            if not isNext or isNext == None:
                tags = TagsSoup.find_all('a', class_='s-tag post-tag')
                for tag in tags:
                    tagText = tag.text.strip()
                    tagTexts.append(tagText)
            else:
                tags = TagsSoup.find_all('a', class_='s-tag post-tag')
                for tag in tags:
                    tagText = tag.text.strip()
                    tagTexts.append(tagText)
                
                nextButtonTag = isNext.pop()
                checkIfActuallyNext = nextButtonTag.get('rel')
                
                while checkIfActuallyNext[0] == 'next':
                    nextPageLink = nextButtonTag.get('href')
                    TagsPageURL = 'https://stackoverflow.com' + nextPageLink
                    TagsPageResponse = requestTheRequest(TagsPageURL)
                    TagsPageSoup = BeautifulSoup(TagsPageResponse.text, 'html.parser')
                    tags = TagsPageSoup.find_all('a', class_='s-tag post-tag')
                    for tag in tags:
                        tagText = tag.text.strip()
                        tagTexts.append(tagText)
                    isNext = TagsPageSoup.find_all('a', 's-pagination--item js-pagination-item')
                    nextButtonTag = isNext.pop()
                    checkIfActuallyNext = []
                    checkIfActuallyNext = nextButtonTag.get('rel')
                    if not checkIfActuallyNext:
                        checkIfActuallyNext = ['notNext']
                
            collectivesDict['tags'] = tagTexts
            externalLinksURL = 'https://stackoverflow.com' + link
            externalLinksResponse = requestTheRequest(externalLinksURL)
            externalLinksSoup = BeautifulSoup(externalLinksResponse.text, 'html.parser')
            
            description = externalLinksSoup.find('div', 'fs-body1 fc-black-500 d:fc-black-600 mb6 wmx7').text.strip()
            collectivesDict['description'] = description
            
            externalLinksFromSoup = externalLinksSoup.find_all('a', class_='s-link s-link__inherit ml12')
            externalLinksDict = {}
            externalLinks = []
            externalLinksTypes = []
            for el in externalLinksFromSoup:
                actualLink = el.get('href')
                externalLinks.append(actualLink)
                spanForType = el.find('span', 'd-none').text.strip().lower()
                if spanForType == "contact":
                    spanForType = "support"
                externalLinksTypes.append(spanForType)
                externalLinksDict[spanForType] = actualLink
            collectivesDict['external_links'] = externalLinksDict
            collectivesList.append(collectivesDict)
    print(json.dumps(collectivesList, indent=4)) 
    return collectivesList
            

def findCollective(linkOfCollective):
    
    findCollectivesURL = 'https://stackoverflow.com' + linkOfCollective
    findCollectivesResponse = requestTheRequest(findCollectivesURL)
    findCollectivesSoup = BeautifulSoup(findCollectivesResponse.text, 'html.parser')
    
    header = findCollectivesSoup.find('div', id='community-header')
    name = header.find('h1').text.strip()
    if ' Collective' in name:
        name = name.replace(' Collective', '')
    slug = linkOfCollective.split('/')[2]
    
    TagsURL = 'https://stackoverflow.com' + linkOfCollective + '?tab=tags'
    TagsResponse = requestTheRequest(TagsURL)
    TagsSoup = BeautifulSoup(TagsResponse.text, 'html.parser')
    
    
    tagTexts = []
    isNext = TagsSoup.find_all('a', 's-pagination--item js-pagination-item')
    
    if not isNext or isNext == None:
        tags = TagsSoup.find_all('a', class_='s-tag post-tag')
        for tag in tags:
            tagText = tag.text.strip()
            tagTexts.append(tagText)
    else:
        tags = TagsSoup.find_all('a', class_='s-tag post-tag')
        for tag in tags:
            tagText = tag.text.strip()
            tagTexts.append(tagText)
        
        nextButtonTag = isNext.pop()
        checkIfActuallyNext = nextButtonTag.get('rel')
        
        while checkIfActuallyNext[0] == 'next':
            nextPageLink = nextButtonTag.get('href')
            TagsPageURL = 'https://stackoverflow.com' + nextPageLink
            TagsPageResponse = requestTheRequest(TagsPageURL)
            TagsPageSoup = BeautifulSoup(TagsPageResponse.text, 'html.parser')
            tags = TagsPageSoup.find_all('a', class_='s-tag post-tag')
            for tag in tags:
                tagText = tag.text.strip()
                tagTexts.append(tagText)
            isNext = TagsPageSoup.find_all('a', 's-pagination--item js-pagination-item')
            nextButtonTag = isNext.pop()
            checkIfActuallyNext = []
            checkIfActuallyNext = nextButtonTag.get('rel')
            if not checkIfActuallyNext:
                checkIfActuallyNext = ['notNext']
    
    externalLinksURL = 'https://stackoverflow.com' + linkOfCollective
    externalLinksResponse = requestTheRequest(externalLinksURL)
    externalLinksSoup = BeautifulSoup(externalLinksResponse.text, 'html.parser')
    description = externalLinksSoup.find('div', 'fs-body1 fc-black-500 d:fc-black-600 mb6 wmx7').text.strip()
    externalLinksFromSoup = externalLinksSoup.find_all('a', class_='s-link s-link__inherit ml12')
    externalLinksDict = {}
    externalLinks = []
    externalLinksTypes = []
    externalLinksActual = []
    for el in externalLinksFromSoup:
        actualLink = el.get('href')
        externalLinks.append(actualLink)
        spanForType = el.find('span', 'd-none').text.strip().lower()
        if spanForType == "contact":
            spanForType = "support"
        externalLinksTypes.append(spanForType)
        externalLinksDict['type'] = spanForType
        externalLinksDict['link'] = actualLink
        externalLinksActual.append(externalLinksDict)
    
    collective = {
        "tags": tagTexts,
        "external_links": externalLinksActual,
        "description": description,
        "link": linkOfCollective,
        "name": name,
        "slug": slug
    }
    return collective
    
def findUser(userLink):
    
    findUserURL = 'https://stackoverflow.com' + userLink
    findUserResponse = requestTheRequest(findUserURL)
    findUserSoup = BeautifulSoup(findUserResponse.text, 'html.parser')
    userName = findUserSoup.find('div', 'flex--item mb12 fs-headline2 lh-xs').text.strip()
    userImage = findUserSoup.find('img', 'bar-sm bar-md d-block').get('src')
    userTypeTagDiv = findUserSoup.find('div', class_='d-flex ai-center fw-wrap gs8 wmx4')
    userTypeTag = userTypeTagDiv.find('div', class_=lambda x: x and x.startswith('flex--item s-badge s-badge__'))
    userType = 'registered'
    if userTypeTag != None:
        userType = userTypeTag.text.strip()
    userID = userLink.split('/')[2]
    
    accountID = None
    head = findUserSoup.find('head')
    listOfAllScripts = head.find_all('script')
    for script in listOfAllScripts:
        scriptText = script.text.strip().lower()
        if 'accountid' in scriptText:
            tempStr = scriptText.split(':')[2]
            tempStr2 = tempStr.split('}')[0].strip()
            accountID = tempStr2
            break
    
    userRep = findUserSoup.find('div', 'fs-body3 fc-black-600').text.strip().replace(',', '')
    owner = {
        'account_id':int(accountID),
        'reputation':int(userRep),
        'user_id':int(userID),
        "user_type": userType,
        "profile_image": userImage,
        "display_name": userName,
        "link": findUserURL
    }
    return owner
    
def searchQuestions(inputURL, order, page, pageSize, sort, min, max):
    
    dontStopUntil = page * pageSize
    counter = 0
    pageCounter = 0
    questionsDict = {}
    questionsList = []
    hasMore = True
    while counter < dontStopUntil:
        if pageCounter == 0:
            pageCounter = pageCounter + 1
            questionsURL = inputURL
        else:
            pageCounter = pageCounter + 1
            questionsURL = inputURL + '&page=' + str(pageCounter)
        
        questionsResponse = requestTheRequest(questionsURL)
        questionsSoup = BeautifulSoup(questionsResponse.text, 'html.parser')
        allQuestions = questionsSoup.find_all('div', class_='s-post-summary js-post-summary')
        if not allQuestions:
            break 
        for q in allQuestions:
            
            questionsDict = {}
            counter = counter + 1
            questionID = q.get('data-post-id')
            print(f"Question ID: {questionID}")
            questionsDict['question_id'] = questionID
            
            titleLink = q.find('a', 's-link').get('href')
            title = q.find('a', 's-link').text.strip()
            print(f"Title of question: {title}   Link: {titleLink}")
            
            #to get last activity date, last edited date and accepted answer user ID, we must go into the question
            indivQuestionsURL = 'https://stackoverflow.com/questions/' + questionID + '/'
            time.sleep(0.5)
            indivQuestionsResponse = requestTheRequest(indivQuestionsURL)
            indivQuestionsSoup = BeautifulSoup(indivQuestionsResponse.text, 'html.parser')
            answerID = None
            questionHyperLink = indivQuestionsSoup.find('a', 'question-hyperlink')
            link = questionHyperLink.get('href')
            title = questionHyperLink.text.strip()
            print(f"Question link: {link}")
            print(f"Question title: {title}")
            questionsDict['link'] = 'https://stackoverflow.com' + link
            if ' [closed]' in title:
                title = title.replace(' [closed]', '')
            if ' [duplicate]' in title:
                title = title.replace(' [duplicate]', '')
            questionsDict['title'] = title
            
            score = indivQuestionsSoup.find('div', class_=lambda x: x and x.startswith('js-vote-count')).text.strip()
            viewsTagDiv = indivQuestionsSoup.find('div', 'd-flex fw-wrap pb8 mb16 bb bc-black-200')
            viewsTagDiv2 = viewsTagDiv.find('div', class_=lambda x: x and x.startswith('flex--item ws-nowrap mb8'))
            
            views = viewsTagDiv2.get('title').split(' ')[-2].replace(',', '')
            
            answersTagDiv = indivQuestionsSoup.find('div', 'answers-subheader d-flex ai-center mb8')
            answersTag = answersTagDiv.find('h2', 'mb0')
            answers = '0'
            if answersTag != None:
                answers = answersTag.text.strip().split(' ')[-1]
            hasAcceptedAns = False
            checkIfAcceptedAns = indivQuestionsSoup.find('svg', 'svg-icon iconCheckmarkLg')
            if checkIfAcceptedAns != None:
                checkIfAcceptedAns2 = checkIfAcceptedAns.get('aria-hidden')
                if checkIfAcceptedAns2 == 'false':
                    hasAcceptedAns = True
            print(f"Question score: {score}")
            if sort == 'score':
                if min != None:
                    if int(score) < min and order == 'desc':
                        counter = dontStopUntil
                        hasMore = False
                        break
                    if int(score) < min:
                        counter = counter - 1
                        continue
                if max != None:
                    if int(score) > max and order == 'asc':
                        counter = dontStopUntil
                        hasMore = False
                        break
                    if int(score) > max:
                        counter = counter - 1
                        continue
            questionsDict['score'] = int(score)
            print(f"Question answers: {answers}")
            questionsDict['answer_count'] = int(answers)
            print(f"Question answers accepted: {hasAcceptedAns}")
            print(f"Question views: {views}")
            questionsDict['view_count'] = int(views)
            
            tagsDiv = indivQuestionsSoup.find('div', 'post-taglist d-flex gs4 gsy fd-column')
            tags = tagsDiv.find_all('a', class_=lambda x: x and x.startswith('s-tag post-tag'))
            tagTexts = []
            for tag in tags:
                tagText = tag.text.strip()
                tagTexts.append(tagText)
            
            print(f"Tags: {tagTexts}")
            questionsDict['tags'] = tagTexts
            
            lastActivityDate = None
            isAnswered = False
            if answers == '0':
                isAnswered = False
            else:
                allAnswersTag = indivQuestionsSoup.find_all('div', id=lambda x: x and x.startswith('answer-'))
                for ans in allAnswersTag:
                    score = ans.find('div', class_=lambda x: x and x.startswith('js-vote-count')).text.strip()
                    if int(score) > 0:
                        isAnswered = True
                        break
                    acceptedTag = ans.find('div', 'js-accepted-answer-indicator flex--item fc-green-400 py6 mtn8')
                    if acceptedTag != None:
                        isAnswered = True
                        break
                
            print(f"is Answered: {isAnswered}")
            questionsDict['is_answered'] = isAnswered
            
            answerID = None
            if hasAcceptedAns == True:
                answerDiv = indivQuestionsSoup.find('div', class_='answer js-answer accepted-answer js-accepted-answer')
                answerID = answerDiv.get('data-answerid')
                questionsDict['accepted_answer_id'] = int(answerID)
            print(f"accepted answer ID: {answerID}")
            modifiedTag = indivQuestionsSoup.find('a', class_='s-link s-link__inherit')
            lastActivityDate = modifiedTag.get('title')
            dateObj = datetime.fromisoformat(lastActivityDate.replace('Z', '+00:00'))
            lastActivityDate = int(dateObj.timestamp())
            print(f"last activity date: {lastActivityDate}")
            questionsDict['last_activity_date'] = lastActivityDate
            if sort == 'last_activity_date':
                if min != None:
                    if lastActivityDate < min and order == 'desc':
                        counter = dontStopUntil
                        hasMore = False
                        break
                    if lastActivityDate < min:
                        counter = counter - 1
                        continue
                if max != None:
                    if lastActivityDate > max and order == 'asc':
                        counter = dontStopUntil
                        hasMore = False
                        break
                    if lastActivityDate > max:
                        counter = counter - 1
                        continue
            lastEditedDate = None
            editedTag = indivQuestionsSoup.find('div', class_='user-action-time fl-grow1')
            editedSpanTag = editedTag.find('span', class_='relativetime')
            lastEditedDate = editedSpanTag.get('title')
            dateObj = datetime.fromisoformat(lastEditedDate.replace('Z', '+00:00'))
            lastEditedDate = int(dateObj.timestamp())
            print(f"last edited date: {lastEditedDate}")
            questionsDict['last_edit_date'] = lastEditedDate
            lastEditedDate = editedSpanTag.get('title')
            lastEditedDate = lastEditedDate[:10]
            closedTag = indivQuestionsSoup.find('aside', class_='s-notice s-notice__info post-notice js-post-notice mb16')
            closedDate = None
            closedReason = None
            lockedDate = None
            isLocked = False
            if closedTag != None:
                lockedIcon = closedTag.find('svg', 'svg-icon iconLock')
                closedDateTag = closedTag.find('span', 'relativetime')
                if lockedIcon != None:
                    isLocked = True
                    lockedDate = lastEditedDate
                if closedDateTag != None:
                    closedDate = closedDateTag.get('title')
                    dateObj = datetime.fromisoformat(closedDate.replace('Z', '+00:00'))
                    closedDate = int(dateObj.timestamp())
                    closedReason = closedTag.find('div', 'd-flex fw-nowrap').text.strip()
            
            print(f"closed date: {closedDate}")
            print(f"closed reason: {closedReason}")
            if closedDate != None:
                questionsDict['closed_date'] = closedDate
            
            bountyTag = indivQuestionsSoup.find('aside', class_='s-notice s-notice__info post-notice js-post-notice mb16 js-bounty-notification')
            bountyAmount = None
            bountyDate = None
            if bountyTag != None:
                bountyDateTag = bountyTag.find('b')
                bountyDateTag2 = bountyDateTag.find('span')
                bountyDate = bountyDateTag2.get('title')
                dateObj = datetime.fromisoformat(bountyDate.replace('Z', '+00:00'))
                bountyDate = int(dateObj.timestamp())
                bountyAmount = bountyTag.find('span', class_='s-badge s-badge__bounty d-inline px4 py2 ba bc-transparent bar-sm fs-caption va-middle').text.split()[0]
            
            print(f"bounty amount: {bountyAmount}")
            print(f"bounty end date: {bountyDate}")
            if bountyAmount != None:
                questionsDict['bounty_amount'] = int(bountyAmount[1:])
                questionsDict['bounty_closes_date'] = bountyDate
            
            creationYear = lastEditedDate[:4]
            creationMonth = lastEditedDate[5:7]
            creationDay = lastEditedDate[8:10]
            print(f"year: {creationYear}   month: {creationMonth}   day: {creationDay}")
            contentLicense = None
            if int(creationYear) < 2011:
                contentLicense = 'CC BY-SA 2.5'
            elif int(creationYear) == 2011 and int(creationMonth) < 4:
                contentLicense = 'CC BY-SA 2.5'
            elif int(creationYear) == 2011 and int(creationMonth) == 4 and int(creationDay) < 8:
                contentLicense = 'CC BY-SA 2.5'
            elif int(creationYear) < 2018:
                contentLicense = 'CC BY-SA 3.0'
            elif int(creationYear) == 2018 and int(creationMonth) < 5:
                contentLicense = 'CC BY-SA 3.0'
            elif int(creationYear) == 2018 and int(creationMonth) == 5 and int(creationDay) < 2:
                contentLicense = 'CC BY-SA 3.0'
            else:
                contentLicense = 'CC BY-SA 4.0'
            print(f"content license: {contentLicense}")
            questionsDict['content_license'] = contentLicense
            
            questionsTimelineURL = 'https://stackoverflow.com/posts/' + str(questionID) + '/timeline'
            questionsTimelineResponse = requestTheRequest(questionsTimelineURL)
            questionsTimelineSoup = BeautifulSoup(questionsTimelineResponse.text, 'html.parser')
            
            dateHashTag = questionsTimelineSoup.find_all('tr', class_=lambda x: x and x.startswith('datehash-'))
            communityOwnedDate = None
            
            migratedFrom = None
            lastLocked = True
            lastClosed = True
            for ct in dateHashTag:
                checkIfCommunity = ct.find('td', 'event-comment').text.strip().lower()
                if "post made community wiki" in checkIfCommunity:
                    communityOwnedTag = ct.find('span', 'relativetime')
                    communityOwnedDate = communityOwnedTag.get('title')
                    dateObj = datetime.fromisoformat(communityOwnedDate.replace('Z', '+00:00'))
                    communityOwnedDate = int(dateObj.timestamp()) 
                migratedOrLockedTag = ct.find('td', 'wmn1').text.strip().lower()
                if "locked" in migratedOrLockedTag and lastLocked and not 'unlocked' in migratedOrLockedTag:
                    lockedDateTag = ct.find('span', 'relativetime')
                    lockedDate = lockedDateTag.get('title')
                    dateObj = datetime.fromisoformat(lockedDate.replace('Z', '+00:00'))
                    lockedDate = int(dateObj.timestamp()) 
                    lastLocked = False
                if 'unlocked' in migratedOrLockedTag:
                    lastLocked = False
                if 'closed' == migratedOrLockedTag and closedDate != None and lastClosed:
                    closedReason = ct.find('td', 'event-comment').text.strip()
                    questionsDict['closed_reason'] = closedReason
                    lastClosed = False
                if "migrated" in migratedOrLockedTag:
                    migratedFrom = None
                    #DO MIGRATION - Leaving it for now because its too long for only 1 test case. 
            print(f"locked date: {lockedDate}")
            print(f"community owned date: {communityOwnedDate}")
            if lockedDate != None:
                questionsDict['locked_date'] = lockedDate
            if communityOwnedDate != None:
                questionsDict['community_owned_date'] = communityOwnedDate
            
            ownerTR = dateHashTag.pop()
            ownerTD = ownerTR.find_all('td', class_='ws-nowrap')
            creationDateTD = ownerTR.find('td', 'ws-nowrap creation-date')
            creationDateSpan = creationDateTD.find('span', 'relativetime')
            creationDate = creationDateSpan.get('title')
            dateObj = datetime.fromisoformat(creationDate.replace('Z', '+00:00'))
            creationDate = int(dateObj.timestamp())
            
            print(f"creation date: {creationDate}")
            
            count = 0
            theRow = None
            ownerTRCommentTag = None
            protectedDate = None
            isProtected = True
            for td in ownerTD:
                userLinkTag = td.find('a', 'comment-user owner')
                if userLinkTag != None:
                    userLink = userLinkTag.get('href')
                    ownerDictionary = findUser(userLink)
                    print(json.dumps(ownerDictionary, indent=4))
                    questionsDict['owner'] = ownerDictionary
                else:
                    count = count + 1
            if count == len(ownerTD):
                count2 = 0
                dateHashTag.append(ownerTR)
                for row in dateHashTag:
                    ownerTRCommentTag = row.find('td', class_=lambda x: x and x.startswith('wmn1')).text.strip().lower()
                    if 'asked' in ownerTRCommentTag:
                        theRow = row
                        ownerTD2 = row.find_all('td', class_='ws-nowrap')
                        
                        for td2 in ownerTD2:
                            userLinkTag2 = td2.find('a', 'comment-user owner')
                            if userLinkTag2 != None:
                                userLink2 = userLinkTag2.get('href')
                                ownerDictionary2 = findUser(userLink2)
                                print(json.dumps(ownerDictionary2, indent=4))
                                questionsDict['owner'] = ownerDictionary2
                            else:
                                count2 = count2 + 1
                    if 'protected' in ownerTRCommentTag and isProtected and not 'unprotected' in ownerTRCommentTag:
                        protectedDateTD = row.find('td', 'ws-nowrap creation-date')
                        protectedDateSpan = protectedDateTD.find('span', 'relativetime')
                        protectedDate = protectedDateSpan.get('title')
                        dateObj = datetime.fromisoformat(protectedDate.replace('Z', '+00:00'))
                        protectedDate = int(dateObj.timestamp())
                    if 'unprotected' in ownerTRCommentTag:
                        isProtected = False
                if count2 == len(ownerTD2):
                    print("User type is does not exist")
                    if "asked" in ownerTRCommentTag:
                        doesNotExistOwner = theRow.find_all('td')[3].text.strip()
                        ownerDictionaryDNE = {
                            'display_name':doesNotExistOwner,
                            "user_type":'does not exist'
                        }
                        print(json.dumps(ownerDictionaryDNE, indent=4))
                        questionsDict['owner'] = ownerDictionaryDNE
            
            if count == len(ownerTD):
                creationDateTD = theRow.find('td', 'ws-nowrap creation-date')
            else:
                creationDateTD = ownerTR.find('td', 'ws-nowrap creation-date')
            creationDateSpan = creationDateTD.find('span', 'relativetime')
            creationDate = creationDateSpan.get('title')
            dateObj = datetime.fromisoformat(creationDate.replace('Z', '+00:00'))
            creationDate = int(dateObj.timestamp())
            questionsDict['creation_date'] = creationDate
            if sort == 'creation_date':
                if min != None:
                    if creationDate < min and order == 'desc':
                        counter = dontStopUntil
                        hasMore = False
                        break
                    if creationDate < min:
                        counter = counter - 1
                        continue
                if max != None:
                    if creationDate > max and order == 'asc':
                        counter = dontStopUntil
                        hasMore = False
                        break
                    if creationDate > max:
                        counter = counter - 1
                        continue
            
            if protectedDate != None:
                questionsDict['protected_date'] = protectedDate
            else:
                dateHashTag.append(ownerTR)
                isProtected = True
                for row in dateHashTag:
                    ownerTRCommentTag = row.find('td', class_=lambda x: x and x.startswith('wmn1')).text.strip().lower()
                    print(ownerTRCommentTag)
                    if 'protected' in ownerTRCommentTag and isProtected and not 'unprotected' in ownerTRCommentTag:
                        protectedDateTD = row.find('td', 'ws-nowrap creation-date')
                        protectedDateSpan = protectedDateTD.find('span', 'relativetime')
                        protectedDate = protectedDateSpan.get('title')
                        dateObj = datetime.fromisoformat(protectedDate.replace('Z', '+00:00'))
                        protectedDate = int(dateObj.timestamp())
                        questionsDict['protected_date'] = protectedDate
                    if 'unprotected' in ownerTRCommentTag:
                        isProtected = False
            print('-' * 80)
            keys = [
                'tags', 'migrated_from', 'owner',
                'is_answered', 'view_count', 'closed_date',
                'bounty_amount', 'bounty_closes_date',
                'protected_date', 'accepted_answer_id',
                'answer_count', 'community_owned_date',
                'score', 'locked_date', 'last_activity_date',
                'creation_date', 'last_edit_date',
                'question_id', 'content_license', 'link',
                'closed_reason', 'title'
            ]
            returningDict = {}
            for key in keys:
                if key in questionsDict:
                    returningDict[key] = questionsDict[key]

            print(json.dumps(returningDict, indent=4))
            questionsList.append(returningDict)
    
    checkIfPageOutOfBounds = math.ceil(len(questionsList)/pageSize)
    if page > checkIfPageOutOfBounds:
        return {
            'items':[],
            'has_more':False
        }, 200
    startPos = (page - 1) * pageSize
    endPos = (page * pageSize)
    if page == checkIfPageOutOfBounds:
        endPos = len(questionsList)
    tempList = []
    while startPos < endPos:
        tempList.append(questionsList[startPos])
        startPos = startPos + 1
    
    if len(tempList) < len(questionsList):
        hasMore = True
    questionsList.clear()
    questionsList = tempList
    
    if order == 'asc':
        questionsList.reverse()
        
    returnList = {
        'items':questionsList,
        'has_more':hasMore
    }
    print(json.dumps(returnList, indent=4))
    return returnList
        
def searchQuestionsByID(id):
    
    questionsByIDURL = 'https://stackoverflow.com/questions/' + str(id)
    time.sleep(0.5)
    questionsByIDResponse = requestTheRequest(questionsByIDURL)
    questionsByIDSoup = BeautifulSoup(questionsByIDResponse.text, 'html.parser')
    questionsByIDDict = {}
    
    questionHyperLink = questionsByIDSoup.find('a', 'question-hyperlink')
    link = questionHyperLink.get('href')
    title = questionHyperLink.text.strip()
    print(f"Question link: {link}")
    print(f"Question title: {title}")
    questionsByIDDict['link'] = 'https://stackoverflow.com' + link
    if ' [closed]' in title:
        title = title.replace(' [closed]', '')
    if ' [duplicate]' in title:
        title = title.replace(' [duplicate]', '')
    questionsByIDDict['title'] = title
    
    
    print(f"Question ID: {id}")
    questionsByIDDict['question_id'] = int(id)
    score = questionsByIDSoup.find('div', class_=lambda x: x and x.startswith('js-vote-count')).text.strip()
    viewsTagDiv = questionsByIDSoup.find('div', 'd-flex fw-wrap pb8 mb16 bb bc-black-200')
    viewsTagDiv2 = viewsTagDiv.find('div', class_=lambda x: x and x.startswith('flex--item ws-nowrap mb8'))
    
    views = viewsTagDiv2.get('title').split(' ')[-2].replace(',', '')
    
    answersTagDiv = questionsByIDSoup.find('div', 'answers-subheader d-flex ai-center mb8')
    answersTag = answersTagDiv.find('h2', 'mb0')
    answers = '0'
    if answersTag != None:
        answers = answersTag.text.strip().split(' ')[-1]
    hasAcceptedAns = False
    checkIfAcceptedAns = questionsByIDSoup.find('svg', 'svg-icon iconCheckmarkLg')
    if checkIfAcceptedAns != None:
        checkIfAcceptedAns2 = checkIfAcceptedAns.get('aria-hidden')
        if checkIfAcceptedAns2 == 'false':
            hasAcceptedAns = True
    print(f"Question score: {score}")
    questionsByIDDict['score'] = int(score)
    print(f"Question answers: {answers}")
    questionsByIDDict['answer_count'] = int(answers)
    print(f"Question answers accepted: {hasAcceptedAns}")
    print(f"Question views: {views}")
    questionsByIDDict['view_count'] = int(views)
    
    tagsDiv = questionsByIDSoup.find('div', 'post-taglist d-flex gs4 gsy fd-column')
    tags = tagsDiv.find_all('a', class_=lambda x: x and x.startswith('s-tag post-tag'))
    tagTexts = []
    for tag in tags:
        tagText = tag.text.strip()
        tagTexts.append(tagText)
    
    print(f"Tags: {tagTexts}")
    questionsByIDDict['tags'] = tagTexts
    
    lastActivityDate = None
    isAnswered = None
    if answers == '0':
        isAnswered = False
    else:
        allAnswersTag = questionsByIDSoup.find_all('div', id=lambda x: x and x.startswith('answer-'))
        for ans in allAnswersTag:
            score = ans.find('div', class_=lambda x: x and x.startswith('js-vote-count')).text.strip()
            if int(score) > 0:
                isAnswered = True
                break
            acceptedTag = ans.find('div', 'js-accepted-answer-indicator flex--item fc-green-400 py6 mtn8')
            if acceptedTag != None:
                isAnswered = True
                break
    print(f"is Answered: {isAnswered}")
    questionsByIDDict['is_answered'] = isAnswered
    
    answerID = None
    if hasAcceptedAns == True:
        answerDiv = questionsByIDSoup.find('div', class_='answer js-answer accepted-answer js-accepted-answer')
        answerID = answerDiv.get('data-answerid')
        questionsByIDDict['accepted_answer_id'] = int(answerID)
    print(f"accepted answer ID: {answerID}")
    modifiedTag = questionsByIDSoup.find('a', class_='s-link s-link__inherit')
    lastActivityDate = modifiedTag.get('title')
    dateObj = datetime.fromisoformat(lastActivityDate.replace('Z', '+00:00'))
    lastActivityDate = int(dateObj.timestamp())
    print(f"last activity date: {lastActivityDate}")
    questionsByIDDict['last_activity_date'] = lastActivityDate
    lastEditedDate = None
    editedTag = questionsByIDSoup.find('div', class_='user-action-time fl-grow1')
    editedSpanTag = editedTag.find('span', class_='relativetime')
    lastEditedDate = editedSpanTag.get('title')
    dateObj = datetime.fromisoformat(lastEditedDate.replace('Z', '+00:00'))
    lastEditedDate = int(dateObj.timestamp())
    print(f"last edited date: {lastEditedDate}")
    questionsByIDDict['last_edit_date'] = lastEditedDate
    lastEditedDate = editedSpanTag.get('title')
    lastEditedDate = lastEditedDate[:10]
    closedTag = questionsByIDSoup.find('aside', class_='s-notice s-notice__info post-notice js-post-notice mb16')
    closedDate = None
    closedReason = None
    lockedDate = None
    isLocked = False
    if closedTag != None:
        lockedIcon = closedTag.find('svg', 'svg-icon iconLock')
        closedDateTag = closedTag.find('span', 'relativetime')
        if lockedIcon != None:
            isLocked = True
            lockedDate = lastEditedDate
        if closedDateTag != None:
            closedDate = closedDateTag.get('title')
            dateObj = datetime.fromisoformat(closedDate.replace('Z', '+00:00'))
            closedDate = int(dateObj.timestamp())
            closedReason = closedTag.find('div', 'd-flex fw-nowrap').text.strip()
    
    print(f"closed date: {closedDate}")
    print(f"closed reason: {closedReason}")
    if closedDate != None:
        questionsByIDDict['closed_date'] = closedDate
    
    bountyTag = questionsByIDSoup.find('aside', class_='s-notice s-notice__info post-notice js-post-notice mb16 js-bounty-notification')
    bountyAmount = None
    bountyDate = None
    if bountyTag != None:
        bountyDateTag = bountyTag.find('b')
        bountyDateTag2 = bountyDateTag.find('span')
        bountyDate = bountyDateTag2.get('title')
        dateObj = datetime.fromisoformat(bountyDate.replace('Z', '+00:00'))
        bountyDate = int(dateObj.timestamp())
        bountyAmount = bountyTag.find('span', class_='s-badge s-badge__bounty d-inline px4 py2 ba bc-transparent bar-sm fs-caption va-middle').text.split()[0]
    
    print(f"bounty amount: {bountyAmount}")
    print(f"bounty end date: {bountyDate}")
    if bountyAmount != None:
        questionsByIDDict['bounty_amount'] = int(bountyAmount[1:])
        questionsByIDDict['bounty_closes_date'] = bountyDate
    
    creationYear = lastEditedDate[:4]
    creationMonth = lastEditedDate[5:7]
    creationDay = lastEditedDate[8:10]
    print(f"year: {creationYear}   month: {creationMonth}   day: {creationDay}")
    contentLicense = None
    if int(creationYear) < 2011:
        contentLicense = 'CC BY-SA 2.5'
    elif int(creationYear) == 2011 and int(creationMonth) < 4:
        contentLicense = 'CC BY-SA 2.5'
    elif int(creationYear) == 2011 and int(creationMonth) == 4 and int(creationDay) < 8:
        contentLicense = 'CC BY-SA 2.5'
    elif int(creationYear) < 2018:
        contentLicense = 'CC BY-SA 3.0'
    elif int(creationYear) == 2018 and int(creationMonth) < 5:
        contentLicense = 'CC BY-SA 3.0'
    elif int(creationYear) == 2018 and int(creationMonth) == 5 and int(creationDay) < 2:
        contentLicense = 'CC BY-SA 3.0'
    else:
        contentLicense = 'CC BY-SA 4.0'
    print(f"content license: {contentLicense}")
    questionsByIDDict['content_license'] = contentLicense
    
    questionsTimelineURL = 'https://stackoverflow.com/posts/' + str(id) + '/timeline'
    questionsTimelineResponse = requestTheRequest(questionsTimelineURL)
    questionsTimelineSoup = BeautifulSoup(questionsTimelineResponse.text, 'html.parser')
    
    dateHashTag = questionsTimelineSoup.find_all('tr', class_=lambda x: x and x.startswith('datehash-'))
    communityOwnedDate = None
    
    migratedFrom = None
    lastLocked = True
    lastClosed = True
    for ct in dateHashTag:
        checkIfCommunity = ct.find('td', 'event-comment').text.strip().lower()
        if "post made community wiki" in checkIfCommunity:
            communityOwnedTag = ct.find('span', 'relativetime')
            communityOwnedDate = communityOwnedTag.get('title')
            dateObj = datetime.fromisoformat(communityOwnedDate.replace('Z', '+00:00'))
            communityOwnedDate = int(dateObj.timestamp()) 
        migratedOrLockedTag = ct.find('td', 'wmn1').text.strip().lower()
        if "locked" in migratedOrLockedTag and lastLocked and not 'unlocked' in migratedOrLockedTag:
            lockedDateTag = ct.find('span', 'relativetime')
            lockedDate = lockedDateTag.get('title')
            dateObj = datetime.fromisoformat(lockedDate.replace('Z', '+00:00'))
            lockedDate = int(dateObj.timestamp()) 
            lastLocked = False
        if 'unlocked' in migratedOrLockedTag:
            lastLocked = False
        if 'closed' == migratedOrLockedTag and closedDate != None and lastClosed:
            closedReason = ct.find('td', 'event-comment').text.strip()
            questionsByIDDict['closed_reason'] = closedReason
            lastClosed = False
        if "migrated" in migratedOrLockedTag:
            migratedFrom = None
            #DO MIGRATION - Leaving it for now because its too long for only 1 test case. 
    print(f"locked date: {lockedDate}")
    print(f"community owned date: {communityOwnedDate}")
    if lockedDate != None:
        questionsByIDDict['locked_date'] = lockedDate
    if communityOwnedDate != None:
        questionsByIDDict['community_owned_date'] = communityOwnedDate
    
    ownerTR = dateHashTag.pop()
    ownerTD = ownerTR.find_all('td', class_='ws-nowrap')
    creationDateTD = ownerTR.find('td', 'ws-nowrap creation-date')
    creationDateSpan = creationDateTD.find('span', 'relativetime')
    creationDate = creationDateSpan.get('title')
    dateObj = datetime.fromisoformat(creationDate.replace('Z', '+00:00'))
    creationDate = int(dateObj.timestamp())
    
    print(f"creation date: {creationDate}")
    
    count = 0
    theRow = None
    ownerTRCommentTag = None
    protectedDate = None
    isProtected = True
    for td in ownerTD:
        userLinkTag = td.find('a', 'comment-user owner')
        if userLinkTag != None:
            userLink = userLinkTag.get('href')
            ownerDictionary = findUser(userLink)
            print(json.dumps(ownerDictionary, indent=4))
            questionsByIDDict['owner'] = ownerDictionary
        else:
            count = count + 1
    if count == len(ownerTD):
        count2 = 0
        dateHashTag.append(ownerTR)
        for row in dateHashTag:
            ownerTRCommentTag = row.find('td', class_=lambda x: x and x.startswith('wmn1')).text.strip().lower()
            if 'asked' in ownerTRCommentTag:
                theRow = row
                ownerTD2 = row.find_all('td', class_='ws-nowrap')
                
                for td2 in ownerTD2:
                    userLinkTag2 = td2.find('a', 'comment-user owner')
                    if userLinkTag2 != None:
                        userLink2 = userLinkTag2.get('href')
                        ownerDictionary2 = findUser(userLink2)
                        print(json.dumps(ownerDictionary2, indent=4))
                        questionsByIDDict['owner'] = ownerDictionary2
                    else:
                        count2 = count2 + 1
            if 'protected' in ownerTRCommentTag and isProtected and not 'unprotected' in ownerTRCommentTag:
                protectedDateTD = row.find('td', 'ws-nowrap creation-date')
                protectedDateSpan = protectedDateTD.find('span', 'relativetime')
                protectedDate = protectedDateSpan.get('title')
                dateObj = datetime.fromisoformat(protectedDate.replace('Z', '+00:00'))
                protectedDate = int(dateObj.timestamp())
            if 'unprotected' in ownerTRCommentTag:
                isProtected = False
        if count2 == len(ownerTD2):
            print("User type is does not exist")
            if "asked" in ownerTRCommentTag:
                doesNotExistOwner = theRow.find_all('td')[3].text.strip()
                ownerDictionaryDNE = {
                    'display_name':doesNotExistOwner,
                    "user_type":'does not exist'
                }
                print(json.dumps(ownerDictionaryDNE, indent=4))
                questionsByIDDict['owner'] = ownerDictionaryDNE
    
    if count == len(ownerTD):
        creationDateTD = theRow.find('td', 'ws-nowrap creation-date')
    else:
        creationDateTD = ownerTR.find('td', 'ws-nowrap creation-date')
    creationDateSpan = creationDateTD.find('span', 'relativetime')
    creationDate = creationDateSpan.get('title')
    dateObj = datetime.fromisoformat(creationDate.replace('Z', '+00:00'))
    creationDate = int(dateObj.timestamp())
    questionsByIDDict['creation_date'] = creationDate
    
    if protectedDate != None:
        questionsByIDDict['protected_date'] = protectedDate
    else:
        dateHashTag.append(ownerTR)
        isProtected = True
        for row in dateHashTag:
            ownerTRCommentTag = row.find('td', class_=lambda x: x and x.startswith('wmn1')).text.strip().lower()
            print(ownerTRCommentTag)
            if 'protected' in ownerTRCommentTag and isProtected and not 'unprotected' in ownerTRCommentTag:
                protectedDateTD = row.find('td', 'ws-nowrap creation-date')
                protectedDateSpan = protectedDateTD.find('span', 'relativetime')
                protectedDate = protectedDateSpan.get('title')
                dateObj = datetime.fromisoformat(protectedDate.replace('Z', '+00:00'))
                protectedDate = int(dateObj.timestamp())
                questionsByIDDict['protected_date'] = protectedDate
            if 'unprotected' in ownerTRCommentTag:
                isProtected = False
    print('-' * 80)
    keys = [
        'tags', 'migrated_from', 'owner',
        'is_answered', 'view_count', 'closed_date',
        'bounty_amount', 'bounty_closes_date',
        'protected_date', 'accepted_answer_id',
        'answer_count', 'community_owned_date',
        'score', 'locked_date', 'last_activity_date',
        'creation_date', 'last_edit_date',
        'question_id', 'content_license', 'link',
        'closed_reason', 'title'
    ]
    returningDict = {}
    for key in keys:
        if key in questionsByIDDict:
            returningDict[key] = questionsByIDDict[key]

    print(json.dumps(returningDict, indent=4))
    return returningDict

def searchAnswerByID(id):
    
    answersByIDURL = 'https://stackoverflow.com/a/' + str(id)
    time.sleep(0.5)
    answersByIDResponse = requestTheRequest(answersByIDURL)
    answersByIDSoup = BeautifulSoup(answersByIDResponse.text, 'html.parser')
    scoreTagID = 'answer-' + str(id)
    answerDivTag = answersByIDSoup.find('div', id=scoreTagID)
    answerByIDDict = {}
    
    print(f"answer id: {id}")
    answerByIDDict['answer_id'] = int(id)
    
    questionIDTag = answersByIDSoup.find('a', 'question-hyperlink')
    questionIDLink = questionIDTag.get('href')
    questionID = questionIDLink.split('/')[2]
    print(f"question id: {questionID}")
    answerByIDDict['question_id'] = int(questionID)
    
    score = answerDivTag.find('div', class_=lambda x: x and x.startswith('js-vote-count')).text.strip()
    print(f"score: {score}")
    answerByIDDict['score'] = int(score)
    acceptedTag = answerDivTag.find('div', 'js-accepted-answer-indicator flex--item fc-green-400 py6 mtn8')
    isAccepted = False
    if acceptedTag != None:
        isAccepted = True
    print(f"is accepted: {isAccepted}")
    answerByIDDict['is_accepted'] = isAccepted
    
    lastEditedDate = None
    editedTag = answerDivTag.find('div', class_='user-action-time fl-grow1')
    editedSpanTag = editedTag.find('span', class_='relativetime')
    lastEditedDate = editedSpanTag.get('title')
    dateObj = datetime.fromisoformat(lastEditedDate.replace('Z', '+00:00'))
    lastEditedDate = int(dateObj.timestamp())
    print(f"last edited date: {lastEditedDate}")
    
    ifEdited = editedTag.text.strip().lower()
    if 'edited' in ifEdited:
        answerByIDDict['last_edit_date'] = lastEditedDate
    lastEditedDate = editedSpanTag.get('title')
    lastEditedDate = lastEditedDate[:10]
    
    recommendedTag = answerDivTag.find('div', 'js-endorsements')
    recommendedCollective = None
    recommendedCreationDate = None
    if recommendedTag != None:
        
        singleTag = recommendedTag.find('a', class_='js-gps-track')
        if singleTag != None:
            name = singleTag.text.strip()
            link = singleTag.get('href')
            dataGPSTrack = singleTag.get('data-gps-track')
            slugSplitting = dataGPSTrack.split('subcommunity_slug:')[1]
            subcommunitySlug = slugSplitting.split(',')[0].strip()
            TagsURL = 'https://stackoverflow.com' + link + '?tab=tags'
            TagsResponse = requestTheRequest(TagsURL)
            TagsSoup = BeautifulSoup(TagsResponse.text, 'html.parser')
            
            tagTexts = []
            isNext = TagsSoup.find_all('a', 's-pagination--item js-pagination-item')
            
            if not isNext or isNext == None:
                tags = TagsSoup.find_all('a', class_='s-tag post-tag')
                for tag in tags:
                    tagText = tag.text.strip()
                    tagTexts.append(tagText)
            else:
                tags = TagsSoup.find_all('a', class_='s-tag post-tag')
                for tag in tags:
                    tagText = tag.text.strip()
                    tagTexts.append(tagText)
                
                nextButtonTag = isNext.pop()
                checkIfActuallyNext = nextButtonTag.get('rel')
                
                while checkIfActuallyNext[0] == 'next':
                    nextPageLink = nextButtonTag.get('href')
                    TagsPageURL = 'https://stackoverflow.com' + nextPageLink
                    TagsPageResponse = requestTheRequest(TagsPageURL)
                    TagsPageSoup = BeautifulSoup(TagsPageResponse.text, 'html.parser')
                    tags = TagsPageSoup.find_all('a', class_='s-tag post-tag')
                    for tag in tags:
                        tagText = tag.text.strip()
                        tagTexts.append(tagText)
                    isNext = TagsPageSoup.find_all('a', 's-pagination--item js-pagination-item')
                    nextButtonTag = isNext.pop()
                    checkIfActuallyNext = []
                    checkIfActuallyNext = nextButtonTag.get('rel')
                    if not checkIfActuallyNext:
                        checkIfActuallyNext = ['notNext']
            externalLinksURL = 'https://stackoverflow.com' + link
            externalLinksResponse = requestTheRequest(externalLinksURL)
            externalLinksSoup = BeautifulSoup(externalLinksResponse.text, 'html.parser')
            description = externalLinksSoup.find('div', 'fs-body1 fc-black-500 d:fc-black-600 mb6 wmx7').text.strip()
            externalLinksFromSoup = externalLinksSoup.find_all('a', class_='s-link s-link__inherit ml12')
            externalLinksDict = {}
            externalLinks = []
            externalLinksTypes = []
            for el in externalLinksFromSoup:
                actualLink = el.get('href')
                externalLinks.append(actualLink)
                spanForType = el.find('span', 'd-none').text.strip().lower()
                if spanForType == "contact":
                    spanForType = "support"
                externalLinksTypes.append(spanForType)
                externalLinksDict['type'] = spanForType
                externalLinksDict['link'] = actualLink
            
            recommendedCollective = {
            "tags": tagTexts,
                "external_links": [
                    externalLinksDict
                ],
                "description": description,
                "link": link,
                "name": name,
                "slug": subcommunitySlug
            }
            print(json.dumps(recommendedCollective, indent=4))
            
    else:
        print("recommendation: None")
    
    creationYear = lastEditedDate[:4]
    creationMonth = lastEditedDate[5:7]
    creationDay = lastEditedDate[8:10]
    print(f"year: {creationYear}   month: {creationMonth}   day: {creationDay}")
    contentLicense = None
    if int(creationYear) < 2011:
        contentLicense = 'CC BY-SA 2.5'
    elif int(creationYear) == 2011 and int(creationMonth) < 4:
        contentLicense = 'CC BY-SA 2.5'
    elif int(creationYear) == 2011 and int(creationMonth) == 4 and int(creationDay) < 8:
        contentLicense = 'CC BY-SA 2.5'
    elif int(creationYear) < 2018:
        contentLicense = 'CC BY-SA 3.0'
    elif int(creationYear) == 2018 and int(creationMonth) < 5:
        contentLicense = 'CC BY-SA 3.0'
    elif int(creationYear) == 2018 and int(creationMonth) == 5 and int(creationDay) < 2:
        contentLicense = 'CC BY-SA 3.0'
    else:
        contentLicense = 'CC BY-SA 4.0'
    print(f"content license: {contentLicense}")
    answerByIDDict['content_license'] = contentLicense
    
    answersTimelineURL = 'https://stackoverflow.com/posts/' + str(id) + '/timeline'
    answersTimelineResponse = requestTheRequest(answersTimelineURL)
    answersTimelineSoup = BeautifulSoup(answersTimelineResponse.text, 'html.parser')
    
    dateHashTag = answersTimelineSoup.find_all('tr', class_=lambda x: x and x.startswith('datehash-'))
    communityOwnedDate = None
    
    lastLocked = True
    #if they want the latest recommended creation date then leave, if thye want the earliest then take lastRecom out  
    lastRecom = True
    lockedDate = None
    for ct in dateHashTag:
        checkIfCommunity = ct.find('td', 'event-comment').text.strip().lower()
        if "post made community wiki" in checkIfCommunity:
            communityOwnedTag = ct.find('span', 'relativetime')
            communityOwnedDate = communityOwnedTag.get('title')
            dateObj = datetime.fromisoformat(communityOwnedDate.replace('Z', '+00:00'))
            communityOwnedDate = int(dateObj.timestamp())
        if "recommended answer in" in checkIfCommunity and lastRecom:
            recommendedCreationDateTag = ct.find('span', 'relativetime')
            recommendedCreationDate = recommendedCreationDateTag.get('title')
            dateObj = datetime.fromisoformat(recommendedCreationDate.replace('Z', '+00:00'))
            recommendedCreationDate = int(dateObj.timestamp())
            lastRecom = False
        migratedOrLockedTag = ct.find('td', 'wmn1').text.strip().lower()
        if "locked" in migratedOrLockedTag and lastLocked:
            lockedDateTag = ct.find('span', 'relativetime')
            lockedDate = lockedDateTag.get('title')
            dateObj = datetime.fromisoformat(lockedDate.replace('Z', '+00:00'))
            lockedDate = int(dateObj.timestamp())
            lastLocked = False 
        
    print(f"recommended creation date: {recommendedCreationDate}")
    if recommendedTag != None and singleTag != None:
        recomDict = {
            'collective':recommendedCollective,
            'creation_date':recommendedCreationDate
        }
        answerByIDDict['recommendations'] = [recomDict]
    print(f"locked date: {lockedDate}")
    if lockedDate != None:
        answerByIDDict['locked_date'] = lockedDate
    print(f"community owned date: {communityOwnedDate}")
    if communityOwnedDate != None:
        answerByIDDict['community_owned_date'] = communityOwnedDate
    for td in dateHashTag:
        lastActDateTD = td.find_all('td')[4].text.strip()
        if 'CC BY-SA' in lastActDateTD:
            lastActDateTD = td.find('td', 'ws-nowrap creation-date')
            lastActDateSpan = lastActDateTD.find('span', 'relativetime')
            lastActDate = lastActDateSpan.get('title')
            dateObj = datetime.fromisoformat(lastActDate.replace('Z', '+00:00'))
            lastActDate = int(dateObj.timestamp())
            print(f"last activity date: {lastActDate}")
            answerByIDDict['last_activity_date'] = lastActDate
            break
    
    ownerTR = dateHashTag.pop()
    ownerTD = ownerTR.find_all('td', class_='ws-nowrap')
    creationDateTD = ownerTR.find('td', 'ws-nowrap creation-date')
    creationDateSpan = creationDateTD.find('span', 'relativetime')
    creationDate = creationDateSpan.get('title')
    dateObj = datetime.fromisoformat(creationDate.replace('Z', '+00:00'))
    creationDate = int(dateObj.timestamp())
    isPostedByCollective = False
    postedByCollectiveLink = None
    
    print(f"creation date: {creationDate}")
    answerByIDDict['creation_date'] = creationDate
    count = 0
    theRow = None
    ownerTRCommentTag = None
    for td in ownerTD:
        userLinkTag = td.find('a', 'comment-user owner')
        if userLinkTag != None:
            userLink = userLinkTag.get('href')
            ownerDictionary = findUser(userLink)
            print(json.dumps(ownerDictionary, indent=4))
            answerByIDDict['owner'] = ownerDictionary
            pbcTag = ownerTR.find('td', 'event-comment')
            pbcStr = pbcTag.text.strip().lower()
            if "posted by recognized" in pbcStr:
                isPostedByCollective = True
                postedByCollectiveLink = pbcTag.find('a').get('href')
        else:
            count = count + 1
    if count == len(ownerTD):
        
        count2 = 0
        dateHashTag.append(ownerTR)
        for row in dateHashTag:
            ownerTRCommentTag = row.find('td', class_=lambda x: x and x.startswith('wmn1')).text.strip().lower()
            if 'answered' in ownerTRCommentTag:
                theRow = row
                ownerTD2 = row.find_all('td', class_='ws-nowrap')
                for td2 in ownerTD2:
                    userLinkTag2 = td2.find('a', 'comment-user owner')
                    if userLinkTag2 != None:
                        userLink2 = userLinkTag2.get('href')
                        ownerDictionary2 = findUser(userLink2)
                        print(json.dumps(ownerDictionary2, indent=4))
                        answerByIDDict['owner'] = ownerDictionary2
                        pbcTag2 = row.find('td', 'event-comment')
                        pbcStr2 = pbcTag2.text.strip().lower()
                        if "posted by recognized" in pbcStr2:
                            isPostedByCollective = True
                            postedByCollectiveLink = pbcTag2.find('a').get('href')
                    else:
                        count2 = count2 + 1
                break
        if count2 == len(ownerTD2):
            print("User type is does not exist")
            if "answered" in ownerTRCommentTag:
                doesNotExistOwner = theRow.find_all('td')[3].text.strip()
                ownerDictionaryDNE = {
                    'display_name':doesNotExistOwner,
                    "user_type":'does not exist'
                }
                print(json.dumps(ownerDictionaryDNE, indent=4))
                answerByIDDict['owner'] = ownerDictionaryDNE
        
    if isPostedByCollective:
        postedByCollective = [findCollective(postedByCollectiveLink)]
        print(json.dumps(postedByCollective, indent=4))
        answerByIDDict['posted_by_collectives'] = postedByCollective
    
    print('-' * 80)
    keys = [
        'posted_by_collectives', 'recommendations', 'owner',
        'is_accepted', 'community_owned_date', 'score', 'last_activity_date',
        'last_edit_date', 'creation_date', 'answer_id',
        'question_id', 'content_license',
    ]
    returningDict = {}
    for key in keys:
        if key in answerByIDDict:
            returningDict[key] = answerByIDDict[key]

    print(json.dumps(returningDict, indent=4))
    return returningDict
    
def searchQuestionsByIDAnswers(id):
    questionsAnswersByIDURL = 'https://stackoverflow.com/questions/' + str(id)
    time.sleep(0.5)
    questionsAnswersByIDResponse = requestTheRequest(questionsAnswersByIDURL)
    questionsAnswersByIDSoup = BeautifulSoup(questionsAnswersByIDResponse.text, 'html.parser')
    
    allAnswersTag = questionsAnswersByIDSoup.find_all('div', id=lambda x: x and x.startswith('answer-'))
    answersByIDQuestionList = []
    answersByIDQuestionDict = {}
    lastRecom = True
    for ans in allAnswersTag:
        
        answersByIDQuestionDict = {}
        ansID = ans.get('data-answerid')
        print(f"answer id: {ansID}")
        answersByIDQuestionDict['answer_id'] = int(ansID)
        
        print(f"question id: {id}")
        answersByIDQuestionDict['question_id'] = int(id)
        
        score = ans.find('div', class_=lambda x: x and x.startswith('js-vote-count')).text.strip()
        print(f"score: {score}")
        answersByIDQuestionDict['score'] = int(score)
        
        acceptedTag = ans.find('div', 'js-accepted-answer-indicator flex--item fc-green-400 py6 mtn8')
        isAccepted = False
        if acceptedTag != None:
            isAccepted = True
        print(f"is accepted: {isAccepted}")
        answersByIDQuestionDict['is_accepted'] = isAccepted
        
        lastEditedDate = None
        editedTag = ans.find('div', class_='user-action-time fl-grow1')
        editedSpanTag = editedTag.find('span', class_='relativetime')
        lastEditedDate = editedSpanTag.get('title')
        dateObj = datetime.fromisoformat(lastEditedDate.replace('Z', '+00:00'))
        lastEditedDate = int(dateObj.timestamp())
        print(f"last edited date: {lastEditedDate}")
        
        ifEdited = editedTag.text.strip().lower()
        if 'edited' in ifEdited:
            answersByIDQuestionDict['last_edit_date'] = lastEditedDate
        lastEditedDate = editedSpanTag.get('title')
        lastEditedDate = lastEditedDate[:10]
        
        recommendedTag = ans.find('div', 'js-endorsements')
        recommendedCollective = None
        recommendedCreationDate = None
        if recommendedTag != None:
            
            singleTag = recommendedTag.find('a', class_='js-gps-track')
            if singleTag != None:
                name = singleTag.text.strip()
                link = singleTag.get('href')
                dataGPSTrack = singleTag.get('data-gps-track')
                slugSplitting = dataGPSTrack.split('subcommunity_slug:')[1]
                subcommunitySlug = slugSplitting.split(',')[0].strip()
                TagsURL = 'https://stackoverflow.com' + link + '?tab=tags'
                TagsResponse = requestTheRequest(TagsURL)
                TagsSoup = BeautifulSoup(TagsResponse.text, 'html.parser')
                
                tagTexts = []
                isNext = TagsSoup.find_all('a', 's-pagination--item js-pagination-item')
                
                if not isNext or isNext == None:
                    tags = TagsSoup.find_all('a', class_='s-tag post-tag')
                    for tag in tags:
                        tagText = tag.text.strip()
                        tagTexts.append(tagText)
                else:
                    tags = TagsSoup.find_all('a', class_='s-tag post-tag')
                    for tag in tags:
                        tagText = tag.text.strip()
                        tagTexts.append(tagText)
                    
                    nextButtonTag = isNext.pop()
                    checkIfActuallyNext = nextButtonTag.get('rel')
                    
                    while checkIfActuallyNext[0] == 'next':
                        nextPageLink = nextButtonTag.get('href')
                        TagsPageURL = 'https://stackoverflow.com' + nextPageLink
                        TagsPageResponse = requestTheRequest(TagsPageURL)
                        TagsPageSoup = BeautifulSoup(TagsPageResponse.text, 'html.parser')
                        tags = TagsPageSoup.find_all('a', class_='s-tag post-tag')
                        for tag in tags:
                            tagText = tag.text.strip()
                            tagTexts.append(tagText)
                        isNext = TagsPageSoup.find_all('a', 's-pagination--item js-pagination-item')
                        nextButtonTag = isNext.pop()
                        checkIfActuallyNext = []
                        checkIfActuallyNext = nextButtonTag.get('rel')
                        if not checkIfActuallyNext:
                            checkIfActuallyNext = ['notNext']
                externalLinksURL = 'https://stackoverflow.com' + link
                externalLinksResponse = requestTheRequest(externalLinksURL)
                externalLinksSoup = BeautifulSoup(externalLinksResponse.text, 'html.parser')
                description = externalLinksSoup.find('div', 'fs-body1 fc-black-500 d:fc-black-600 mb6 wmx7').text.strip()
                externalLinksFromSoup = externalLinksSoup.find_all('a', class_='s-link s-link__inherit ml12')
                externalLinksDict = {}
                externalLinks = []
                externalLinksTypes = []
                for el in externalLinksFromSoup:
                    actualLink = el.get('href')
                    externalLinks.append(actualLink)
                    spanForType = el.find('span', 'd-none').text.strip().lower()
                    if spanForType == "contact":
                        spanForType = "support"
                    externalLinksTypes.append(spanForType)
                    externalLinksDict['type'] = spanForType
                    externalLinksDict['link'] = actualLink
                
                recommendedCollective = {
                "tags": tagTexts,
                    "external_links": [
                        externalLinksDict
                    ],
                    "description": description,
                    "link": link,
                    "name": name,
                    "slug": subcommunitySlug
                }
                print(json.dumps(recommendedCollective, indent=4))
                
        else:
            print("recommendation: None")
        
        creationYear = lastEditedDate[:4]
        creationMonth = lastEditedDate[5:7]
        creationDay = lastEditedDate[8:10]
        print(f"year: {creationYear}   month: {creationMonth}   day: {creationDay}")
        contentLicense = None
        if int(creationYear) < 2011:
            contentLicense = 'CC BY-SA 2.5'
        elif int(creationYear) == 2011 and int(creationMonth) < 4:
            contentLicense = 'CC BY-SA 2.5'
        elif int(creationYear) == 2011 and int(creationMonth) == 4 and int(creationDay) < 8:
            contentLicense = 'CC BY-SA 2.5'
        elif int(creationYear) < 2018:
            contentLicense = 'CC BY-SA 3.0'
        elif int(creationYear) == 2018 and int(creationMonth) < 5:
            contentLicense = 'CC BY-SA 3.0'
        elif int(creationYear) == 2018 and int(creationMonth) == 5 and int(creationDay) < 2:
            contentLicense = 'CC BY-SA 3.0'
        else:
            contentLicense = 'CC BY-SA 4.0'
        print(f"content license: {contentLicense}")
        answersByIDQuestionDict['content_license'] = contentLicense
        
        answersTimelineURL = 'https://stackoverflow.com/posts/' + ansID + '/timeline'
        time.sleep(1)
        answersTimelineResponse = requestTheRequest(answersTimelineURL)
        answersTimelineSoup = BeautifulSoup(answersTimelineResponse.text, 'html.parser')
        
        dateHashTag = answersTimelineSoup.find_all('tr', class_=lambda x: x and x.startswith('datehash-'))
        communityOwnedDate = None
        
        lastLocked = True
        #if they want the latest recommended creation date then leave, if thye want the earliest then take lastRecom out  
        lastRecom = True
        lockedDate = None
        for ct in dateHashTag:
            checkIfCommunity = ct.find('td', 'event-comment').text.strip().lower()
            if "post made community wiki" in checkIfCommunity:
                communityOwnedTag = ct.find('span', 'relativetime')
                communityOwnedDate = communityOwnedTag.get('title')
                dateObj = datetime.fromisoformat(communityOwnedDate.replace('Z', '+00:00'))
                communityOwnedDate = int(dateObj.timestamp())
            if "recommended answer in" in checkIfCommunity and lastRecom:
                recommendedCreationDateTag = ct.find('span', 'relativetime')
                recommendedCreationDate = recommendedCreationDateTag.get('title')
                dateObj = datetime.fromisoformat(recommendedCreationDate.replace('Z', '+00:00'))
                recommendedCreationDate = int(dateObj.timestamp())
                lastRecom = False
            migratedOrLockedTag = ct.find('td', 'wmn1').text.strip().lower()
            if "locked" in migratedOrLockedTag and lastLocked:
                lockedDateTag = ct.find('span', 'relativetime')
                lockedDate = lockedDateTag.get('title')
                dateObj = datetime.fromisoformat(lockedDate.replace('Z', '+00:00'))
                lockedDate = int(dateObj.timestamp())
                lastLocked = False 
            
        print(f"recommended creation date: {recommendedCreationDate}")
        if recommendedTag != None and singleTag != None:
            recomDict = {
                'collective':recommendedCollective,
                'creation_date':recommendedCreationDate
            }
            answersByIDQuestionDict['recommendations'] = [recomDict]
        print(f"locked date: {lockedDate}")
        if lockedDate != None:
            answersByIDQuestionDict['locked_date'] = lockedDate
        print(f"community owned date: {communityOwnedDate}")
        if communityOwnedDate != None:
            answersByIDQuestionDict['community_owned_date'] = communityOwnedDate
        for td in dateHashTag:
            lastActDateTD = td.find_all('td')[4].text.strip()
            if 'CC BY-SA' in lastActDateTD:
                lastActDateTD = td.find('td', 'ws-nowrap creation-date')
                lastActDateSpan = lastActDateTD.find('span', 'relativetime')
                lastActDate = lastActDateSpan.get('title')
                dateObj = datetime.fromisoformat(lastActDate.replace('Z', '+00:00'))
                lastActDate = int(dateObj.timestamp())
                print(f"last activity date: {lastActDate}")
                answersByIDQuestionDict['last_activity_date'] = lastActDate
                break
        
        ownerTR = dateHashTag.pop()
        ownerTD = ownerTR.find_all('td', class_='ws-nowrap')
        creationDateTD = ownerTR.find('td', 'ws-nowrap creation-date')
        creationDateSpan = creationDateTD.find('span', 'relativetime')
        creationDate = creationDateSpan.get('title')
        dateObj = datetime.fromisoformat(creationDate.replace('Z', '+00:00'))
        creationDate = int(dateObj.timestamp())
        isPostedByCollective = False
        postedByCollectiveLink = None
        
        print(f"creation date: {creationDate}")
        answersByIDQuestionDict['creation_date'] = creationDate
        count = 0
        theRow = None
        ownerTRCommentTag = None
        for td in ownerTD:
            userLinkTag = td.find('a', 'comment-user owner')
            if userLinkTag != None:
                userLink = userLinkTag.get('href')
                ownerDictionary = findUser(userLink)
                print(json.dumps(ownerDictionary, indent=4))
                answersByIDQuestionDict['owner'] = ownerDictionary
                pbcTag = ownerTR.find('td', 'event-comment')
                pbcStr = pbcTag.text.strip().lower()
                if "posted by recognized" in pbcStr:
                    isPostedByCollective = True
                    postedByCollectiveLink = pbcTag.find('a').get('href')
            else:
                count = count + 1
        if count == len(ownerTD):
            
            count2 = 0
            dateHashTag.append(ownerTR)
            for row in dateHashTag:
                ownerTRCommentTag = row.find('td', class_=lambda x: x and x.startswith('wmn1')).text.strip().lower()
                if 'answered' in ownerTRCommentTag:
                    theRow = row
                    ownerTD2 = row.find_all('td', class_='ws-nowrap')
                    for td2 in ownerTD2:
                        userLinkTag2 = td2.find('a', 'comment-user owner')
                        if userLinkTag2 != None:
                            userLink2 = userLinkTag2.get('href')
                            ownerDictionary2 = findUser(userLink2)
                            print(json.dumps(ownerDictionary2, indent=4))
                            answersByIDQuestionDict['owner'] = ownerDictionary2
                            pbcTag2 = row.find('td', 'event-comment')
                            pbcStr2 = pbcTag2.text.strip().lower()
                            if "posted by recognized" in pbcStr2:
                                isPostedByCollective = True
                                postedByCollectiveLink = pbcTag2.find('a').get('href')
                        else:
                            count2 = count2 + 1
                    break
            if count2 == len(ownerTD2):
                print("User type is does not exist")
                if "answered" in ownerTRCommentTag:
                    doesNotExistOwner = theRow.find_all('td')[3].text.strip()
                    ownerDictionaryDNE = {
                        'display_name':doesNotExistOwner,
                        "user_type":'does not exist'
                    }
                    print(json.dumps(ownerDictionaryDNE, indent=4))
                    answersByIDQuestionDict['owner'] = ownerDictionaryDNE
            
        if isPostedByCollective:
            postedByCollective = [findCollective(postedByCollectiveLink)]
            print(json.dumps(postedByCollective, indent=4))
            answersByIDQuestionDict['posted_by_collectives'] = postedByCollective
        
        print('-' * 80)
        keys = [
            'posted_by_collectives', 'recommendations', 'owner',
            'is_accepted', 'community_owned_date', 'score', 'last_activity_date',
            'last_edit_date', 'creation_date', 'answer_id',
            'question_id', 'content_license',
        ]
        returningDict = {}
        for key in keys:
            if key in answersByIDQuestionDict:
                returningDict[key] = answersByIDQuestionDict[key]

        print(json.dumps(returningDict, indent=4))
        
        print('-' * 80)
        answersByIDQuestionList.append(returningDict)
    
    isNext = questionsAnswersByIDSoup.find_all('a', 's-pagination--item js-pagination-item')
    
    if not isNext or isNext == None:
        print(json.dumps(answersByIDQuestionList, indent=4))
        return answersByIDQuestionList
    else:
        
        nextButtonTag = isNext.pop()
        checkIfActuallyNext = nextButtonTag.get('rel')
        
        while checkIfActuallyNext[0] == 'next':
            nextPageLink = nextButtonTag.get('href')
            TagsPageURL = 'https://stackoverflow.com' + nextPageLink
            time.sleep(0.5)
            TagsPageResponse = requestTheRequest(TagsPageURL)
            TagsPageSoup = BeautifulSoup(TagsPageResponse.text, 'html.parser')
            
            allAnswersTag = TagsPageSoup.find_all('div', id=lambda x: x and x.startswith('answer-'))
            answersByIDQuestionDict = {}
            lastRecom = True
            for ans in allAnswersTag:
                
                answersByIDQuestionDict = {}
                ansID = ans.get('data-answerid')
                print(f"answer id: {ansID}")
                answersByIDQuestionDict['answer_id'] = int(ansID)
                
                print(f"question id: {id}")
                answersByIDQuestionDict['question_id'] = int(id)
                
                score = ans.find('div', class_=lambda x: x and x.startswith('js-vote-count')).text.strip()
                print(f"score: {score}")
                answersByIDQuestionDict['score'] = int(score)
                
                acceptedTag = ans.find('div', 'js-accepted-answer-indicator flex--item fc-green-400 py6 mtn8')
                isAccepted = False
                if acceptedTag != None:
                    isAccepted = True
                print(f"is accepted: {isAccepted}")
                answersByIDQuestionDict['is_accepted'] = isAccepted
                
                lastEditedDate = None
                editedTag = ans.find('div', class_='user-action-time fl-grow1')
                editedSpanTag = editedTag.find('span', class_='relativetime')
                lastEditedDate = editedSpanTag.get('title')
                dateObj = datetime.fromisoformat(lastEditedDate.replace('Z', '+00:00'))
                lastEditedDate = int(dateObj.timestamp())
                print(f"last edited date: {lastEditedDate}")
                
                ifEdited = editedTag.text.strip().lower()
                if 'edited' in ifEdited:
                    answersByIDQuestionDict['last_edit_date'] = lastEditedDate
                lastEditedDate = editedSpanTag.get('title')
                lastEditedDate = lastEditedDate[:10]
                
                recommendedTag = ans.find('div', 'js-endorsements')
                recommendedCollective = None
                recommendedCreationDate = None
                if recommendedTag != None:
                    
                    singleTag = recommendedTag.find('a', class_='js-gps-track')
                    if singleTag != None:
                        name = singleTag.text.strip()
                        link = singleTag.get('href')
                        dataGPSTrack = singleTag.get('data-gps-track')
                        slugSplitting = dataGPSTrack.split('subcommunity_slug:')[1]
                        subcommunitySlug = slugSplitting.split(',')[0].strip()
                        TagsURL = 'https://stackoverflow.com' + link + '?tab=tags'
                        TagsResponse = requestTheRequest(TagsURL)
                        TagsSoup = BeautifulSoup(TagsResponse.text, 'html.parser')
                        
                        tagTexts = []
                        isNext = TagsSoup.find_all('a', 's-pagination--item js-pagination-item')
                        
                        if not isNext or isNext == None:
                            tags = TagsSoup.find_all('a', class_='s-tag post-tag')
                            for tag in tags:
                                tagText = tag.text.strip()
                                tagTexts.append(tagText)
                        else:
                            tags = TagsSoup.find_all('a', class_='s-tag post-tag')
                            for tag in tags:
                                tagText = tag.text.strip()
                                tagTexts.append(tagText)
                            
                            nextButtonTag = isNext.pop()
                            checkIfActuallyNext = nextButtonTag.get('rel')
                            
                            while checkIfActuallyNext[0] == 'next':
                                nextPageLink = nextButtonTag.get('href')
                                TagsPageURL = 'https://stackoverflow.com' + nextPageLink
                                TagsPageResponse = requestTheRequest(TagsPageURL)
                                TagsPageSoup = BeautifulSoup(TagsPageResponse.text, 'html.parser')
                                tags = TagsPageSoup.find_all('a', class_='s-tag post-tag')
                                for tag in tags:
                                    tagText = tag.text.strip()
                                    tagTexts.append(tagText)
                                isNext = TagsPageSoup.find_all('a', 's-pagination--item js-pagination-item')
                                nextButtonTag = isNext.pop()
                                checkIfActuallyNext = []
                                checkIfActuallyNext = nextButtonTag.get('rel')
                                if not checkIfActuallyNext:
                                    checkIfActuallyNext = ['notNext']
                        externalLinksURL = 'https://stackoverflow.com' + link
                        externalLinksResponse = requestTheRequest(externalLinksURL)
                        externalLinksSoup = BeautifulSoup(externalLinksResponse.text, 'html.parser')
                        description = externalLinksSoup.find('div', 'fs-body1 fc-black-500 d:fc-black-600 mb6 wmx7').text.strip()
                        externalLinksFromSoup = externalLinksSoup.find_all('a', class_='s-link s-link__inherit ml12')
                        externalLinksDict = {}
                        externalLinks = []
                        externalLinksTypes = []
                        for el in externalLinksFromSoup:
                            actualLink = el.get('href')
                            externalLinks.append(actualLink)
                            spanForType = el.find('span', 'd-none').text.strip().lower()
                            if spanForType == "contact":
                                spanForType = "support"
                            externalLinksTypes.append(spanForType)
                            externalLinksDict['type'] = spanForType
                            externalLinksDict['link'] = actualLink
                        
                        recommendedCollective = {
                        "tags": tagTexts,
                            "external_links": [
                                externalLinksDict
                            ],
                            "description": description,
                            "link": link,
                            "name": name,
                            "slug": subcommunitySlug
                        }
                        print(json.dumps(recommendedCollective, indent=4))
                        
                else:
                    print("recommendation: None")
                
                creationYear = lastEditedDate[:4]
                creationMonth = lastEditedDate[5:7]
                creationDay = lastEditedDate[8:10]
                print(f"year: {creationYear}   month: {creationMonth}   day: {creationDay}")
                contentLicense = None
                if int(creationYear) < 2011:
                    contentLicense = 'CC BY-SA 2.5'
                elif int(creationYear) == 2011 and int(creationMonth) < 4:
                    contentLicense = 'CC BY-SA 2.5'
                elif int(creationYear) == 2011 and int(creationMonth) == 4 and int(creationDay) < 8:
                    contentLicense = 'CC BY-SA 2.5'
                elif int(creationYear) < 2018:
                    contentLicense = 'CC BY-SA 3.0'
                elif int(creationYear) == 2018 and int(creationMonth) < 5:
                    contentLicense = 'CC BY-SA 3.0'
                elif int(creationYear) == 2018 and int(creationMonth) == 5 and int(creationDay) < 2:
                    contentLicense = 'CC BY-SA 3.0'
                else:
                    contentLicense = 'CC BY-SA 4.0'
                print(f"content license: {contentLicense}")
                answersByIDQuestionDict['content_license'] = contentLicense
                
                answersTimelineURL = 'https://stackoverflow.com/posts/' + ansID + '/timeline'
                answersTimelineResponse = requestTheRequest(answersTimelineURL)
                answersTimelineSoup = BeautifulSoup(answersTimelineResponse.text, 'html.parser')
                
                dateHashTag = answersTimelineSoup.find_all('tr', class_=lambda x: x and x.startswith('datehash-'))
                communityOwnedDate = None
                
                lastLocked = True
                #if they want the latest recommended creation date then leave, if thye want the earliest then take lastRecom out  
                lastRecom = True
                lockedDate = None
                for ct in dateHashTag:
                    checkIfCommunity = ct.find('td', 'event-comment').text.strip().lower()
                    if "post made community wiki" in checkIfCommunity:
                        communityOwnedTag = ct.find('span', 'relativetime')
                        communityOwnedDate = communityOwnedTag.get('title')
                        dateObj = datetime.fromisoformat(communityOwnedDate.replace('Z', '+00:00'))
                        communityOwnedDate = int(dateObj.timestamp())
                    if "recommended answer in" in checkIfCommunity and lastRecom:
                        recommendedCreationDateTag = ct.find('span', 'relativetime')
                        recommendedCreationDate = recommendedCreationDateTag.get('title')
                        dateObj = datetime.fromisoformat(recommendedCreationDate.replace('Z', '+00:00'))
                        recommendedCreationDate = int(dateObj.timestamp())
                        lastRecom = False
                    migratedOrLockedTag = ct.find('td', 'wmn1').text.strip().lower()
                    if "locked" in migratedOrLockedTag and lastLocked:
                        lockedDateTag = ct.find('span', 'relativetime')
                        lockedDate = lockedDateTag.get('title')
                        dateObj = datetime.fromisoformat(lockedDate.replace('Z', '+00:00'))
                        lockedDate = int(dateObj.timestamp())
                        lastLocked = False 
                    
                print(f"recommended creation date: {recommendedCreationDate}")
                if recommendedTag != None and singleTag != None:
                    recomDict = {
                        'collective':recommendedCollective,
                        'creation_date':recommendedCreationDate
                    }
                    answersByIDQuestionDict['recommendations'] = [recomDict]
                print(f"locked date: {lockedDate}")
                if lockedDate != None:
                    answersByIDQuestionDict['locked_date'] = lockedDate
                print(f"community owned date: {communityOwnedDate}")
                if communityOwnedDate != None:
                    answersByIDQuestionDict['community_owned_date'] = communityOwnedDate
                for td in dateHashTag:
                    lastActDateTD = td.find_all('td')[4].text.strip()
                    if 'CC BY-SA' in lastActDateTD:
                        lastActDateTD = td.find('td', 'ws-nowrap creation-date')
                        lastActDateSpan = lastActDateTD.find('span', 'relativetime')
                        lastActDate = lastActDateSpan.get('title')
                        dateObj = datetime.fromisoformat(lastActDate.replace('Z', '+00:00'))
                        lastActDate = int(dateObj.timestamp())
                        print(f"last activity date: {lastActDate}")
                        answersByIDQuestionDict['last_activity_date'] = lastActDate
                        break
                
                ownerTR = dateHashTag.pop()
                ownerTD = ownerTR.find_all('td', class_='ws-nowrap')
                creationDateTD = ownerTR.find('td', 'ws-nowrap creation-date')
                creationDateSpan = creationDateTD.find('span', 'relativetime')
                creationDate = creationDateSpan.get('title')
                dateObj = datetime.fromisoformat(creationDate.replace('Z', '+00:00'))
                creationDate = int(dateObj.timestamp())
                isPostedByCollective = False
                postedByCollectiveLink = None
                
                print(f"creation date: {creationDate}")
                answersByIDQuestionDict['creation_date'] = creationDate
                count = 0
                theRow = None
                ownerTRCommentTag = None
                for td in ownerTD:
                    userLinkTag = td.find('a', 'comment-user owner')
                    if userLinkTag != None:
                        userLink = userLinkTag.get('href')
                        ownerDictionary = findUser(userLink)
                        print(json.dumps(ownerDictionary, indent=4))
                        answersByIDQuestionDict['owner'] = ownerDictionary
                        pbcTag = ownerTR.find('td', 'event-comment')
                        pbcStr = pbcTag.text.strip().lower()
                        if "posted by recognized" in pbcStr:
                            isPostedByCollective = True
                            postedByCollectiveLink = pbcTag.find('a').get('href')
                    else:
                        count = count + 1
                if count == len(ownerTD):
                    
                    count2 = 0
                    dateHashTag.append(ownerTR)
                    for row in dateHashTag:
                        
                        ownerTRCommentTag = row.find('td', class_=lambda x: x and x.startswith('wmn1')).text.strip().lower()
                        if 'answered' in ownerTRCommentTag:
                            theRow = row
                            ownerTD2 = row.find_all('td', class_='ws-nowrap')
                            for td2 in ownerTD2:
                                userLinkTag2 = td2.find('a', 'comment-user owner')
                                if userLinkTag2 != None:
                                    userLink2 = userLinkTag2.get('href')
                                    ownerDictionary2 = findUser(userLink2)
                                    print(json.dumps(ownerDictionary2, indent=4))
                                    answersByIDQuestionDict['owner'] = ownerDictionary2
                                    pbcTag2 = row.find('td', 'event-comment')
                                    pbcStr2 = pbcTag2.text.strip().lower()
                                    if "posted by recognized" in pbcStr2:
                                        isPostedByCollective = True
                                        postedByCollectiveLink = pbcTag2.find('a').get('href')
                                else:
                                    count2 = count2 + 1
                            break
                    if count2 == len(ownerTD2):
                        print("User type is does not exist")
                        if "answered" in ownerTRCommentTag:
                            doesNotExistOwner = theRow.find_all('td')[3].text.strip()
                            ownerDictionaryDNE = {
                                'display_name':doesNotExistOwner,
                                "user_type":'does not exist'
                            }
                            print(json.dumps(ownerDictionaryDNE, indent=4))
                            answersByIDQuestionDict['owner'] = ownerDictionaryDNE
                    
                if isPostedByCollective:
                    postedByCollective = [findCollective(postedByCollectiveLink)]
                    print(json.dumps(postedByCollective, indent=4))
                    answersByIDQuestionDict['posted_by_collectives'] = postedByCollective
                
                print('-' * 80)
                keys = [
                    'posted_by_collectives', 'recommendations', 'owner',
                    'is_accepted', 'community_owned_date', 'score', 'last_activity_date',
                    'last_edit_date', 'creation_date', 'answer_id',
                    'question_id', 'content_license',
                ]
                returningDict = {}
                for key in keys:
                    if key in answersByIDQuestionDict:
                        returningDict[key] = answersByIDQuestionDict[key]

                print(json.dumps(returningDict, indent=4))
                
                print('-' * 80)
                answersByIDQuestionList.append(returningDict)
            
            isNext = TagsPageSoup.find_all('a', 's-pagination--item js-pagination-item')
            nextButtonTag = isNext.pop()
            checkIfActuallyNext = []
            checkIfActuallyNext = nextButtonTag.get('rel')
            if not checkIfActuallyNext:
                checkIfActuallyNext = ['notNext']
    
    print(json.dumps(answersByIDQuestionList, indent=4))
    return answersByIDQuestionList

if __name__ == "__main__":
    
    #searchCollectives()
    #searchQuestions()
    #searchQuestionsByID(549)
    #searchAnswerByID(78898233)
    #searchQuestionsByIDAnswers(927358)
    port = int(os.getenv('STACKOVERFLOW_API_PORT', 5002))
    app.run(port=port)
    
    #78898233 for answers posted by collectives
    #60496 for answers recommended by collectives
    #5963269 questions by ID answers
    # everything with questions: /questions/20829860;2003505;927358;3577641;74790323;549
    # everything with answers: /answers/78898233;60496;11227902;11227877;11237235;11303693
    # everything with questions/ids/answers: /questions/78898216;60174;11227809;2003505/answers      5767325 - 150 answers
    #migrated from id - 74790323
    # change last avtivity date so that it looks for last history date (exclusing bots) 
    # for filters do : &filter=none (empty json file), &filter=default (normal), &filter=total (total number of questions/answers), &filter=withbody (idk)
