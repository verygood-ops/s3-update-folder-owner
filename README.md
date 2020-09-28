s3-update-folder-owner
======================

Recursively updates S3 folder owner, so that matches user running this script (usually also a bucket owner).

Install
--------

`git clone git@github.com:verygood-ops/s3-update-folder-owner.git`

`cd s3-update-folder-owner/ && python3 setup.py install`


Use
---

`s3-update-folder-owner.py <s3_bucket_name> <s3/folder/prefix> --num-workers=24`

`s3-update-folder-owner.py <s3_bucket_name> <s3/folder/prefix> --num-workers=24 --start-after logs/my-latest-cloudfront-log.gz`
