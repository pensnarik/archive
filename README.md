# General provisions

1. File is identified by its md5 hash. Thefore, there are [known examples](https://crypto.stackexchange.com/questions/1434/are-there-two-known-strings-which-have-the-same-md5-hash-value) of md5 hash collision. We have
to think to switch to `sha256`.
2. File might be included in another file (archive, encrypted tar, etc.)
3. There is a FUSE driver, written in Python that allows to navigate files by EXIF date or
EXIF Make/Model.
4. Files in archives are processed recursively. Currently supported archive formats are: gz, xz, zip and rar.
5. If file has multiple copies all original file names are stored in the database.

# Archiving process

The file archiving process comprises two phases. The first phase is md5 hash calculation and generation
JSON metadata with `preproc.py` tool. The second phase is to send this data to archive service using
HTTP REST API. You can put all in one by using unix pipes:

```bash
./preproc.py "$1" | curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ARCHIVE_SERVICE_TOKEN" "http://127.0.0.1:5000/api/add" -d @-
```

You can refer to `upload.sh` for an example.

# Environment variables

Variable | Description
-------- | -----------
ARCHIVE_SERVICE_URL | URL of REST API HTTP service
ARCHIVE_SERVICE_TOKEN | Access token to access REST API HTTP service
ARCHIVE_HOSTNAME | Prefix to all files that are stored on machine where the `./preproc` script is running

# REST API

Files should be added/updated/removed from archive via HTTP REST API.

## Adding new files

```
POST https://archive-service.parselab.ru/api/add
```

See `upload.sh` for an example. JSON data generated by `preproc.py` should be provided in HTTP request body. JSON
data example for this readme as the following:

```json
{
  "1d010435c7c92dbff73bc067a0c4cf01": {
    "filename": "README.md",
    "size": 1103,
    "ctime": 1561518708.027529,
    "mtime": 1561518708.027529,
    "filetype": "text"
  }
}
```

## Checking files

```
POST https://archive-service.parselab.ru/api/check/<hash>
```

Checks whether file with a given hash exists in the database.

# TODO

1. pcp hash calculation for animated GIFs. `convert` produces multiple images for animated GIFs,
how to calculate pcp hash for them?