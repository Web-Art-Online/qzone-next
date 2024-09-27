import asyncio
import json
import time
from typing import Union

from qzone.models import QzoneImage

from httpx import AsyncClient, Cookies

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


class Qzone:
    uin: str
    cookies: Cookies
    _updated: int

    def __init__(self, uin: str, cookies: Cookies, updated: int):
        self.uin = uin
        self.cookies = cookies
        self._updated = updated

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

    def __hash__(self):
        return hash(self.uin)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.uin == other.uin
        else:
            return False


async def _get_clientkey(uin: str) -> str:
    local_key_url = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin?s_url=https%3A%2F%2Fhuifu.qq.com%2Findex.html&style=20&appid=715021417" \
        "&proxy_url=https%3A%2F%2Fhuifu.qq.com%2Fproxy.html"
    async with AsyncClient(timeout=15) as client:
        resp = await client.get(local_key_url, headers={"User-Agent": UA})
        pt_local_token = resp.cookies["pt_local_token"]
        client_key_url = f"https://localhost.ptlogin2.qq.com:4301/pt_get_st?clientuin={
            uin}&callback=ptui_getst_CB&r=0.7284667321181328&pt_local_tk={pt_local_token}"
        resp = await client.get(client_key_url, headers={"User-Agent": UA, "Referer": "https://ssl.xui.ptlogin2.qq.com/"})
        if resp.status_code == 400:
            return RuntimeError(f"获取clientkey失败: {resp.text}")
        return resp.cookies["clientkey"]


async def _get_cookies(uin: str, clientkey: str) -> Cookies:
    login_url = f"https://ssl.ptlogin2.qq.com/jump?ptlang=1033&clientuin={uin}&clientkey={clientkey}" \
        f"&u1=https%3A%2F%2Fuser.qzone.qq.com%2F{uin}%2Finfocenter&keyindex=19"
    async with AsyncClient(timeout=15) as client:
        resp = await client.get(login_url, headers={"User-Agent": UA}, follow_redirects=False)
        resp = await client.get(resp.headers["Location"], headers={"User-Agnet": UA}, follow_redirects=False)
        return resp.cookies


_instance: dict[str, Qzone] = {}


async def get_instance(uin: Union[str, int], expiration: int = 4 * 60 * 60) -> Qzone:
    uin = str(uin)
    instance = _instance.get(uin)

    if instance != None and time.time() - instance._updated < expiration:
        return instance

    times = 0
    while times <= 5:
        try:
            clientkey = await _get_clientkey(uin=uin)
            cookies = await _get_cookies(uin=uin, clientkey=clientkey)
            break
        except:
            await asyncio.sleep(3)
            times += 1
            continue

    _instance[uin] = Qzone(uin=uin, cookies=cookies, updated=time.time())
    return _instance[uin]
