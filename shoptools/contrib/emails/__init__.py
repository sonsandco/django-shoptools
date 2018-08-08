
def send_email(*args, **kwargs):
    from .emails import send_email
    return send_email(*args, **kwargs)


def email_content(*args, **kwargs):
    from .emails import email_content
    return email_content(*args, **kwargs)
