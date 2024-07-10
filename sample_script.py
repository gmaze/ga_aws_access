import boto3
from botocore import UNSIGNED
from botocore.client import Config

if __name__ == "__main__":

    print("\n", "="*40, "Create boto3 client", "\n")
    # fs = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    fs = boto3.client('s3')
    access_key = fs._request_signer._credentials.get_frozen_credentials().access_key
    print("Found AWS Credentials for access_key='%s'" % access_key)

    # List the object:
    # Work with UNSIGNED client
    # Won't work if creds are not found
    print("\n", "="*40, "list_objects_v2", "\n")
    object_list = fs.list_objects_v2(Bucket='argo-gdac-sandbox', Prefix="pub/idx/argo_synthetic-profile_index.txt.gz")
    print(object_list)

    # Select data from the object:
    print("\n", "="*40, "select_object_content", "\n")
    s3_object = fs.select_object_content(
                    Bucket='argo-gdac-sandbox',
                    Key='pub/idx/argo_synthetic-profile_index.txt.gz',
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

    # Iterate over the filtered CSV data
    records = []
    for event in s3_object["Payload"]:
        if "Records" in event:
            records.append(event["Records"]["Payload"].decode("utf-8"))
        elif 'Stats' in event:
            stats = event['Stats']['Details']

    print(''.join(r for r in records))
