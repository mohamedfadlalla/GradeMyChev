from pymongo import MongoClient
import certifi
import streamlit as st

class EvaluationCounter:
    def __init__(self, connection_string):
        """Initialize MongoDB connection"""
        self.connection_string = connection_string
        self.db = None
        self.error_message = None

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            client = MongoClient(
                self.connection_string,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000
            )
            client.admin.command('ping')
            self.db = client['evaluation_analytics']
            return True
        except Exception as e:
            self.error_message = str(e)
            return False

    def increment_and_get_count(self):
        """Increment evaluation counter and return new value"""
        try:
            counter_collection = self.db['evaluation_counter']
            result = counter_collection.update_one(
                {'counter_id': 'evaluation_counter'},
                {'$inc': {'count': 1}},
                upsert=True
            )
            counter_doc = counter_collection.find_one({'counter_id': 'evaluation_counter'})
            return counter_doc['count'] if counter_doc else 1
        except Exception as e:
            self.error_message = str(e)
            return None

    def get_total_evaluations(self):
        """Get total number of evaluations"""
        try:
            counter_collection = self.db['evaluation_counter']
            counter_doc = counter_collection.find_one({'counter_id': 'evaluation_counter'})
            return counter_doc['count'] if counter_doc else 0
        except Exception as e:
            self.error_message = str(e)
            return None

# Initialize counter (to be used in Streamlit)
@st.cache_resource
def init_counter():
    """Initialize evaluation counter (runs once)"""
    return EvaluationCounter(st.secrets["connection_string"])
