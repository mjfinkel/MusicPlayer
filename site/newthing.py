import os
import re

def main():
    original_title = 'iwuC7KAB3Ik'
    original_ext = "mp3"
    original_filename = os.path.join('site/resources/audio', f"{original_title}.{original_ext}")
    original_filename = f'site/resources/audio/{original_title}.{original_ext}'
    sanitized_title = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', 'Hey Jude (Live at Sullivan Stadium, Foxboro, MA 7/2/89)')
    print(sanitized_title)
    sanitized_filename = os.path.join('site/resources/audio', f"{sanitized_title}.{original_ext}")
    os.rename(original_filename, sanitized_filename)

if __name__ == "__main__":
    print(os.path.exists('site/resources/audio/iwuC7KAB3Ik.mp3'))
    main()