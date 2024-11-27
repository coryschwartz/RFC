#!/usr/bin/env bash

# https://www.rfc-editor.org/retrieve/rsync/


rsync -avz --delete rsync.rfc-editor.org::everything-ftp ./mirror
