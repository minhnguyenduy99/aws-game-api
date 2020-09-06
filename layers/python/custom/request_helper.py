import email
import base64

def parse_cookies(cookie_str: str) -> dict:
    if cookie_str is None:
        return None
    cookies_str = cookie_str.split(";")
    cookies = {}
    for cookie in cookies_str:
        cookie_parts = cookie.split("=")
        if len(cookie_parts) != 2:
            raise Exception("Cookie is invalid")
        cookies[cookie_parts[0]] = cookie_parts[1]

    return cookies


def parse_binary_multipart_to_form(request: dict) -> dict:
    """
    Parse binary body from `multipart/form-data` type to `dict`\n
    If the `Content-Type` is not `multipart/form-data` then return `None`\n
    Else the returned result is a `dict`. Each pair is a `dict` contains of 2 fields:\n
    `metadata`: a map of parameters from subpart of the body\n
    `value`: the value of subpart
    """

    request["headers"] = lowercase_headers(request["headers"])
    if request is None:
        raise Exception("The request param cannot be None")
    post_data = ("Content-Type: " + request["headers"]["content-type"] + "\n").encode() + base64.b64decode(request["body"])
    msg = email.message_from_bytes(post_data)
    if msg.is_multipart() is False:
        return None

    form = {}
    for part in msg.get_payload():
        key = part.get_param("name", header="Content-Disposition")
        tuple_params = part.get_params(header="Content-Disposition", unquote=True)
        map_params = {}
        for param in tuple_params:
            map_params[param[0]] = param[1]
        payload = part.get_payload()
        if "filename" in map_params:
            payload = part.get_payload(decode=True)
            form[key] = {
                "metadata": map_params,
                "value": {
                    "file_name": map_params["filename"],
                    "data": payload
                }
            }
        else:
            form[key] = {
                "metadata": map_params,
                "value": payload
            }
    return form


def validate_multipart_form_data(form: dict, validator: list = []) -> bool:
    if dict is None:
        raise Exception("Cannot validate form of NoneType")
    return all([key in form.keys() for key in validator])


def lowercase_headers(headers: dict) -> dict:
    lower_headers = {}
    for header in headers:
        lower = header.lower()
        lower_headers[lower] = headers[header]
    return lower_headers