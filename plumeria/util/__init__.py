MIME_TYPES = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.txt': 'text/plain',
}


def to_mimetype(ext):
    if ext.lower() in MIME_TYPES:
        return MIME_TYPES[ext.lower()]
    else:
        return "application/octet-stream"
