import unittest
import json
import boto3
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to the path so we can import the app module
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import the functions from app.py
from app import generate_sql_with_bedrock, generate_nlp_response

class TestModelSelection(unittest.TestCase):
    
    @patch('boto3.client')
    def test_generate_sql_with_different_models(self, mock_boto3_client):
        # Mock the boto3 client and its invoke_model method
        mock_bedrock_runtime = MagicMock()
        mock_boto3_client.return_value = mock_bedrock_runtime
        
        # Mock response for Claude model
        claude_response = {
            'body': MagicMock(),
        }
        claude_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'SELECT * FROM Students'}]
        })
        
        # Mock response for Llama model
        llama_response = {
            'body': MagicMock(),
        }
        llama_response['body'].read.return_value = json.dumps({
            'generation': 'SELECT * FROM Students'
        })
        
        # Mock response for Titan model
        titan_response = {
            'body': MagicMock(),
        }
        titan_response['body'].read.return_value = json.dumps({
            'results': [{'outputText': 'SELECT * FROM Students'}]
        })
        
        # Test data
        prompt = "Show me all students"
        table_structures = {"tables": [{"name": "Students", "columns": [{"name": "id", "type": "INTEGER"}]}]}
        
        # Test with Claude model
        mock_bedrock_runtime.invoke_model.return_value = claude_response
        result_claude = generate_sql_with_bedrock(prompt, table_structures, "anthropic.claude-3-5-sonnet-20240620-v1:0")
        self.assertEqual(result_claude, "SELECT * FROM Students")
        
        # Verify Claude model was called with correct parameters
        claude_call = mock_bedrock_runtime.invoke_model.call_args_list[0][1]
        self.assertEqual(claude_call['modelId'], "anthropic.claude-3-5-sonnet-20240620-v1:0")
        self.assertIn("anthropic_version", json.loads(claude_call['body']))
        
        # Test with Llama model
        mock_bedrock_runtime.invoke_model.return_value = llama_response
        result_llama = generate_sql_with_bedrock(prompt, table_structures, "meta.llama2-13b-chat-v1")
        self.assertEqual(result_llama, "SELECT * FROM Students")
        
        # Verify Llama model was called with correct parameters
        llama_call = mock_bedrock_runtime.invoke_model.call_args_list[1][1]
        self.assertEqual(llama_call['modelId'], "meta.llama2-13b-chat-v1")
        self.assertIn("prompt", json.loads(llama_call['body']))
        
        # Test with Titan model
        mock_bedrock_runtime.invoke_model.return_value = titan_response
        result_titan = generate_sql_with_bedrock(prompt, table_structures, "amazon.titan-text-express-v1")
        self.assertEqual(result_titan, "SELECT * FROM Students")
        
        # Verify Titan model was called with correct parameters
        titan_call = mock_bedrock_runtime.invoke_model.call_args_list[2][1]
        self.assertEqual(titan_call['modelId'], "amazon.titan-text-express-v1")
        self.assertIn("inputText", json.loads(titan_call['body']))
    
    @patch('boto3.client')
    def test_generate_nlp_response_with_different_models(self, mock_boto3_client):
        # Mock the boto3 client and its invoke_model method
        mock_bedrock_runtime = MagicMock()
        mock_boto3_client.return_value = mock_bedrock_runtime
        
        # Mock response for Claude model
        claude_response = {
            'body': MagicMock(),
        }
        claude_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'There are 10 students in the database.'}]
        })
        
        # Mock response for Llama model
        llama_response = {
            'body': MagicMock(),
        }
        llama_response['body'].read.return_value = json.dumps({
            'generation': 'There are 10 students in the database.'
        })
        
        # Mock response for Titan model
        titan_response = {
            'body': MagicMock(),
        }
        titan_response['body'].read.return_value = json.dumps({
            'results': [{'outputText': 'There are 10 students in the database.'}]
        })
        
        # Test data
        prompt = "How many students are there?"
        sql_query = "SELECT COUNT(*) FROM Students"
        formatted_results = {'headers': ['count'], 'data': [{'count': '10'}]}
        
        # Test with Claude model
        mock_bedrock_runtime.invoke_model.return_value = claude_response
        result_claude = generate_nlp_response(prompt, formatted_results, sql_query, "anthropic.claude-3-5-sonnet-20240620-v1:0")
        self.assertEqual(result_claude['nlp_response'], "There are 10 students in the database.")
        
        # Test with Llama model
        mock_bedrock_runtime.invoke_model.return_value = llama_response
        result_llama = generate_nlp_response(prompt, formatted_results, sql_query, "meta.llama2-13b-chat-v1")
        self.assertEqual(result_llama['nlp_response'], "There are 10 students in the database.")
        
        # Test with Titan model
        mock_bedrock_runtime.invoke_model.return_value = titan_response
        result_titan = generate_nlp_response(prompt, formatted_results, sql_query, "amazon.titan-text-express-v1")
        self.assertEqual(result_titan['nlp_response'], "There are 10 students in the database.")

if __name__ == '__main__':
    unittest.main()