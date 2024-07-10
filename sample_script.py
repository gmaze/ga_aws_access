import boto3
from botocore import UNSIGNED
from botocore.client import Config

if __name__ == "__main__":

    # fs = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    fs = boto3.client('s3')

    # List the object:
    print("\n", "="*40, "\n")
    object_list = fs.list_objects_v2(Bucket='argo-gdac-sandbox', Prefix="pub/idx/argo_synthetic-profile_index.txt.gz")
    print(object_list)
    print("\n", "="*40, "\n")

    # Select data from the object:
    print("\n", "="*40, "\n")
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
    print("\n", "="*40, "\n")
