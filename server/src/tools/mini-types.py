def get_mime_type(file_path: str) -> str:
    extension = file_path.lower().split('.')[-1] if '.' in file_path else ''
    
    # Image types - only the formats we can display
    image_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    
    # Check if the file is an image
    if extension in image_types:
        return image_types[extension]
    
    # Default to text/plain for all other files
    return 'text/plain'

def is_image_file(mime_type: str) -> bool:
    return mime_type.startswith('image/')