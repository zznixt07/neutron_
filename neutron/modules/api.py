from .main_downloader import Downloader

def get(dUrl,
        params: dict = None,
        sess=None,
        customName: str = None,
        customPath: str = None,
        overwrite: bool = False) -> str:
    '''
    :dUrl: - url to Download from
    :params: - params in the url as dict
    :sess: None - `requests.Session` obj
    :customName: None - Name for the file
    :customPath: None - Full path to the directory where file
                        will be downloaded (exclude filename)
    :rtype: Path
    '''
    return Downloader(dUrl,
                    params=params,
                    sess=sess,
                    customName=customName,
                    customPath=customPath,
                    overwrite=overwrite).downloadPath

