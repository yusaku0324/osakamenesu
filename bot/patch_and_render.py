"""
Figma patch and render script for automated banner generation
"""
import os
import requests
import datetime
import pathlib
import yaml
import logging
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FigmaClient:
    """Client for interacting with Figma API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": api_key,
            "Content-Type": "application/json"
        }
    
    def patch_variables(self, file_id: str, mode: str, values: Dict[str, Any]) -> None:
        """Update variables in a Figma file"""
        url = f"{self.base_url}/files/{file_id}/variables"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        variables = response.json()
        question_var_id = None
        
        for var_id, var_data in variables.get('meta', {}).get('variables', {}).items():
            if var_data.get('name') == 'question':
                question_var_id = var_id
                break
        
        if not question_var_id:
            raise ValueError("Variable 'question' not found in Figma file")
        
        update_url = f"{self.base_url}/files/{file_id}/variables"
        payload = {
            "variableUpdates": {
                question_var_id: {
                    "valuesByMode": {
                        mode: values['question']
                    }
                }
            }
        }
        
        response = requests.post(update_url, headers=self.headers, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully updated variable 'question' to: {values['question']}")
    
    def render_png(self, file_id: str, node_id: str, scale: float = 1.0) -> str:
        """Render a node as PNG and return the URL"""
        url = f"{self.base_url}/images/{file_id}"
        params = {
            "ids": node_id,
            "scale": scale,
            "format": "png"
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        images = response.json().get('images', {})
        if node_id not in images:
            raise ValueError(f"Node {node_id} not found in response")
        
        image_url = images[node_id]
        logger.info(f"Successfully rendered PNG for node {node_id}")
        return image_url


def patch(question: str) -> None:
    """Update the question variable in Figma"""
    fg = FigmaClient(os.environ["FIGMA_API_KEY"])
    fg.patch_variables(
        file_id=os.environ["FIGMA_FILE_ID"],
        mode="Production/bannerVars",
        values={"question": question}
    )


def render() -> str:
    """Render the current state as PNG and return URL"""
    fg = FigmaClient(os.environ["FIGMA_API_KEY"])
    return fg.render_png(
        file_id=os.environ["FIGMA_FILE_ID"],
        node_id=os.environ["FIGMA_NODE_ID"],
        scale=1
    )


def main():
    """Main function to process queue files"""
    today = datetime.date.today().isoformat()
    qfile = f"queue/queue_{today}.yaml"
    
    if not os.path.exists(qfile):
        logger.warning(f"Queue file not found: {qfile}")
        return
    
    with open(qfile, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data:
        logger.warning(f"Queue file is empty: {qfile}")
        return
    
    for item in data:
        if 'text' not in item:
            logger.warning(f"Item missing 'text' field: {item}")
            continue
        
        try:
            patch(item["text"])
            item["png_url"] = render()
            logger.info(f"Processed item: {item['text'][:50]}...")
        except Exception as e:
            logger.error(f"Error processing item: {e}")
            continue
    
    with open(qfile, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
    
    logger.info(f"Successfully updated queue file: {qfile}")


if __name__ == "__main__":
    main()
