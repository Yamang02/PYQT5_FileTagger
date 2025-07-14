from dataclasses import dataclass
from typing import List
from PyQt5.QtCore import QObject, pyqtSignal
import time

@dataclass
class TagAddedEvent:
    file_path: str
    tag: str
    timestamp: float

@dataclass  
class TagRemovedEvent:
    file_path: str
    tag: str
    timestamp: float

class EventBus(QObject):
    # 타입 안전한 시그널 정의
    tag_added = pyqtSignal(TagAddedEvent)
    tag_removed = pyqtSignal(TagRemovedEvent)
    
    def publish_tag_added(self, file_path: str, tag: str):
        event = TagAddedEvent(file_path, tag, time.time())
        self.tag_added.emit(event)
    
    def subscribe_tag_added(self, callback):
        self.tag_added.connect(callback)

    def publish_tag_removed(self, file_path: str, tag: str):
        event = TagRemovedEvent(file_path, tag, time.time())
        self.tag_removed.emit(event)

    def subscribe_tag_removed(self, callback):
        self.tag_removed.connect(callback)
