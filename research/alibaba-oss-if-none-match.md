# Alibaba OSS `If-None-Match: *` evidence

Date: 2026-08-20

## Conclusion

The strongest supportable conclusion is:

- Alibaba OSS documents `x-oss-forbid-overwrite` as the PutObject mechanism for preventing overwrite.
- The official PutObject request-header documentation does not list `If-None-Match` as a PutObject conditional-write header.
- Alibaba's official Java SDK exposes `If-None-Match` for GET/HEAD and copy-source conditions, but not as a PutObject request option.
- The PR's real Alibaba OSS test records `supportsCreateExclusive() == false`, matching the observed incompatibility with Trino's `createExclusive`, which sends `If-None-Match: *`.

This is enough to explain that OSS does not provide the S3 conditional-write primitive required by Trino's `createExclusive` path. A direct signed request/response capture against a real OSS bucket is still the best evidence for the narrower claim that OSS ignores or rejects this exact header.

## Primary sources

1. Alibaba Cloud OSS PutObject documentation:
   https://www.alibabacloud.com/help/en/oss/developer-reference/putobject

   Relevant statements in the request-header and error tables:

   - `x-oss-forbid-overwrite` “specifies whether to overwrite an object that has the same name during a PutObject operation.”
   - If `x-oss-forbid-overwrite` is `true`, an existing object with the same name cannot be overwritten.
   - If bucket versioning is enabled or suspended, OSS ignores this header and existing objects can be overwritten.
   - `FileAlreadyExists` (409) is documented for an existing object when `x-oss-forbid-overwrite=true`.

   The PutObject header table does not document `If-None-Match`.

2. Alibaba OSS official Java SDK header definitions:
   https://github.com/aliyun/aliyun-oss-java-sdk/blob/master/src/main/java/com/aliyun/oss/internal/OSSHeaders.java#L37-L52

   The SDK defines `If-None-Match` for GET and HEAD, and `x-oss-copy-source-if-none-match` for copy operations. It does not define an `If-None-Match` PutObject condition.

3. Alibaba OSS official Java SDK PutObject request model:
   https://github.com/aliyun/aliyun-oss-java-sdk/blob/master/src/main/java/com/aliyun/oss/model/PutObjectRequest.java#L25-L115

   `PutObjectRequest` has no `If-None-Match` or conditional-create field. This is corroborating SDK evidence, not by itself proof that an arbitrary raw HTTP header is rejected.

4. Trino's implementation at the PR head:
   https://github.com/trinodb/trino/blob/e33be4ee9787a7dd5880fd7a9d33d64cb9cf0186/lib/trino-filesystem-s3/src/main/java/io/trino/filesystem/s3/S3OutputStream.java#L385-L433

   Trino's exclusive path sets `builder.ifNoneMatch("*")` and maps HTTP 412 to an existing-file failure.

5. PR real-backend test:
   https://github.com/trinodb/trino/blob/e33be4ee9787a7dd5880fd7a9d33d64cb9cf0186/lib/trino-filesystem-s3/src/test/java/io/trino/filesystem/s3/TestOSSFileSystemAliyunOss.java#L104-L113

   The Alibaba OSS test explicitly declares `supportsCreateExclusive()` as `false`. The PR discussion records the reason as a real OSS incompatibility with `If-None-Match: *`, and the implementation excludes `createExclusive` for OSS.

## Recommended wording for the PR discussion

> Alibaba OSS does not expose S3's `If-None-Match: *` conditional PutObject behavior required by Trino's `createExclusive` implementation. OSS documents `x-oss-forbid-overwrite` as its PutObject overwrite-prevention mechanism instead, and its official SDK models `If-None-Match` for GET/HEAD and copy-source conditions, not PutObject. We also verified the limitation against a real OSS backend; therefore OSS cannot claim support for `createExclusive` or the Delta Lake conditional-write paths that depend on it. Note that `x-oss-forbid-overwrite` is not a reliable equivalent for all buckets because OSS documents that it is ignored when versioning is enabled or suspended.
