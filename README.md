# Neutron
A download manager

**Features**

 - Categorize downloaded files automatically
 - Progress Bar
 - Provide a Custom name and location for download file or directory
 - names the file as sent by the server or tries to guess it.
 - Enumerates if a file with same name already exists(default) or overwrites it.
 - Supports requests session and query params using dict.

**Installation**

`pip install git+https://git@github.com/zznixt07/neutron_.git`

**Requirements**
 - requests
 - tqdm (optional)
 
  `pip install requests tqdm`

**Usage**

```
import neutron

# download image from 'https://cdn.pixabay.com/photo/2019/10/04/18/36/milky-way-4526277_1280.jpg'
neutron.get('https://cdn.pixabay.com/photo/2019/10/04/18/36/milky-way-4526277_1280.jpg')

# download video from 'https://file-examples-com.github.io/uploads/2020/03/file_example_WEBM_480_900KB.webm'
neutron.get(
    'https://file-examples-com.github.io/uploads/2020/03/file_example_WEBM_480_900KB.webm',
    customName='earthfromspace.webm')

# some download require auth which can be stored in `requests.Session`
import requests
with requests.Session() as sess:
    # ...login and store cookies in `sess`
    neutron.get(
        'https://file-examples-com.github.io/uploads/2020/03/file_example_WEBM_480_900KB.webm',
        sess=sess,
        customName='happy_earth.webm',
        customPath='c:\\')
```
