# Qzone Next

封装了一些对QQ空间的操作

## 使用

需要在本机上登录QQ客户端. 推荐使用[NapCatQQ](https://github.com/NapNeko/NapCatQQ).

`async def get_instance(uin: Union[str, int], expiration: int = 4 * 60 * 60) -> Qzone:` 获取Qzone实例，默认Cookie有效期为4h

`async def upload_image(self, base64: bytes) -> QzoneImage` 上传照片

`async def publish(self, text: str, images: list[QzoneImage] = []) -> str` 发布动态，返回动态的tid

## TODO

* 上传视频
* 获取点赞列表，查看量
* 删除动态
* 获取访客列表