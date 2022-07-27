#######
# AWS #
#######

# Bucket name and location for AWS S3
BUCKET = "bookbot-speech"
REGION = "ap-southeast-1"

# Maximum URL timeout for AWS S3
SIGNED_URL_TIMEOUT = 3600

# Language codes accepted for AWS Transcribe
LANGUAGE_CODES = [
    "en-AB",
    "en-AU",
    "en-GB",
    "en-IE",
    "en-IN",
    "en-US",
    "en-WL",
    "en-ZA",
    "en-NZ",
    "id-ID",
]

# File extensions
EXTENSIONS = ["txt", "srt", "json", "aac", "wav", "m4a"]
