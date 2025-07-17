#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Manager
JSON 기반 설정 파일을 관리하는 모듈
"""

import json
import os
import logging
from typing import Dict, Any, Optional

class ConfigManager:
    """JSON 기반 설정 파일을 관리하는 클래스"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        ConfigManager 초기화
        
        Args:
            config_file: 설정 파일 경로
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._setup_defaults()
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일을 로드합니다."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logging.info(f"설정 파일 '{self.config_file}'을(를) 성공적으로 로드했습니다.")
                return config
            else:
                logging.warning(f"설정 파일 '{self.config_file}'이(가) 존재하지 않습니다. 기본 설정을 사용합니다.")
                return {}
        except Exception as e:
            logging.error(f"설정 파일 로드 중 오류 발생: {e}")
            return {}
    
    def _setup_defaults(self):
        """기본 설정값을 설정합니다."""
        defaults = {
            "mongodb": {
                "host": "localhost",
                "port": 27018,
                "database": "file_tagger",
                "collection": "tags"
            },
            "application": {
                "default_workspace_path": "",
                "custom_tags_file": "custom_tags.json"
            },
            "ui": {
                "theme": "default",
                "language": "ko"
            }
        }
        
        # 기본값으로 누락된 설정을 채웁니다
        for section, values in defaults.items():
            if section not in self.config:
                self.config[section] = values
            else:
                for key, value in values.items():
                    if key not in self.config[section]:
                        self.config[section][key] = value
        
        # MongoDB URI 생성
        if "mongodb" in self.config:
            host = self.config["mongodb"].get("host", "localhost")
            port = self.config["mongodb"].get("port", 27018)
            self.config["mongodb"]["uri"] = f"mongodb://{host}:{port}/"
        
        # 기본 작업 디렉토리 설정
        if not self.config["application"]["default_workspace_path"]:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # core 디렉토리에서 상위로 이동
            project_dir = os.path.dirname(os.path.dirname(current_dir))
            workspace_path = os.path.join(project_dir, "workspace")
            self.config["application"]["default_workspace_path"] = workspace_path
    
    def save_config(self) -> bool:
        """설정을 파일에 저장합니다."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logging.info(f"설정이 '{self.config_file}'에 저장되었습니다.")
            return True
        except Exception as e:
            logging.error(f"설정 저장 중 오류 발생: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """설정값을 가져옵니다."""
        try:
            return self.config[section][key]
        except KeyError:
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """설정값을 설정합니다."""
        try:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value
            return True
        except Exception as e:
            logging.error(f"설정값 설정 중 오류 발생: {e}")
            return False
    
    def get_mongodb_uri(self) -> str:
        """MongoDB URI를 가져옵니다."""
        return self.get("mongodb", "uri", "mongodb://localhost:27018/")
    
    def get_workspace_path(self) -> str:
        """작업 디렉토리 경로를 가져옵니다."""
        path = self.get("application", "default_workspace_path", "")
        if not path:
            # 기본값으로 현재 디렉토리의 workspace 사용
            current_dir = os.getcwd()
            path = os.path.join(current_dir, "workspace")
        
        # 디렉토리가 없으면 생성
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                logging.info(f"작업 디렉토리를 생성했습니다: {path}")
            except Exception as e:
                logging.error(f"작업 디렉토리 생성 실패: {e}")
                path = current_dir  # 실패시 현재 디렉토리 사용
        
        return path
    
    def set_workspace_path(self, path: str) -> bool:
        """작업 디렉토리 경로를 설정합니다."""
        return self.set("application", "default_workspace_path", path)
    
    def get_custom_tags_file(self) -> str:
        """커스텀 태그 파일 경로를 가져옵니다."""
        return self.get("application", "custom_tags_file", "custom_tags.json")

# 전역 ConfigManager 인스턴스
config_manager = ConfigManager()

# 기존 config.py와의 호환성을 위한 별칭
MONGO_HOST = config_manager.get("mongodb", "host", "localhost")
MONGO_PORT = config_manager.get("mongodb", "port", 27018)
MONGO_DB_NAME = config_manager.get("mongodb", "database", "file_tagger")
MONGO_COLLECTION_NAME = config_manager.get("mongodb", "collection", "tags")
MONGO_URI = config_manager.get_mongodb_uri()
DEFAULT_WORKSPACE_PATH = config_manager.get_workspace_path()
CUSTOM_TAGS_FILE = config_manager.get_custom_tags_file() 