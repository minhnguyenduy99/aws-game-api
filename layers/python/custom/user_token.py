import datetime
import jwt

def generate_access_token(user_id: str, SECRET_KEY: str):
    if user_id is None:
        raise Exception("User cannot be None")

    payload = {
        "user_id": user_id,
        "iat": datetime.datetime.now(),
        "exp": datetime.datetime.now() + datetime.timedelta(hours=2)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256").decode("utf-8")

    return token

def generate_refresh_token(user_id: str, SECRET_KEY: str):
    if user_id is None:
        raise Exception("User cannot be None")
    payload = {
        "user_id": user_id,
        "iat": datetime.datetime.now(),
        "exp": datetime.datetime.now() + datetime.timedelta(days=5)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256").decode("utf-8")

    return token



def decode_user_token(token: str, SECRET_KEY: str):
    error = None
    payload = None
    try:
        payload = jwt.decode(token, SECRET_KEY)
    except jwt.ExpiredSignatureError:
        error = "The token has been expired"
    except jwt.InvalidTokenError:
        error = "Invalid token"
    except:
        error = "Token decoding error"
    finally:
        print(f"error: {error}")
        print(f"payload: {payload}")
        if error is None:
            return {
                "payload": payload,
                "error": None
            }
        return {
            "payload": None,
            "error": error
        }
        