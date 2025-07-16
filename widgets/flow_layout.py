from PyQt5.QtWidgets import QLayout, QSizePolicy, QLayoutItem, QWidget, QWidgetItem
from PyQt5.QtCore import Qt, QSize, QPoint, QRect


class FlowLayout(QLayout):
    """
    위젯들을 수평으로 배치하다가 공간이 부족하면 자동으로 줄바꿈하는 레이아웃
    태그칩들의 자연스러운 배치를 위해 사용됩니다.
    """
    
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        
        self.setSpacing(spacing)
        self.item_list = []
    
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    
    def addItem(self, item):
        self.item_list.append(item)
    
    def addWidget(self, widget):
        """위젯을 레이아웃에 추가합니다."""
        if widget is not None:
            from PyQt5.QtWidgets import QWidgetItem
            item = QWidgetItem(widget)
            self.addItem(item)
            # 위젯 부모 설정
            widget.setParent(self.parentWidget())
    
    def count(self):
        return len(self.item_list)
    
    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        if not self.item_list:
            return QSize(0, 50)  # 기본 최소 크기
            
        # 최소 너비는 가장 큰 아이템의 너비
        min_width = 0
        for item in self.item_list:
            min_width = max(min_width, item.minimumSize().width())
        
        # 높이는 실제 레이아웃을 계산해서 구함
        min_height = self.heightForWidth(min_width)
        
        margins = self.contentsMargins()
        return QSize(min_width + margins.left() + margins.right(), 
                    min_height + margins.top() + margins.bottom())
    
    def _do_layout(self, rect, test_only):
        """레이아웃 계산 및 적용"""
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = max(self.spacing(), 4)  # 최소 4px 간격 보장
        
        for item in self.item_list:
            widget = item.widget()
            if widget is None:
                continue
                
            item_width = item.sizeHint().width()
            item_height = item.sizeHint().height()
            
            # 다음 아이템이 현재 줄에 들어갈 수 있는지 확인
            next_x = x + item_width
            if next_x > rect.right() and line_height > 0:
                # 새 줄로 이동
                x = rect.x()
                y = y + line_height + spacing
                next_x = x + item_width
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(x, y, item_width, item_height))
            
            x = next_x + spacing
            line_height = max(line_height, item_height)
        
        # 마지막 줄의 높이 포함
        total_height = y + line_height - rect.y() if line_height > 0 else 0
        return max(total_height, 50)  # 최소 높이 보장 