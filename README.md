# Test repo for accessing AWS-S3 from G. Actions

## Problem

Back at argopy, on Github actions, when unit testing the new s3 store, we fall back on an anonymous requests with the following client:

```python
import boto3
from botocore import UNSIGNED
from botocore.client import Config

fs = boto3.client('s3', config=Config(signature_version=UNSIGNED))
```

but tests fails with the error:
```python
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the SelectObjectContent operation: Access Denied
```

I don't get why we can't run anonymously a `select_object_content` on the bucket

We can list the bucket:
```python
object_list = fs.list_objects_v2(Bucket='argo-gdac-sandbox', Prefix="pub/idx/argo_synthetic-profile_index.txt.gz")
object_list
```
returns:
```
{'ResponseMetadata': {'RequestId': 'PMVAY0JH3KRP8J3Y',
  'HostId': 'xqACBxsLPkqHm1VEPccv0zsceMm7s3cn5i5mey6Wd0yIHdTED8UbGA+ZGe0pLxiPnJLWaT3goIo=',
  'HTTPStatusCode': 200,
  'HTTPHeaders': {'x-amz-id-2': 'xqACBxsLPkqHm1VEPccv0zsceMm7s3cn5i5mey6Wd0yIHdTED8UbGA+ZGe0pLxiPnJLWaT3goIo=',
   'x-amz-request-id': 'PMVAY0JH3KRP8J3Y',
   'date': 'Tue, 09 Jul 2024 20:20:54 GMT',
   'x-amz-bucket-region': 'eu-west-3',
   'content-type': 'application/xml',
   'transfer-encoding': 'chunked',
   'server': 'AmazonS3'},
  'RetryAttempts': 0},
 'IsTruncated': False,
 'Contents': [{'Key': 'pub/idx/argo_synthetic-profile_index.txt.gz',
   'LastModified': datetime.datetime(2024, 7, 9, 3, 0, 5, tzinfo=tzutc()),
   'ETag': '"cc0d89c9dbda566cb9a29085b55d3a5a"',
   'Size': 6232628,
   'StorageClass': 'STANDARD'}],
 'Name': 'argo-gdac-sandbox',
 'Prefix': 'pub/idx/argo_synthetic-profile_index.txt.gz',
 'MaxKeys': 1000,
 'EncodingType': 'url',
 'KeyCount': 1}
```

But we can't run a boto3 `select_object_content`:

```python
s3_object = fs.select_object_content(
                Bucket='argotests',
                Key='ar_index_global_prof.txt.gz',
                ExpressionType="SQL",
                Expression="SELECT COUNT(*) FROM s3object",
                InputSerialization={"CSV": {"FileHeaderInfo": "IGNORE",
                                            'Comments': '#',
                                            'QuoteEscapeCharacter': '"',
                                            'RecordDelimiter': '\n',
                                            'FieldDelimiter': ',',
                                            'QuoteCharacter': '"',
                                            'AllowQuotedRecordDelimiter': False
                                            },
                                    "CompressionType": 'GZIP'},
                OutputSerialization={"CSV": {}},
            )
```

through the error:
```python
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the SelectObjectContent operation: Access Denied
```

<details><summary>Full trace</summary>

```python
---------------------------------------------------------------------------
ClientError                               Traceback (most recent call last)
Cell In[5], line 1
----> 1 s3_object = fs.select_object_content(
      2                 Bucket='argotests',
      3                 Key='ar_index_global_prof.txt.gz',
      4                 ExpressionType="SQL",
      5                 Expression="SELECT COUNT(*) FROM s3object",
      6                 InputSerialization={"CSV": {"FileHeaderInfo": "IGNORE",
      7                                             'Comments': '#',
      8                                             'QuoteEscapeCharacter': '"',
      9                                             'RecordDelimiter': '\n',
     10                                             'FieldDelimiter': ',',
     11                                             'QuoteCharacter': '"',
     12                                             'AllowQuotedRecordDelimiter': False
     13                                             },
     14                                     "CompressionType": 'GZIP'},
     15                 OutputSerialization={"CSV": {}},
     16             )

File ~/miniconda3/envs/argopy-pull326/lib/python3.9/site-packages/botocore/client.py:535, in ClientCreator._create_api_method.<locals>._api_call(self, *args, **kwargs)
    531     raise TypeError(
    532         f"{py_operation_name}() only accepts keyword arguments."
    533     )
    534 # The "self" in this scope is referring to the BaseClient.
--> 535 return self._make_api_call(operation_name, kwargs)

File ~/miniconda3/envs/argopy-pull326/lib/python3.9/site-packages/botocore/client.py:980, in BaseClient._make_api_call(self, operation_name, api_params)
    978     error_code = parsed_response.get("Error", {}).get("Code")
    979     error_class = self.exceptions.from_code(error_code)
--> 980     raise error_class(parsed_response, operation_name)
    981 else:
    982     return parsed_response

ClientError: An error occurred (AccessDenied) when calling the SelectObjectContent operation: Access Denied
```
</details>

## Explanation

The bucket can be read anonymously, but it is the `SelectObjectContent` method that requires credentials !

https://docs.aws.amazon.com/sdkfornet/v3/apidocs/items/S3/MS3SelectObjectContentSelectObjectContentRequest.html

> Permissions
You must have the s3:GetObject permission for this operation. Amazon S3 Select does not support anonymous 
access. For more information about permissions, see [Specifying Permissions in a Policy](https://docs.aws.amazon.com/AmazonS3/latest/dev/using-with-s3-actions.html) in the Amazon S3 User Guide.

# Fix

We need to find a way to get some credentials from Github Actions.

There is some info here:
https://stackoverflow.com/questions/58643905/how-aws-credentials-works-at-github-actions

## Solution 1

Use secrets for both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.

This is not recommended though.

## Solution 2

Use the Action [configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials).

We need to *use GitHub's OIDC provider in conjunction with a configured AWS IAM Identity Provider endpoint*.

The GitHub's OIDC provider is a method to get short-lived credentials needed for Github Actions (JWT).

When using OIDC, you configure IAM to accept JWTs from GitHub's OIDC endpoint. This action will then create a JWT unique to the workflow run using the OIDC endpoint, and it will use the JWT to assume the specified role with short-term credentials

Configuring OpenID Connect in Amazon Web Services ([I followed this procedure](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)):

- [x] [Create the OIDC provider on AWS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html#manage-oidc-provider-console). [Check IAM identuty providers here](https://us-east-1.console.aws.amazon.com/iam/home#/identity_providers) 

- [x] Configure a role and trust policy ([this is for a third-party Id provider](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp.html)). [Check create role here](https://us-east-1.console.aws.amazon.com/iam/home#/roles/details/ci-tests-ga-argopy-01?section=permissions)