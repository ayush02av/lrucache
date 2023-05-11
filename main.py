import redis
import json
from dotenv import dotenv_values
from datetime import datetime

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

        if self.size <= 1:
            raise Exception("Cache size should be greater than 1")
        
        self.keys = [
            'least_recent',
            'most_recent'
        ]

        self.cache.flushall(True)
    
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
        
        value = self.decode(value)
        value['created'] = datetime.fromtimestamp(value['created'])

        return value
    
    def set(self, key: str, value: dict, update_created: bool = True):
        # if update_created:
        value['created'] = datetime.today().timestamp()
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
        
        least_recent = self.get('least_recent')

        if key == least_recent['key']:
            self.set('least_recent', {
                'key': required_node['next']
            })

            next = self.get(required_node['next'])
            if next:
                self.set(required_node['next'], {
                    'value': next['value'],
                    'next': next['next'],
                    'previous': ''
                }, False)
            
        else:
            previous = self.get(required_node['previous'])
            if previous:
                self.set(required_node['previous'], {
                    'value': previous['value'],
                    'next': required_node['next'],
                    'previous': previous['previous']
                }, False)
            
            next = self.get(required_node['next'])
            if next:
                self.set(required_node['next'], {
                    'value': next['value'],
                    'next': next['next'],
                    'previous': required_node['previous']
                }, False)
            
        most_recent = self.get('most_recent')
        self.set('most_recent', {
            'key': key
        })
        self.set(key, {
            'value': required_node['value'],
            'next': '',
            'previous': most_recent['key']
        })

        most_recent_node = self.get(most_recent['key'])
        self.set(most_recent['key'], {
            'value': most_recent_node['value'],
            'next': key,
            'previous': most_recent_node['previous']
        })
            
        return node['value']

    def set_node(self, key: str, node: dict):
        if key in self.keys:
            return
        
        dbsize = self.cache.dbsize() - 2
        
        print(dbsize)
        
        if dbsize == self.size:
            print('cache size')
            
            least_recent = self.get('least_recent')
            least_recent_node = self.get(least_recent['key'])

            next_least_recent_node = self.get(least_recent_node['next']) if least_recent_node else None
            
            if next_least_recent_node:
                self.set('least_recent', {
                    'key': least_recent_node['next']
                })

                self.set(least_recent_node['next'], {
                    'value': next_least_recent_node['value'],
                    'next': next_least_recent_node['next'],
                    'previous': '',
                }, False)

            self.erase(least_recent['key'])
        
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
  size = 2,
)

cache.set_node('first', {'key': 'first name'})
cache.set_node('second', {'key': 'second name'})
cache.set_node('third', {'key': 'third name'})
cache.set_node('fourth', {'key': 'fourth name'})

cache.get_node('second')
cache.get_node('third')