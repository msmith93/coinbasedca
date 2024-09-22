import json
from coinbase.rest import RESTClient
import boto3
from botocore.exceptions import ClientError
from uuid import uuid4

BUY_PRODUCTS = [
    {
        "product_id": "BTC-USD",
        "dollar_amount_buy": "1",
    },
    {
        "product_id": "ETH-USD",
        "dollar_amount_buy": "1",
    },
    {
        "product_id": "DOGE-USD",
        "dollar_amount_buy": "1",
    },
]

def get_secret():

    secret_name = "coinbaseapikey"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e    

    secret = json.loads(get_secret_value_response["SecretString"])

    api_key = secret['COINBASE_API_KEY']
    api_secret = secret['COINBASE_API_SECRET']

    return api_key, api_secret


def lambda_handler(event, context):
    api_key, api_secret = get_secret()
    client = RESTClient(api_key=api_key, api_secret=api_secret)

    order_ids = []

    for product in BUY_PRODUCTS:
        order = client.market_order_buy(
            client_order_id=str(uuid4()),
            product_id=product.get("product_id"),
            quote_size=product.get("dollar_amount_buy")
        )
        print(order)
        if 'success_response' in order:
            order_id = order['success_response']['order_id']
            order_ids.append(order_id)
        elif 'error_response' in order:
            error_response = order['error_response']
            print(error_response)

    print(f"Orders executed: {order_ids}")

    for order_id in order_ids:
        fills = client.get_fills(order_id=order_id)

        print(f"Fills for order {order_id}:")
        print(json.dumps(fills, indent=2))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "order_ids": order_ids,
        }),
    }
