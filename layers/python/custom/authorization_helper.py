

def generate_deny_policy(principalId, resource, context = {}):
    return {
        "principalId": principalId,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": resource
                }
            ]
        },
        "context": context
    }


def generate_allow_policy(principal, resource, context = {}):
    return {
        "principalId": principal,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": "*"
                }
            ]
        },
        "context": context
    }