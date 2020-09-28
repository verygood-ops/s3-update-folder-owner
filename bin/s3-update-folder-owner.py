#!/usr/bin/env python3
"""
Update permissions for S3 objects in a folder,
so that user running this script (usually bucket owner)
becomes an owner of files in folder,
and achieves full control.

A use-case for this script
is establishing cross-account access to files delivered by AWS Cloudfront standard logging system.

As it stated in documentation, AWS Cloudfront logs are owned by awslogsdelivery account:

https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html#AccessLogsBucketAndFileOwnership

This makes impossible cross-account access to such Cloudfront logs with S3 bucket policy,
because such policy would apply only to the objects that the bucket owner creates.

https://docs.aws.amazon.com/AmazonS3/latest/user-guide/add-bucket-policy.html
"""
import argparse
import concurrent.futures
import logging
import threading

import boto3


arg_parser = argparse.ArgumentParser()
logger = logging.getLogger(__name__)
arg_parser.add_argument('bucket_name')
arg_parser.add_argument('prefix')
arg_parser.add_argument('--debug', action='store_true')
arg_parser.add_argument('--start-after', default='')
arg_parser.add_argument('--num-workers', default=16, type=int)
resources = {}


def main():
    args = arg_parser.parse_args()

    debug = args.debug
    if debug:
        boto3.set_stream_logger(level=logging.DEBUG)

    s3c = boto3.client('s3')
    s3_paginator = s3c.get_paginator('list_objects_v2')
    prefix = args.prefix

    def objects(delimiter='/', start_after=args.start_after):
        """Iterate over given bucket object,
        prefixed with a common (possibly empty) prefix..

        :yields: dict with S3 object key metadata
        """
        nonlocal prefix

        prefix = prefix[1:] if prefix.startswith(delimiter) else prefix
        start_after = (start_after or prefix) if prefix.endswith(delimiter) else start_after
        for page in s3_paginator.paginate(Bucket=args.bucket_name, Prefix=prefix, StartAfter=start_after):
            for content in page.get('Contents', ()):
                yield content

    def process(obj):
        """Process single bucket key.
        This function runs in a thread pool.

        :param obj: An S3 object dictionary containing key and metadata.
        """

        nonlocal s3c, args

        #
        # While low-level clients are thread-safe,
        # boto3 resources should be thread local.
        #
        ident = threading.get_ident()
        if ident in resources:
            s3 = resources[ident]
        else:
            s3 = boto3.resource('s3')
            resources[ident] = s3

        object_key = obj['Key']
        object_acl = s3.ObjectAcl(args.bucket_name, object_key)

        acl_response = object_acl.put(ACL='bucket-owner-full-control')

        if debug:
            logger.warning('Created ACL %s', object_acl)
            logger.warning('ACL response: %r', acl_response)

        copy_response = s3c.copy_object(
            Bucket=args.bucket_name,
            Key=object_key,
            MetadataDirective="REPLACE",
            CopySource='{}/{}'.format(args.bucket_name, object_key)
        )


        if debug:
            logger.warning('Copied object over itself %s', '{}/{}'.format(args.bucket_name, object_key))
            logger.warning('COPY response: %r', copy_response)

        logger.warning('Entitled bucket owner to have full control on object s3://%s/%s',
            args.bucket_name, object_key
        )


    with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        executor.map(process, objects())


if __name__ == '__main__':
    main()
