import json

from qzone.models import QzoneImage

from httpx import Client, AsyncClient

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


class Qzone:
    uin: str
    cookies: dict

    def __init__(self, onebot_url: str, uin: str | int):
        self.uin = str(uin)
        with Client() as client:
            self.cookies = dict(c.split("=") for c in json.loads(
                client.get(f"{onebot_url}/get_cookies?domain=user.qzone.qq.com").text)["data"]["cookies"].replace(" ", "").split(";"))

    async def upload_image(self, base64: bytes) -> QzoneImage:
        async with AsyncClient(timeout=60) as client:
            resp = await client.post("https://up.qzone.qq.com/cgi-bin/upload/cgi_upload_image",
                                     params={"g_tk": self.get_g_tk(),
                                             "uin": self.uin},
                                     data={
                                         "filename": "filename",
                                         "zzpanelkey": "",
                                         "uploadtype": "1",
                                         "albumtype": "7",
                                         "exttype": "0",
                                         "skey": self.cookies["skey"],
                                         "zzpaneluin": self.uin,
                                         "p_uin": self.uin,
                                         "uin": self.uin,
                                         "p_skey": self.cookies["p_skey"],
                                         "output_type": "json",
                                         "qzonetoken": "",
                                         "refer": "shuoshuo",
                                         "charset": "utf-8",
                                         "output_charset": "utf-8",
                                         "upload_hd": "1",
                                         "hd_width": "2048",
                                         "hd_height": "10000",
                                         "hd_quality": "96",
                                         "backUrls": "http://upbak.photo.qzone.qq.com/cgi-bin/upload/cgi_upload_image,"
                                         "http://119.147.64.75/cgi-bin/upload/cgi_upload_image",
                                         "url": f"https://up.qzone.qq.com/cgi-bin/upload/cgi_upload_image?g_tk={self.get_g_tk()}",
                                         "base64": "1",
                                         "picfile": base64.decode(),
                                     }, headers={"Referer": f"https://user.qzone.qq.com/{self.uin}", "Origin": "https://user.qzone.qq.com", "User-Agent": UA})
            if resp.status_code == 200:
                r = json.loads(
                    resp.text[resp.text.find('{'):resp.text.rfind('}') + 1])
                if r.get("ret") != 0:
                    raise RuntimeError(f"上传图片失败[{resp.status_code}]:{resp.text}")
                return QzoneImage.parse(r)
            else:
                raise RuntimeError(f"上传图片失败[{resp.status_code}]:{resp.text}")

    async def publish(self, text: str, images: list[QzoneImage] = []) -> str:
        if not text and not images:
            return None
        pic_bos = []
        richvals = []
        for image in images:
            pic_bos.append(image.pic_bo)
            richvals.append(image.richval)

        async with AsyncClient(timeout=60) as client:
            resp = await client.post(
                url="https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_publish_v6",
                params={
                    "g_tk": self.get_g_tk(),
                    "uin": self.uin,
                },
                cookies=self.cookies,
                data={
                    "syn_tweet_verson": "1",
                    "paramstr": "1",
                    "who": "1",
                    "con": text,
                    "feedversion": "1",
                    "ver": "1",
                    "ugc_right": "1",
                    "to_sign": "0",
                    "hostuin": self.uin,
                    "code_version": "1",
                    "format": "json",
                    "qzreferrer": f"https://user.qzone.qq.com/{self.uin}",
                    "pic_bo": ",".join(pic_bos) if len(images) != 0 else None,
                    "richtype": "1" if len(images) != 0 else None,
                    "richval": '\t'.join(richvals) if len(images) != 0 else None
                }, headers={"User-Agent": UA, "Referer": f"https://user.qzone.qq.com/{self.uin}", "Origin": "https://user.qzone.qq.com"})
            if resp.status_code == 200:
                return resp.json()['tid']
            else:
                raise RuntimeError(resp.text)

    def get_g_tk(self) -> str:
        p_skey = self.cookies["p_skey"]
        hash_val = 5381
        for i in range(len(p_skey)):
            hash_val += (hash_val << 5) + ord(p_skey[i])
        return str(hash_val & 2147483647)