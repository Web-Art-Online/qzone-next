class QzoneImage:
    pic_bo: str
    richval: str
    
    def __init__(self, pic_bo: str, richval: str):
        self.pic_bo = pic_bo
        self.richval = richval
        
    def parse(resp: dict):
        pic_bo = resp['data']['url'].split('&bo=')[1]

        richval = ",{},{},{},{},{},{},,{},{}".format(resp['data']['albumid'], resp['data']['lloc'],
                                                    resp['data']['sloc'], resp['data']['type'],
                                                    resp['data']['height'], resp['data']['width'],
                                                    resp['data']['height'], resp['data']['width'])
        return QzoneImage(pic_bo=pic_bo, richval=richval)