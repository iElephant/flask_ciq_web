import json
import redis


class CiqRedis:

    def __init__(self, m_host="127.0.0.1", m_port="6379"):
        self.r_conn = redis.StrictRedis(host=m_host, charset="utf-8", port=m_port, db=0, decode_responses=True)

    def write_data(self, m_dict, m_key="ciq"):
        json_data = json.dumps(m_dict)
        self.r_conn.set(m_key, json_data)

    def get_data(self, m_key="ciq"):
        r_dict = dict()
        r_dict = json.loads(self.r_conn.get(m_key))
        return r_dict

    def get_all(self):
        r_list = list()
        r_list = self.r_conn.keys()
        return r_list
    
    def get_set(self, m_key="ciq"):
        r_set = self.r_conn.smembers(m_key)
        return r_set

    def set_set(self, m_value="", m_key="ciq"):
        self.r_conn.sadd(m_key, m_value)

    def is_member_set(self, m_value="",m_key="ciq"):
        r_member = self.r_conn.sismember(m_key,m_value)
        return r_member

    def get_hash(self, m_key="ciq"):
        r_hash=self.r_conn.hgetall(m_key)
        return r_hash

    def set_hash(self, m_name="", m_value="",m_key="ciq"):
        self.r_conn.hset(m_key, m_name, m_value)

    def set_m_hash(self, m_mapping, m_key="ciq"):
        self.r_conn.hmset(m_key,m_mapping)
        
