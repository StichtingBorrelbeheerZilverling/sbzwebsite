import json
import base64
from urllib.parse import urlparse

import requests
from settings import DE_KLOK_EMAIL, DE_KLOK_PASSWORD


class DeKlok:
	LOGIN_FORM_URL = "https://www.deklokdranken.nl/connect/token"
	GRAPHQL_URL = "https://www.deklokdranken.nl/graphql"

	def __init__(self):
		self.session = requests.Session()
		self.session.headers.update({
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0',
			'Accept': '*/*',
			'Accept-Language': 'en-GB',
		})

		email = DE_KLOK_EMAIL
		password = DE_KLOK_PASSWORD

		login_payload = {
			'grant_type': 'password',
			'scope': 'offline_access',
			'storeId': 'dkd',
			'username': email,
			'password': password,
		}

		response = self.session.post(
			self.LOGIN_FORM_URL,
			data=login_payload, 
			headers={'Authorization': 'Bearer null'}
		)

		response.raise_for_status()
		login_data = response.json()
		self.access_token = login_data.get('access_token')
		self.refresh_token = login_data.get('refresh_token')
		self.user_id = self._extract_user_id_from_token(self.access_token)
		
		self.session.headers.update({
			'authorization': f'Bearer {self.access_token}',
			'content-type': 'application/json',
			'apollographql-client-name': 'x-api-graphql-client',
			'x-graphql-operation-type': 'query',
		})

	def _extract_user_id_from_token(self, token):
		# Extract userId from Access token

		try:
			parts = token.split('.')
			if len(parts) != 3:
				return None
			
			payload = parts[1]
			padding = 4 - len(payload) % 4
			if padding != 4:
				payload += '=' * padding
			
			decoded = base64.urlsafe_b64decode(payload)
			token_data = json.loads(decoded)
			return token_data.get('sub')
		except Exception:
			return None

	def _get_product_id_from_permalink(self, permalink):
		# Get product ID using GetSlugInfo GraphQL query

		query = """
		query GetSlugInfo($permalink: String, $storeId: String, $userId: String, $cultureName: String) {
		  slugInfo(
			permalink: $permalink
			storeId: $storeId
			userId: $userId
			cultureName: $cultureName
		  ) {
			entityInfo {
			  objectId
			}
			redirectUrl
		  }
		}
		"""
		
		graphql_payload = {
			'operationName': 'GetSlugInfo',
			'variables': {
				'storeId': 'dkd',
				'userId': self.user_id,
				'cultureName': 'nl-NL',
				'permalink': permalink,
			},
			'query': query,
		}
		
		response = self.session.post(
			self.GRAPHQL_URL,
			json=graphql_payload,
		)
		response.raise_for_status()
		
		data = response.json()

		if 'data' in data and data['data']['slugInfo']['entityInfo']:
			return data['data']['slugInfo']['entityInfo']['objectId']
		
		else:
			# Product_id may be in the permalink itself for some products
			product_id = permalink.split('/')[-1]
			if product_id:
				return product_id
			

		raise ValueError(f"Could not get product ID for permalink: {permalink}")


	def get_product_by_url(self, product_url):
		# Fetch product data from GraphQL by product URL

		permalink = urlparse(product_url).path.strip('/')

		try:
			product_id = self._get_product_id_from_permalink(permalink)

		except ValueError:
			raise ValueError(f"Could not get product from URL: {product_url}")
		
		query = """
		query GetProduct($storeId: String!, $currencyCode: String!, $cultureName: String, $id: String!, $previousOutline: String) {
		  product(
			storeId: $storeId
			id: $id
			currencyCode: $currencyCode
			cultureName: $cultureName
			previousOutline: $previousOutline
		  ) {
			name
			id
			code
			price {
			  actual {
				amount
			  }
			}
		  }
		}
		"""
		
		graphql_payload = {
			'operationName': 'GetProduct',
			'variables': {
				'storeId': 'dkd',
				'cultureName': 'nl-NL',
				'currencyCode': 'EUR',
				'id': product_id,
				'previousOutline': None,
			},
			'query': query,
		}
		
		response = self.session.post(
			self.GRAPHQL_URL,
			json=graphql_payload,
		)
		response.raise_for_status()

		data = response.json()

		if 'data' in data and 'product' in data['data'] and data['data']['product']:
			return data['data']['product']
		
		raise ValueError(f"Could not get product from URL: {product_url}")

	def get_product_prices(self, ids):
		# Fetch prices for multiple products by IDs

		query = """
		query GetProductsByIds($storeId: String!, $currencyCode: String!, $cultureName: String, $productIds: [String!]!, $first: Int) {
		  products(
			storeId: $storeId
			productIds: $productIds
			currencyCode: $currencyCode
			cultureName: $cultureName
			first: $first
		  ) {
			edges {
			  node {
				name
				id
				code
				price {
				  actual {
					amount
				  }
				}
			  }
			}
		  }
		}
		"""
		
		graphql_payload = {
			'operationName': 'GetProductsByIds',
			'variables': {
				'storeId': 'dkd',
				'cultureName': 'nl-NL',
				'currencyCode': 'EUR',
				'productIds': ids,
				'first': len(ids),
			},
			'query': query,
		}
		
		response = self.session.post(
			self.GRAPHQL_URL,
			json=graphql_payload,
		)

		response.raise_for_status()
		
		data = response.json()
		if 'data' in data and data['data'].get('products'):
			edges = data['data']['products'].get('edges', [])
			return [edge['node'] for edge in edges]
		
		raise ValueError(f"Could not get product prices for ID: {ids}")
