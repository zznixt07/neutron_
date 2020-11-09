from .main_downloader import Downloader

def get(dUrl, sess=None, customName=None, customPath=None):
    '''
    :dUrl: - url to Download from
    :sess: None - `requests.Session` obj
    :customName: None - Name for the file
    :customPath: None - Full path to the directory where file
                        will be downloaded (exclude filename)
    :rtype: Path
    '''
    return Downloader(dUrl,
                        sess=sess,
                        customName=customName,
                        customPath=customPath).downloadPath
