import redis
import json
from dotenv import dotenv_values

config = dotenv_values(".env")

class Cache:
    def __init__(
        self,
        host: str,
        port: str,
        password: str,
        ssl: bool,
        size: int,
    ):
        self.cache = redis.Redis(
            host = host,
            port = port,
            password = password,
            ssl = ssl
        )
        self.size = size
        self.keys = [
            'least_recent',
            'most_recent'
        ]
    
    def encode(self, value: dict) -> str:
        return str(value)

    def decode(self, value: str) -> dict:
        return json.loads(
            value.decode("utf-8").replace("'", '"')
        )
    
    def get(self, key: str) -> dict | None:
        value = self.cache.get(key)

        if value == None:
            return None
        
        return self.decode(value)
    
    def set(self, key: str, value: dict):
        self.cache.set(key, self.encode(value))
        
    def erase(self, key: str):
        self.cache.delete(key)

    def get_node(self, key: str) -> dict | None:
        if key in self.keys:
            return None
        
        node = self.get(key)
        
        if node == None:
            return node
        
        required_node = self.get(key)
        
        if required_node == None:
            return None
        
        # least_recent = self.get('least_recent')

        # if key == least_recent['key']:
        #     self.set('least_recent', {
        #         'key': required_node['next']
        #     })
        #     pass
            
        # else:
        #     previous = self.get(required_node['previous'])
        #     next = self.get(required_node['next'])
        
        return node['value']

    def set_node(self, key: str, node: dict):
        if key in self.keys:
            return
        
        most_recent = self.get('most_recent')

        if most_recent != None:
            most_recent_node = self.get(most_recent['key'])

            self.set(key, {
                'value': node,
                'next': '',
                'previous': most_recent['key'],
            })
            self.set(most_recent['key'], {
                'value': most_recent_node['value'],
                'next': key,
                'previous': most_recent_node['previous']
            })
        
        else:
            self.set(key, {
                'value': node,
                'next': '',
                'previous': '',
            })
            self.set('least_recent', {
                'key': key
            })
        
        self.set('most_recent', {
            'key': key
        })
    
cache = Cache(
  host = config['host'],
  port = config['port'],
  password = config['password'],
  ssl = True,
  size = 5,
)

cache.set_node('third', {'key': 'first name'})
cache.set_node('fourth', {'key': 'secon name'})

print(cache.get_node('first'))
print(cache.get_node('second'))