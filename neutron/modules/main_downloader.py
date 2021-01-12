# neutron -- a download manager

import re
import os
import logging
import platform
# import warnings
import mimetypes
import urllib.parse
import requests
from .constants import *

# warnings.filterwarnings('ignore')           # verify=False
logger = logging.getLogger(__name__)

try:
    from tqdm import tqdm
    logger.debug('tqdm installation found.')
    _tqdm_ = True
    _tqdm_ = False
except ImportError:
    logger.debug('tqdm installation NOT found.')
    _tqdm_ = False


class Downloader:
    ''':dUrl: - url to download from
    :sess: None - `requests.Session` obj
    :customName: None - Name for the file
    :customPath: None - Full path to the directory where file
                        will be downloaded (exclude filename)
    '''

    groupExt = mainExtensions

    def __str__(self):
        return self.downloadPath

    def __init__(
        self,
        dUrl,
        params: dict = None,
        sess=None,
        customName: str = None,
        customPath: str = None,
        overwrite: bool = False):

        if params:
            try: dUrl += '?' + urllib.parse.urlencode(params)
            except TypeError as e:
                logger.error('params should be of type dict or a mapping')
                raise e

        logger.debug('Downloading from\n %s', dUrl)
        self.dUrl = dUrl
        self.customName = customName
        self.customPath = customPath
        self.overwrite = overwrite
        self.sess = sess
        
        if self.customPath is None:
            self.dwnld = os.path.join(os.path.expanduser('~'), 'Downloads')
            # only for download dir
            self.makeDirIfNoDir(self.dwnld)
        else:
            os.makedirs(self.customPath, exist_ok=True)

        if self.sess is None:
            self.sess = requests.Session()

        self.downloadPath = self.mainDownloader()

    def mainDownloader(self):
        # defer downloading the resp body until you access the Response.content attribute
        # by setting stream=True. used for figuring out size, name, ext of file
        # from headers only before downloading actual data
        try:
            req = requests.Request('GET', self.dUrl)
            self.prep = self.sess.prepare_request(req)
            self.chunkSize = 1024 * 8        
            r = self.sess.send(self.prep, stream=True, verify=True, timeout=40)
        
        except requests.exceptions.RequestException:
            # sometimes new session cannot be created. dunno y.
            r = self.sess.get(self.dUrl, stream=True, verify=True, timeout=40)
        r.raise_for_status()
        
        rHdrs = {k.lower(): v for k, v in r.headers.items()}
        totalSize = int(rHdrs.get('content-length', 0))
        if not self.customName:
            # this may or may not have extension
            defaultName = r.url.split('/')[-1]
            # order matters
            fullname = self.tryContentDisposition(rHdrs, preferThis=None) or \
                        self.hasExt(defaultName) or \
                        self.tryContentType(rHdrs, defaultName) or \
                        None
        else:
            # this may or may not have extension
            givenName = self.customName
            # order matters
            fullname = self.hasExt(givenName) or \
                        self.tryContentDisposition(rHdrs, preferThis=givenName) or \
                        self.tryContentType(rHdrs, givenName) or \
                        None
        
        if fullname is None: return None, "couldn't guess the extension"
        fullname = removeInvalidCharInPath(fullname)
        ext = fullname.split('.')[-1]

        if self.customPath: # if customPath is provided dont categorize
            fullPath = os.path.join(self.customPath, fullname)# has extension
        else:
            fullPath = os.path.join(self.catgPath(ext), fullname)# has extension
        if not self.overwrite: fullPath = enumIfFileExists(fullPath)
        
        with open(fullPath, 'wb') as f:
            if totalSize == 0:
                logger.warning('NO FILE SIZE!! PROGRESS BAR WON\'T BE AVAILABLE!!')
            try:
                if _tqdm_:
                    for chunk in tqdm(
                            iterable=r.iter_content(chunk_size=self.chunkSize),
                            total=(totalSize//self.chunkSize),
                            unit='KB'):
                        f.write(chunk)
                else:
                    for chunk in ProgressBar(
                            iterable=r.iter_content(chunk_size=self.chunkSize),
                            total=totalSize):
                        f.write(chunk)

            finally:
                r.close()

        logger.debug(f'Downloaded to: {fullPath}')
        return fullPath

    @staticmethod 
    def tryContentDisposition(respHeaders, preferThis=None):
        '''returns Full Name with extension else None'''
        haystack = respHeaders.get('content-disposition', None)
        if haystack:
            # some dont have quotations. see:
            # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition
            needle = re.compile(r'.*filename\*?="?(.*)')
            needle = needle.search(haystack)
            if not needle: return None
            nameWithExt = needle.groups()[0].rstrip(';').rstrip('"')
            if not preferThis: 
                return nameWithExt
            else:
                return preferThis + '.' + nameWithExt.split('.')[-1]

        return None

    @staticmethod
    def hasExt(string):
        '''returns Full Name with extension else None'''
        if mimetypes.guess_type(string)[0] is not None: # then we know it has extension
            return string

        return None

    @staticmethod
    def tryContentType(respHeaders, string):
        '''returns Full Name with extension else None'''
        conType = respHeaders.get('content-type', None)
        ext = mimetypes.guess_extension(conType)
        
        if ext is not None:
            logger.debug('appending extension', ext)
            return string + ext

        return None

    def catgPath(self, urlOrExt):
        # if the extension is present in dict, insert it in respective dirs.        
        for catg in self.groupExt.keys():
            if urlOrExt.endswith(self.groupExt[catg]):
                return os.path.join(self.dwnld, catg)
        
        # else file will be downloaded to Downloads directory
        else:
            logger.debug('cannot categorize!')
            return self.dwnld

    def makeDirIfNoDir(self, dwnldFolder):
        """Only for Downloads folder to categorize files"""
        for folder in self.groupExt.keys():
            os.makedirs(os.path.join(dwnldFolder, folder), exist_ok=True)
        return 'All required folder are available.'

def removeInvalidCharInPath(p):
    splitted = p.split(os.path.sep)
    # if 'windows' in platform.system().lower():
    invalids = '\\/:?*<>|"'
    for i in range(len(splitted)):
        for invalid in invalids:
            splitted[i] = splitted[i].replace(invalid, '')

    return (os.path.sep).join(splitted)
        
def enumIfFileExists(fp):
    '''check if file already exists. if it does, tries to number it.'''
    i = 0
    parent, fullname = os.path.split(fp)
    # '.'.join(f.split('.')[:-1]), f.split('.')[-1]
    justname, dotExt = os.path.splitext(fullname)

    def keepChecking(innerFilename):
        nonlocal i
        if innerFilename in os.listdir(parent):
            i += 1
            return keepChecking(f'{justname}_({i}){dotExt}')
        else:
            return innerFilename
    return os.path.join(parent, keepChecking(fullname))


class ProgressBar:
    '''
    iterable: response.iter_content
    totalSize: bytes
    '''    

    def __init__(self, iterable, total): 
        self.iterable = iterable    # r.iter_content
        self.chunkSize = None
        self.totalSize = total
        if self.totalSize == 0:
            self.totalSize = 1      # avoid ZeroDivisionError
            self.chunkSize = 0      # easy fix; makes progress bar stuck at 0%
                                    # len(self.iterable.__next__()) gives chunk size
        self.currCount = 0
        self.toDisplay = '■'
        self.width = 30             # in ch
        self.percentComplete = 0

    def __iter__(self):
        return self

    def __next__(self):
        nextChunk = self.iterable.__next__()
        if self.chunkSize is None:                      # only the first time
            # get chunkSize from .iter_content()
            self.chunkSize = len(nextChunk)

        # since chunkSize is taken from the first chunk, it will always be <totalSize.
        p = (self.chunkSize * self.currCount) / self.totalSize # range [0-1]
        per = f'{p:.0%}'
        self.currCount += 1

        # only 100 max lines are printed. guess y.
        if self.percentComplete == per:
            # if prev and current % is same: don't print to stdout
            return nextChunk
        
        self.percentComplete = per
        print(f"{self.percentComplete:<4}|{self.toDisplay * int(p * self.width)}" \
                .ljust(self.width+4) + '|') # +4 cuz 4 char is covered by %
        
        # easier hardcoded way
        # print(f"{self.percentComplete:<4}|{self.toDisplay * int(p * 10):<10}|")
        return nextChunk


if __name__ == "__main__":

    FORMAT = '[%(module)s] :: %(levelname)s :: %(message)s'
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
