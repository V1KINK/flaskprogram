from qiniu import Auth, put_data

access_key = "gXzBF_MkWyY_Q3sgY9uKNautS8W0XIQauC_ebziQ"
secret_key = "q7UHxQ1fa9MncdK6sf2NM7IRlKjoj9T87ZKSeJMI"
bucket_name = "1"


def storage(data):
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
        print(ret, info)
    except Exception as e:
        raise e

    if info.status_code != 200:
        raise Exception("上传图片失败")

    return ret["key"]

if __name__ == '__main__':
    file = input("请输入文件路径")
    with open(file, "rb") as f:
        storage(f.read())
