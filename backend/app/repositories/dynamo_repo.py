import os

import boto3
from typing import Dict, Any, List, Optional


class DynamoRepository:
    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        self.table_name = table_name
        # Respect AWS_ENDPOINT_URL for local DynamoDB (docker on port 8001)
        endpoint_url = os.environ.get("AWS_ENDPOINT_URL")
        kwargs: Dict[str, Any] = {"region_name": region_name}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.dynamodb = boto3.resource("dynamodb", **kwargs)
        self.table = self.dynamodb.Table(table_name)

    def put_item(self, item: Dict[str, Any]) -> None:
        """Puts an item into the DynamoDB table."""
        self.table.put_item(Item=item)

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Gets an item from the DynamoDB table by key."""
        response = self.table.get_item(Key=key)
        return response.get("Item")

    def query_index(
        self,
        index_name: str,
        key_condition_expression: Any,
        limit: int = 10,
        exclusive_start_key: Optional[Dict[str, Any]] = None,
        scan_index_forward: bool = True,
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Queries a DynamoDB index with pagination."""
        kwargs = {
            "IndexName": index_name,
            "KeyConditionExpression": key_condition_expression,
            "Limit": limit,
            "ScanIndexForward": scan_index_forward,
        }
        if exclusive_start_key:
            kwargs["ExclusiveStartKey"] = exclusive_start_key

        response = self.table.query(**kwargs)
        return response.get("Items", []), response.get("LastEvaluatedKey")

    def query(
        self,
        key_condition_expression: Any,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Queries the DynamoDB table or index."""
        kwargs = {
            "KeyConditionExpression": key_condition_expression,
        }
        if expression_attribute_values is not None:
            kwargs["ExpressionAttributeValues"] = expression_attribute_values
        if index_name:
            kwargs["IndexName"] = index_name

        response = self.table.query(**kwargs)
        return response.get("Items", []), response.get("LastEvaluatedKey")
