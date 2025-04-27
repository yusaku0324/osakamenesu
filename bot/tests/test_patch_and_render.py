"""
Tests for patch_and_render.py
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import yaml
import tempfile
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import patch_and_render


class TestFigmaClient(unittest.TestCase):
    """Test FigmaClient class"""
    
    def setUp(self):
        self.api_key = "test_api_key"
        self.client = patch_and_render.FigmaClient(self.api_key)
    
    @patch('requests.get')
    @patch('requests.post')
    def test_patch_variables(self, mock_post, mock_get):
        """Test patching variables in Figma"""
        mock_get.return_value.json.return_value = {
            'meta': {
                'variables': {
                    'var_123': {'name': 'question'}
                }
            }
        }
        mock_get.return_value.raise_for_status = MagicMock()
        
        mock_post.return_value.raise_for_status = MagicMock()
        
        self.client.patch_variables(
            file_id="test_file",
            mode="Production/bannerVars",
            values={"question": "Test question?"}
        )
        
        mock_get.assert_called_once()
        mock_post.assert_called_once()
        
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertIn('variableUpdates', payload)
        self.assertIn('var_123', payload['variableUpdates'])
    
    @patch('requests.get')
    def test_render_png(self, mock_get):
        """Test rendering PNG from Figma"""
        mock_get.return_value.json.return_value = {
            'images': {
                'test_node': 'https://example.com/image.png'
            }
        }
        mock_get.return_value.raise_for_status = MagicMock()
        
        url = self.client.render_png(
            file_id="test_file",
            node_id="test_node",
            scale=1.0
        )
        
        self.assertEqual(url, 'https://example.com/image.png')
        mock_get.assert_called_once()


class TestPatchAndRender(unittest.TestCase):
    """Test main functions"""
    
    def setUp(self):
        os.environ['FIGMA_API_KEY'] = 'test_api_key'
        os.environ['FIGMA_FILE_ID'] = 'test_file_id'
        os.environ['FIGMA_NODE_ID'] = 'test_node_id'
    
    @patch('patch_and_render.FigmaClient')
    def test_patch(self, mock_client_class):
        """Test patch function"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        patch_and_render.patch("Test question?")
        
        mock_client.patch_variables.assert_called_once_with(
            file_id='test_file_id',
            mode='Production/bannerVars',
            values={'question': 'Test question?'}
        )
    
    @patch('patch_and_render.FigmaClient')
    def test_render(self, mock_client_class):
        """Test render function"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.render_png.return_value = 'https://example.com/image.png'
        
        url = patch_and_render.render()
        
        self.assertEqual(url, 'https://example.com/image.png')
        mock_client.render_png.assert_called_once_with(
            file_id='test_file_id',
            node_id='test_node_id',
            scale=1
        )
    
    @patch('patch_and_render.patch')
    @patch('patch_and_render.render')
    def test_main(self, mock_render, mock_patch):
        """Test main function"""
        today = date.today().isoformat()
        queue_data = [
            {'text': 'Question 1?'},
            {'text': 'Question 2?'}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_dir = os.path.join(tmpdir, 'queue')
            os.makedirs(queue_dir)
            queue_file = os.path.join(queue_dir, f'queue_{today}.yaml')
            
            with open(queue_file, 'w') as f:
                yaml.safe_dump(queue_data, f)
            
            mock_render.side_effect = [
                'https://example.com/image1.png',
                'https://example.com/image2.png'
            ]
            
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                patch_and_render.main()
            finally:
                os.chdir(original_cwd)
            
            with open(queue_file, 'r') as f:
                updated_data = yaml.safe_load(f)
            
            self.assertEqual(len(updated_data), 2)
            self.assertEqual(updated_data[0]['png_url'], 'https://example.com/image1.png')
            self.assertEqual(updated_data[1]['png_url'], 'https://example.com/image2.png')
            
            self.assertEqual(mock_patch.call_count, 2)
            self.assertEqual(mock_render.call_count, 2)


if __name__ == '__main__':
    unittest.main()
