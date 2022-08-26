# 重写JWT返回结果方法

def jwt_response_payload_handler(token,user=None,request=None):
    return {
        'token':token,
        'username':user.username,
        'id':user.id
    }